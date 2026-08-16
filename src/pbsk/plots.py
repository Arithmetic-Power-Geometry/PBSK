from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from .utils import ensure


def _has(df, *cols):
    return isinstance(df, pd.DataFrame) and (not df.empty) and all(c in df.columns for c in cols)


def _save(path):
    path=Path(path); ensure(path.parent); plt.tight_layout(); plt.savefig(path,dpi=300,bbox_inches='tight'); plt.close()
    return True


def benchmark_timeline(cases,path):
    if not _has(cases,'landmark_year','label'): return False
    d=cases.dropna(subset=['landmark_year','label']).sort_values('landmark_year')
    if d.empty:return False
    plt.figure(figsize=(10,6)); plt.scatter(d['landmark_year'],range(len(d)))
    plt.yticks(range(len(d)),d['label']); plt.xlabel('Landmark year'); plt.ylabel('Benchmark case'); plt.title('PBSK benchmark timeline'); return _save(path)


def temporal_score(df,path,metric='bookwide_pbsk',source='OpenAlex'):
    if not _has(df,'source','offset','target',metric):return False
    z=df[df['source']==source].dropna(subset=['offset','target',metric])
    if z.empty:return False
    g=z.groupby(['offset','target'],as_index=False)[metric].agg(['mean','sem']).reset_index(); plt.figure(figsize=(7,5))
    for target,label in [(1,'Breakthrough regions'),(0,'Matched controls')]:
        q=g[g['target']==target].sort_values('offset',ascending=False)
        if len(q):plt.errorbar(q['offset'],q['mean'],yerr=q['sem'].fillna(0),marker='o',capsize=4,label=label)
    plt.gca().invert_xaxis(); plt.xlabel('Years before landmark (T−Δ)'); plt.ylabel(metric.replace('_',' ').title()); plt.title(f'Temporal trajectory — {source}'); plt.legend(); return _save(path)


def stage_profile(df,path,source='OpenAlex',offset=1):
    stages=['possibility_pressure','question_pressure','anomaly_pressure','doubt_tension','pattern_formation','collision_index','insight_coherence','leap_nonlinearity']
    if not _has(df,'source','offset','target',*stages):return False
    z=df[(df['source']==source)&(df['offset']==offset)]
    if z.empty:return False
    pos=[z[z['target']==1][col].mean() for col in stages]; ctrl=[z[z['target']==0][col].mean() for col in stages]
    x=np.arange(len(stages)); w=.38; plt.figure(figsize=(11,5)); plt.bar(x-w/2,pos,w,label='Breakthrough'); plt.bar(x+w/2,ctrl,w,label='Matched control')
    plt.xticks(x,[s.replace('_','\n') for s in stages],rotation=0); plt.ylabel('Mean normalized proxy'); plt.title(f'Book-derived stage profile at T−{offset}'); plt.legend(); return _save(path)


def distribution(df,path,metric='bookwide_pbsk',source='OpenAlex',offset=1):
    if not _has(df,'source','offset','target',metric):return False
    z=df[(df['source']==source)&(df['offset']==offset)].dropna(subset=[metric])
    if z.empty:return False
    a=z[z['target']==1][metric]; b=z[z['target']==0][metric]
    if a.empty and b.empty:return False
    plt.figure(figsize=(7,5)); plt.boxplot([a,b],tick_labels=['Breakthrough','Matched control'],showmeans=True)
    plt.ylabel(metric.replace('_',' ').title()); plt.title(f'{metric.replace("_"," ").title()} at T−{offset} — {source}'); return _save(path)


def model_performance(tab,path):
    if not _has(tab,'model','roc_auc'):return False
    d=tab.dropna(subset=['model','roc_auc']).sort_values('roc_auc')
    if d.empty:return False
    plt.figure(figsize=(9,6)); plt.barh(d['model'],d['roc_auc']); plt.axvline(.5,linestyle='--',linewidth=1); plt.xlabel('Grouped out-of-sample ROC-AUC'); plt.title('Predictive discrimination'); return _save(path)


def temporal_performance(tab,path):
    if not _has(tab,'model','offset','roc_auc'):return False
    focus=tab[tab['model'].isin(['Activity/citation baseline','Book-wide PBSK only','Full theory model'])].dropna(subset=['offset','roc_auc'])
    if focus.empty:return False
    plt.figure(figsize=(8,5))
    for model,d in focus.groupby('model'):
        q=d.sort_values('offset',ascending=False); plt.plot(q['offset'],q['roc_auc'],marker='o',label=model)
    plt.gca().invert_xaxis(); plt.axhline(.5,linestyle='--',linewidth=1); plt.xlabel('Years before landmark'); plt.ylabel('ROC-AUC'); plt.title('Temporal out-of-sample prediction'); plt.legend(); return _save(path)


def ablation(tab,path):
    if not _has(tab,'removed_component','delta_roc_auc_vs_full'):return False
    d=tab[tab['removed_component']!='none'].dropna(subset=['delta_roc_auc_vs_full']).sort_values('delta_roc_auc_vs_full')
    if d.empty:return False
    plt.figure(figsize=(9,7)); plt.barh(d['removed_component'],d['delta_roc_auc_vs_full']); plt.axvline(0,linewidth=1)
    plt.xlabel('Δ ROC-AUC after component removal'); plt.title('Book-wide PBSK ablation'); return _save(path)


def transformation(tab,path):
    metrics=['post_growth','topic_diffusion','normalization_index','post_adoption','transformation']
    if not _has(tab,'target',*metrics):return False
    z=tab.groupby('target')[metrics].mean()
    if z.empty:return False
    x=np.arange(len(metrics)); w=.38; plt.figure(figsize=(9,5))
    plt.bar(x-w/2,[z.loc[1,m] if 1 in z.index else np.nan for m in metrics],w,label='Breakthrough')
    plt.bar(x+w/2,[z.loc[0,m] if 0 in z.index else np.nan for m in metrics],w,label='Matched control')
    plt.xticks(x,[m.replace('_','\n') for m in metrics]); plt.ylabel('Mean normalized outcome'); plt.title('Post-landmark transformation'); plt.legend(); return _save(path)


def sequence_plot(tab,path):
    if not _has(tab,'offset','class','mean_sequence_order_score'):return False
    q=tab.dropna(subset=['offset','class','mean_sequence_order_score'])
    if q.empty:return False
    piv=q.pivot_table(index='offset',columns='class',values='mean_sequence_order_score',aggfunc='mean').sort_index(ascending=False)
    if piv.empty:return False
    ax=piv.plot(kind='bar',figsize=(7,5)); ax.set_ylabel('Mean sequence-order score'); ax.set_xlabel('Years before landmark'); ax.set_title('Support for book-derived stage ordering'); plt.tight_layout(); plt.savefig(path,dpi=300,bbox_inches='tight'); plt.close(); return True


def replication(openalex,pubmed,path):
    required=('offset','match_case_id','target','bookwide_pbsk')
    if not _has(openalex,*required) or not _has(pubmed,*required):return False
    oa=openalex[openalex['offset']==1].dropna(subset=['match_case_id','target','bookwide_pbsk'])
    pm=pubmed[pubmed['offset']==1].dropna(subset=['match_case_id','target','bookwide_pbsk'])
    if oa.empty or pm.empty:return False
    # Bracket selection is intentional: unlike GroupBy attribute access it remains
    # correct even if pandas changes attribute dispatch or a provider adds a colliding name.
    a=oa.groupby(['match_case_id','target'],as_index=False)['bookwide_pbsk'].mean().rename(columns={'bookwide_pbsk':'openalex'})
    p=pm.groupby(['match_case_id','target'],as_index=False)['bookwide_pbsk'].mean().rename(columns={'bookwide_pbsk':'pubmed'})
    m=a.merge(p,on=['match_case_id','target'],how='inner').dropna(subset=['openalex','pubmed'])
    if len(m)<2:return False
    plt.figure(figsize=(6,6)); plt.scatter(m['openalex'],m['pubmed']); lo=min(m['openalex'].min(),m['pubmed'].min()); hi=max(m['openalex'].max(),m['pubmed'].max())
    if np.isfinite(lo) and np.isfinite(hi):plt.plot([lo,hi],[lo,hi],linestyle='--')
    plt.xlabel('OpenAlex book-wide PBSK (T−1)'); plt.ylabel('PubMed book-wide PBSK (T−1)'); plt.title('Cross-source replication'); return _save(path)


def realm_profile(df,path):
    if not _has(df,'source','offset','target','book_realm','bookwide_pbsk'):return False
    z=df[(df['source']=='OpenAlex')&(df['offset']==1)&(df['target']==1)].dropna(subset=['book_realm','bookwide_pbsk'])
    if z.empty:return False
    z=z.groupby('book_realm')['bookwide_pbsk'].mean().sort_values()
    if z.empty:return False
    plt.figure(figsize=(7,5)); plt.barh(z.index,z.values); plt.xlabel('Mean book-wide PBSK'); plt.title('Creative-universe realm profile'); return _save(path)


def retrieval_qc(qc,path):
    if not _has(qc,'source','window','records'):return False
    q=qc.dropna(subset=['source','window','records'])
    if q.empty:return False
    d=q.groupby(['source','window'])['records'].mean().unstack(fill_value=0); ax=d.plot(kind='bar',figsize=(7,5)); ax.set_ylabel('Mean records per region'); ax.set_title('Retrieval coverage by window'); plt.tight_layout(); plt.savefig(path,dpi=300,bbox_inches='tight'); plt.close(); return True
