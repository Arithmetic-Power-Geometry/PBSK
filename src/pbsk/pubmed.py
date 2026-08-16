from __future__ import annotations
import json, os, time, xml.etree.ElementTree as ET
from pathlib import Path
import requests
from .utils import ensure, stable_key, write_json, now_utc, backoff_sleep

class PubMedClient:
    def __init__(self, cfg, api_key=None, cache_dir='cache/pubmed'):
        self.cfg=cfg; self.api_key=api_key or os.getenv('NCBI_API_KEY')
        self.base=cfg['base_url'].rstrip('/'); self.cache=ensure(cache_dir); self.manifests=ensure('cache/manifests')
        self.tool=cfg.get('tool','PBSK'); self.email=os.getenv(cfg.get('contact_email_env','PBSK_CONTACT_EMAIL'),'').strip()
        self.session=requests.Session()

    def _get(self, endpoint, params):
        params=dict(params); params['tool']=self.tool
        if self.email: params['email']=self.email
        if self.api_key: params['api_key']=self.api_key
        for attempt in range(int(self.cfg.get('max_retries',6))):
            try:
                r=self.session.get(f'{self.base}/{endpoint}',params=params,timeout=self.cfg.get('timeout_seconds',60))
                if r.status_code in {429,500,502,503,504}: backoff_sleep(attempt); continue
                r.raise_for_status();
                time.sleep(0.11 if self.api_key else 0.35)
                return r
            except requests.RequestException:
                if attempt+1>=int(self.cfg.get('max_retries',6)): raise
                backoff_sleep(attempt)
        raise RuntimeError('PubMed request failed')

    def search(self, term, start_year, end_year, retmax=250):
        q=f'({term}) AND {start_year}:{end_year}[dp]'
        key=stable_key({'q':q,'retmax':retmax}); cf=self.cache/f'search_{key}.json'
        if cf.exists(): return json.loads(cf.read_text(encoding='utf-8'))
        p={'db':'pubmed','term':q,'retmode':'json','retmax':int(retmax),'sort':'pub date'}
        r=self._get('esearch.fcgi',p); d=r.json()['esearchresult']; ids=d.get('idlist',[])
        cf.write_text(json.dumps(ids),encoding='utf-8')
        write_json(self.manifests/f'pubmed_search_{key}.json',{'provider':'NCBI PubMed','retrieved_utc':now_utc(),'query':q,'returned_ids':len(ids),'reported_count':int(d.get('count',0))})
        return ids

    @staticmethod
    def _text(node):
        if node is None: return ''
        return ''.join(node.itertext()).strip()

    def fetch(self, pmids):
        if not pmids: return []
        key=stable_key({'ids':list(pmids)}); cf=self.cache/f'fetch_{key}.json'
        if cf.exists(): return json.loads(cf.read_text(encoding='utf-8'))
        out=[]; bs=int(self.cfg.get('batch_size',200))
        for i in range(0,len(pmids),bs):
            batch=pmids[i:i+bs]
            r=self._get('efetch.fcgi',{'db':'pubmed','id':','.join(batch),'retmode':'xml'})
            root=ET.fromstring(r.content)
            for art in root.findall('.//PubmedArticle'):
                cit=art.find('./MedlineCitation'); article=cit.find('./Article') if cit is not None else None
                pmid=self._text(cit.find('./PMID')) if cit is not None else ''
                title=self._text(article.find('./ArticleTitle')) if article is not None else ''
                abs_text=' '.join(self._text(x) for x in article.findall('./Abstract/AbstractText')) if article is not None else ''
                year=''
                if article is not None:
                    y=article.find('./Journal/JournalIssue/PubDate/Year')
                    if y is not None: year=self._text(y)
                    if not year:
                        md=article.find('./Journal/JournalIssue/PubDate/MedlineDate');
                        if md is not None: year=''.join(ch for ch in self._text(md)[:4] if ch.isdigit())
                mesh=[self._text(m.find('./DescriptorName')) for m in cit.findall('./MeshHeadingList/MeshHeading')] if cit is not None else []
                out.append({'id':f'PMID:{pmid}','pmid':pmid,'title':title,'abstract':abs_text,'publication_year':int(year) if str(year).isdigit() else None,
                            'topic_ids':[m for m in mesh if m], 'referenced_works_count':0,'cited_by_count':0})
        cf.write_text(json.dumps(out),encoding='utf-8')
        write_json(self.manifests/f'pubmed_fetch_{key}.json',{'provider':'NCBI PubMed','retrieved_utc':now_utc(),'requested_ids':len(pmids),'returned_records':len(out)})
        return out
