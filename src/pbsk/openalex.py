from __future__ import annotations
import json, os, time, math
from pathlib import Path
import requests
from .utils import ensure, stable_key, write_json, now_utc, backoff_sleep

class OpenAlexClient:
    def __init__(self, cfg, api_key=None, cache_dir='cache/openalex'):
        self.cfg=cfg
        self.api_key=api_key or os.getenv('OPENALEX_API_KEY')
        if not self.api_key:
            raise RuntimeError('OPENALEX_API_KEY is required for full OpenAlex analysis.')
        self.base=cfg['base_url'].rstrip('/')
        self.cache=ensure(cache_dir)
        self.manifests=ensure('cache/manifests')
        self.session=requests.Session()

    def _get(self, endpoint, params):
        safe={k:v for k,v in params.items() if k!='api_key'}
        last=None
        for attempt in range(int(self.cfg.get('max_retries',6))):
            try:
                r=self.session.get(f'{self.base}/{endpoint.lstrip("/")}', params=params, timeout=self.cfg.get('timeout_seconds',60))
                if r.status_code in {401,403}:
                    raise RuntimeError(f'OpenAlex authentication/authorization failed (HTTP {r.status_code}); check OPENALEX_API_KEY.')
                if r.status_code in {429,500,502,503,504}:
                    last=RuntimeError(f'OpenAlex transient HTTP {r.status_code}'); backoff_sleep(attempt); continue
                if r.status_code>=400:
                    raise RuntimeError(f'OpenAlex request failed (HTTP {r.status_code}) for parameters {safe}')
                return r
            except RuntimeError:
                raise
            except requests.RequestException as e:
                last=e
                if attempt+1>=int(self.cfg.get('max_retries',6)): break
                backoff_sleep(attempt)
        raise RuntimeError(f'OpenAlex request failed after retries for parameters {safe}: {type(last).__name__}')

    def rate_limit(self):
        return self._get('rate-limit', {'api_key':self.api_key}).json()

    def _paged_works(self, params, max_records, cache_query):
        key=stable_key(cache_query); cf=self.cache/f'works_{key}.json'
        if cf.exists(): return json.loads(cf.read_text(encoding='utf-8'))
        p=dict(params); p['api_key']=self.api_key; p['per_page']=min(100,int(self.cfg.get('per_page',100))); p['cursor']='*'
        results=[]; calls=0; total_count=None; cost=0.0
        while len(results)<int(max_records):
            r=self._get('works',p); calls+=1; data=r.json(); meta=data.get('meta',{})
            total_count=meta.get('count',total_count); cost += float(meta.get('cost_usd') or 0.0)
            batch=data.get('results',[]); results.extend(batch)
            nxt=meta.get('next_cursor')
            if not batch or not nxt: break
            p['cursor']=nxt; time.sleep(float(self.cfg.get('sleep_seconds',0.1)))
        # deterministic de-duplication
        seen=set(); out=[]
        for w in results:
            wid=w.get('id') or json.dumps(w,sort_keys=True)
            if wid in seen: continue
            seen.add(wid); out.append(w)
            if len(out)>=int(max_records): break
        cf.write_text(json.dumps(out),encoding='utf-8')
        write_json(self.manifests/f'openalex_{key}.json',{
            'provider':'OpenAlex','retrieved_utc':now_utc(),'query':cache_query,'returned_records':len(out),
            'estimated_total_count':total_count,'api_calls':calls,'reported_cost_usd':cost
        })
        return out

    def get_works(self, *, search=None, start_date, end_date, max_records, select=None, topic_id=None):
        select=select or self.cfg['select']
        filters=[f'from_publication_date:{start_date}',f'to_publication_date:{end_date}']
        if topic_id: filters.append(f'topics.id:{str(topic_id).split("/")[-1]}')
        query={'search':search or '', 'topic_id':topic_id or '', 'start_date':start_date,'end_date':end_date,'max_records':int(max_records),'select':select}
        params={'filter':','.join(filters),'select':select}
        if search: params['search']=search
        return self._paged_works(params,max_records,query)

    def get_works_balanced(self, *, search=None, topic_id=None, start_year, end_year, max_records, per_year_cap, select=None):
        """Deterministic random sampling across the complete date window.

        v3 truncated the first N API results. v4 instead requests reproducible random samples
        (OpenAlex ``sample`` + ``seed``) in chunks of at most 100 and de-duplicates them.
        This removes fixed-rank truncation while keeping API cost bounded. ``per_year_cap`` is
        retained in the public signature for backward compatibility but no longer truncates years.
        """
        select=select or self.cfg['select']; filters=[f'from_publication_date:{int(start_year)}-01-01',f'to_publication_date:{int(end_year)}-12-31']
        if topic_id:filters.append(f'topics.id:{str(topic_id).split("/")[-1]}')
        base={'filter':','.join(filters),'select':select,'per_page':100}
        if search:base['search']=search
        query={'random_sample':True,'search':search or '', 'topic_id':topic_id or '', 'start_year':int(start_year),'end_year':int(end_year),'max_records':int(max_records),'select':select}
        key=stable_key(query); cf=self.cache/f'sample_{key}.json'
        if cf.exists():return json.loads(cf.read_text(encoding='utf-8'))
        target=int(max_records); out=[]; seen=set(); calls=0; cost=0.0
        seed0=int(stable_key(query)[:8],16) % 2000000000
        # Multiple deterministic 100-work samples are used because per_page is capped at 100.
        attempts=max(1,math.ceil(target/100)+3)
        for j in range(attempts):
            need=min(100,target-len(out))
            if need<=0:break
            params={**base,'api_key':self.api_key,'sample':need,'seed':seed0+j}
            data=self._get('works',params).json(); calls+=1; cost+=float((data.get('meta') or {}).get('cost_usd') or 0.0)
            batch=data.get('results',[]) or []
            for w in batch:
                wid=w.get('id')
                if wid and wid not in seen:
                    seen.add(wid); out.append(w)
                    if len(out)>=target:break
            if not batch:break
        cf.write_text(json.dumps(out),encoding='utf-8')
        write_json(self.manifests/f'openalex_sample_{key}.json',{'provider':'OpenAlex','retrieved_utc':now_utc(),'query':query,'returned_records':len(out),'api_calls':calls,'reported_cost_usd':cost,'sampling':'deterministic_random'})
        return out

    def sample_topics(self, n=600, minimum_works=1000):
        query={'sample_topics':int(n),'minimum_works':int(minimum_works)}; key=stable_key(query); cf=self.cache/f'topics_{key}.json'
        if cf.exists():return json.loads(cf.read_text(encoding='utf-8'))
        target=min(int(n),10000); rows=[]; seen=set(); seed0=int(stable_key(query)[:8],16)%2000000000
        attempts=max(1,math.ceil(target/100)+5)
        for j in range(attempts):
            need=min(100,target-len(rows))
            if need<=0:break
            params={'api_key':self.api_key,'sample':need,'seed':seed0+j,'per_page':100,'filter':f'works_count:>{int(minimum_works)}',
                    'select':'id,display_name,description,keywords,domain,field,subfield,works_count,cited_by_count'}
            data=self._get('topics',params).json()
            for t in (data.get('results',[]) or []):
                tid=t.get('id')
                if tid and tid not in seen:
                    seen.add(tid); rows.append(t)
                    if len(rows)>=target:break
        cf.write_text(json.dumps(rows),encoding='utf-8')
        write_json(self.manifests/f'openalex_topics_{key}.json',{'provider':'OpenAlex','retrieved_utc':now_utc(),'query':query,'returned_records':len(rows),'sampling':'deterministic_random'})
        return rows

    def topic_year_counts(self, topic_id, start_year, end_year):
        tid=str(topic_id).split('/')[-1]
        query={'topic_year_counts':tid,'start_year':int(start_year),'end_year':int(end_year)}; key=stable_key(query); cf=self.cache/f'counts_{key}.json'
        if cf.exists():return json.loads(cf.read_text(encoding='utf-8'))
        params={'api_key':self.api_key,'filter':f'topics.id:{tid},from_publication_date:{int(start_year)}-01-01,to_publication_date:{int(end_year)}-12-31',
                'group_by':'publication_year','per_page':100,'cursor':'*'}
        groups=[]
        while True:
            data=self._get('works',params).json(); groups.extend(data.get('group_by',[]) or [])
            nxt=(data.get('meta') or {}).get('next_cursor')
            if not nxt:break
            params['cursor']=nxt
        counts={str(g.get('key')):int(g.get('count') or 0) for g in groups if g.get('key') not in {None,-111,'-111'}}
        cf.write_text(json.dumps(counts),encoding='utf-8')
        return counts
