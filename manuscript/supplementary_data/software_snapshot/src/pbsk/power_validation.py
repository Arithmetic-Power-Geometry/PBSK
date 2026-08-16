from __future__ import annotations
import math
import numpy as np
import pandas as pd
from .retrieval import RegionSpec, _realm


def _growth(pre, post):
    return float(math.log1p(post)-math.log1p(pre))


def build_power_cohort(client, cfg):
    """Construct an independent, outcome-defined topic cohort for prospective validation.

    IMPORTANT: post-cutoff growth is used only to define the future outcome label. All PBSK
    predictors are subsequently computed with literature at or before the cutoff. This cohort is
    deliberately separate from the 12 landmark cases so v3-derived exploratory signals can be
    tested on independent groups rather than re-fit to the same landmarks.
    """
    pcfg=cfg['power_validation']; cutoff=int(pcfg['cutoff_year']); outcome_end=int(pcfg['outcome_end_year'])
    start=cutoff-int(cfg['experiment']['lookback_years'])+1
    topics=client.sample_topics(int(pcfg['topic_sample_size']),int(pcfg['minimum_topic_works']))
    rows=[]
    for t in topics:
        tid=t.get('id'); name=t.get('display_name') or ''
        if not tid or not name: continue
        counts=client.topic_year_counts(tid,start,outcome_end)
        pre=sum(int(counts.get(str(y),0)) for y in range(start,cutoff+1))
        post=sum(int(counts.get(str(y),0)) for y in range(cutoff+1,outcome_end+1))
        recent_pre=sum(int(counts.get(str(y),0)) for y in range(cutoff-2,cutoff+1))
        early_pre=sum(int(counts.get(str(y),0)) for y in range(start,min(cutoff-2,start+3)))
        dom=((t.get('domain') or {}).get('display_name') or 'Unassigned')
        field=((t.get('field') or {}).get('display_name') or 'Unassigned')
        if pre < int(pcfg['minimum_pre_count']): continue
        rows.append({'topic_id':tid,'topic_name':name,'domain':dom,'field':field,'book_realm':_realm(dom),
                     'pre_count':pre,'post_count':post,'recent_pre_count':recent_pre,'early_pre_count':early_pre,
                     'future_growth':_growth(pre,post),'future_ratio':(post+1)/(pre+1),'pre_momentum_ratio':(recent_pre+1)/(early_pre+1)})
    d=pd.DataFrame(rows)
    if len(d)<30:return pd.DataFrame(),pd.DataFrame(),[]
    # Within-domain ranks prevent one rapidly expanding domain from defining the outcome.
    d['growth_rank']=d.groupby('domain')['future_growth'].rank(pct=True,method='average')
    npos=min(int(pcfg['target_positive_topics']), max(10, len(d)//4))
    positives=d.sort_values(['growth_rank','future_growth'],ascending=False).head(npos).copy()
    positives['target']=1
    # Controls: same domain and closest pre-cutoff volume, excluding top-growth topics.
    pool=d[~d.topic_id.isin(positives.topic_id)].copy()
    controls=[]; used=set(); k=int(pcfg['controls_per_positive'])
    for i,p in positives.iterrows():
        cand=pool[(pool.domain==p.domain)&(~pool.topic_id.isin(used))].copy()
        if len(cand)<k: cand=pool[~pool.topic_id.isin(used)].copy()
        if cand.empty: continue
        cand['match_distance']=abs(np.log1p(cand.pre_count)-np.log1p(p.pre_count)) + 0.50*abs(np.log1p(cand.pre_momentum_ratio)-np.log1p(p.pre_momentum_ratio))
        take=cand.sort_values('match_distance').head(k)
        for _,c in take.iterrows():
            used.add(c.topic_id)
            controls.append({**c.to_dict(),'target':0,'match_topic_id':p.topic_id,'match_case_id':f'PV_{len(controls)//k:04d}'})
    # Assign stable matched-group IDs to positives after controls are formed.
    posrows=[]; specs=[]
    for j,(_,p) in enumerate(positives.iterrows()):
        gid=f'PV_{j:04d}'
        pr={**p.to_dict(),'match_case_id':gid,'match_topic_id':p.topic_id}; posrows.append(pr)
        specs.append(RegionSpec(f'{gid}_P',gid,p.topic_name,p.topic_name,p.domain,cutoff+1,1,p.book_realm,p.topic_id,'power_validation'))
        matched=[c for c in controls if c.get('match_topic_id')==p.topic_id]
        for z,c in enumerate(matched):
            specs.append(RegionSpec(f'{gid}_C{z+1}',gid,c['topic_name'],c['topic_name'],c['domain'],cutoff+1,0,c['book_realm'],c['topic_id'],'power_validation'))
    posdf=pd.DataFrame(posrows)
    ctrldf=pd.DataFrame(controls)
    return posdf,ctrldf,specs
