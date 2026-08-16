from __future__ import annotations
import pandas as pd, numpy as np
from .benchmark import load_cases, load_controls, validate_matching
from .features import compute_region_features, compute_scores, compute_transformation_features
from .config import load_config
from .utils import ensure, write_json


def synthetic_frame(seed=17,n=120,start=2010,end=2020):
    rng=np.random.default_rng(seed); years=rng.integers(start,end+1,size=n)
    question=['unknown question gap challenge' if i%7==0 else '' for i in range(n)]
    anomaly=['unexpected anomaly contradiction' if i%11==0 else '' for i in range(n)]
    return pd.DataFrame({'title':[f'knowledge bridge concept {i%9} method {i%4} {question[i]}' for i in range(n)],
      'abstract':[f'possible future pattern framework {i%3} integration mechanism {i%6} {anomaly[i]}' for i in range(n)],
      'publication_year':years,'cited_by_count':rng.poisson(12,size=n),'referenced_works_count':rng.poisson(28,size=n),
      'topic_ids':[[f'T{i%5}',f'T{(i+2)%8}'] for i in range(n)]})


def run_smoke(config_path='config/default.yaml'):
    cfg=load_config(config_path); cases=load_cases(); ctrls=load_controls(); validate_matching(cases,ctrls)
    pre=synthetic_frame(); post=synthetic_frame(18,90,2021,2025)
    f=compute_region_features(pre,2019,{**cfg['analysis'],'min_documents_for_semantics':12}); skg,pbs,bwide=compute_scores(f,cfg['analysis']['fixed_pbs_weights'])
    trans=compute_transformation_features(pre,post,2020)
    out=ensure('results'); ensure(out/'tables'); ensure(out/'figures')
    rep={'status':'PASS','cases':len(cases),'controls':len(ctrls),'book_chapters_operationalized':40,'synthetic_skg':skg,'synthetic_legacy_pbs':pbs,
         'synthetic_bookwide_pbsk':bwide,'synthetic_transformation':trans['transformation'],
         'note':'Smoke mode validates the complete book-wide computation path only. It is not an empirical breakthrough result.'}
    write_json(out/'smoke_report.json',rep); return rep
