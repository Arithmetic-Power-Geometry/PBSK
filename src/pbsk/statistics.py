from __future__ import annotations
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

# Confirmatory family is deliberately small. core_geometry_score was identified in v3 and
# must be interpreted confirmatorily only in the independent v4 power-validation cohort.
CONFIRMATORY_METRICS=['skg','collision_index','sequence_order_score','bookwide_pbsk','core_geometry_score']
EXPLORATORY_METRICS=['pbs','possibility_pressure','question_pressure','anomaly_pressure','doubt_tension',
                     'pattern_formation','analogical_transfer','bridge_formation','surprise_geometry',
                     'insight_coherence','leap_nonlinearity','originality_risk',
                     'stage_possibility','stage_question','stage_pattern','stage_imagination','stage_insight','stage_discovery_readiness']
CORE_METRICS=CONFIRMATORY_METRICS+EXPLORATORY_METRICS


def cohens_d_paired(a,b):
    d=np.asarray(a,dtype=float)-np.asarray(b,dtype=float); d=d[np.isfinite(d)]
    sd=d.std(ddof=1) if len(d)>1 else 0
    return float(d.mean()/sd) if len(d) and sd>0 else 0.0


def paired_permutation(a,b,n_iter=5000,seed=17,alternative='two-sided'):
    rng=np.random.default_rng(seed); d=np.asarray(a,dtype=float)-np.asarray(b,dtype=float); d=d[np.isfinite(d)]
    if len(d)==0:return np.nan
    obs=float(d.mean())
    if np.allclose(d,0):return 1.0
    vals=np.array([(d*rng.choice([-1,1],size=len(d))).mean() for _ in range(int(n_iter))])
    return float((1+np.sum(vals>=obs))/(len(vals)+1)) if alternative=='greater' else float((1+np.sum(np.abs(vals)>=abs(obs)))/(len(vals)+1))


def _bh(p):
    p=np.asarray(p,dtype=float); n=len(p)
    if n==0:return p
    order=np.argsort(p); ranked=np.empty(n,float); prev=1.0
    for i in range(n-1,-1,-1):
        idx=order[i]; val=min(prev,p[idx]*n/(i+1)); ranked[idx]=val; prev=val
    return np.clip(ranked,0,1)


def _safe_wilcoxon_greater(pos,ctrl):
    a=np.asarray(pos,dtype=float); b=np.asarray(ctrl,dtype=float); d=a-b; d=d[np.isfinite(d)]
    if len(d)==0 or np.allclose(d,0):return 1.0
    try:return float(wilcoxon(a,b,zero_method='wilcox',alternative='greater').pvalue)
    except (ValueError,FloatingPointError):return 1.0


def _eligible(d):
    if 'quality_eligible' in d.columns:
        return d[pd.to_numeric(d.quality_eligible,errors='coerce').fillna(0).astype(int)==1]
    return d


def hypothesis_table(feature_rows, permutation_iterations=5000, seed=17, cohort='landmark'):
    out=[]; required={'offset','target','match_case_id'}
    if feature_rows is None or feature_rows.empty or not required.issubset(feature_rows.columns):return pd.DataFrame()
    f=_eligible(feature_rows)
    for offset in sorted(pd.to_numeric(f['offset'],errors='coerce').dropna().unique(),reverse=True):
        z=f[pd.to_numeric(f['offset'],errors='coerce')==offset]
        for metric in [m for m in CORE_METRICS if m in z.columns]:
            pos=z[z.target==1][['match_case_id',metric]].groupby('match_case_id',as_index=False).mean().rename(columns={metric:'pos'})
            ctrl=z[z.target==0].groupby('match_case_id',as_index=False)[metric].mean().rename(columns={metric:'ctrl'})
            m=pos.merge(ctrl,on='match_case_id').dropna()
            if len(m)<3:continue
            out.append({'cohort':cohort,'offset':int(offset),'metric':metric,'family':'confirmatory' if metric in CONFIRMATORY_METRICS else 'exploratory',
                        'n_pairs':len(m),'positive_mean':m.pos.mean(),'control_mean':m.ctrl.mean(),'mean_difference':(m.pos-m.ctrl).mean(),
                        'paired_cohens_d':cohens_d_paired(m.pos,m.ctrl),'wilcoxon_one_sided_p':_safe_wilcoxon_greater(m.pos,m.ctrl),
                        'permutation_one_sided_p':paired_permutation(m.pos,m.ctrl,permutation_iterations,seed+int(offset),'greater')})
    tab=pd.DataFrame(out)
    if not tab.empty:
        tab['bh_fdr_permutation']=np.nan
        # FDR is controlled within prespecified offset x family, not across unrelated exploratory tests.
        for (_,fam),idx in tab.groupby(['offset','family']).groups.items():
            tab.loc[idx,'bh_fdr_permutation']=_bh(tab.loc[idx,'permutation_one_sided_p'].fillna(1).to_numpy())
    return tab


def transformation_test(rows, permutation_iterations=5000, seed=17):
    required={'target','match_case_id'}
    if rows is None or rows.empty or not required.issubset(rows.columns):return pd.DataFrame()
    out=[]
    for metric in ['post_growth','topic_diffusion','normalization_index','post_adoption','transformation']:
        if metric not in rows.columns:continue
        pos=rows[rows.target==1].groupby('match_case_id')[metric].mean(); ctrl=rows[rows.target==0].groupby('match_case_id')[metric].mean()
        m=pd.concat([pos.rename('pos'),ctrl.rename('ctrl')],axis=1).dropna()
        if len(m)<3:continue
        out.append({'metric':metric,'n_pairs':len(m),'positive_mean':m.pos.mean(),'control_mean':m.ctrl.mean(),'mean_difference':(m.pos-m.ctrl).mean(),
                    'paired_cohens_d':cohens_d_paired(m.pos,m.ctrl),'wilcoxon_one_sided_p':_safe_wilcoxon_greater(m.pos,m.ctrl),
                    'permutation_one_sided_p':paired_permutation(m.pos,m.ctrl,permutation_iterations,seed,'greater')})
    tab=pd.DataFrame(out)
    if not tab.empty:tab['bh_fdr_permutation']=_bh(tab.permutation_one_sided_p.fillna(1).to_numpy())
    return tab


def sequence_test(feature_rows):
    required={'offset','target','sequence_order_score'}
    if feature_rows is None or feature_rows.empty or not required.issubset(feature_rows.columns):return pd.DataFrame()
    f=_eligible(feature_rows); rows=[]
    for offset in sorted(pd.to_numeric(f.offset,errors='coerce').dropna().unique(),reverse=True):
        z=f[pd.to_numeric(f.offset,errors='coerce')==offset]
        for target,label in [(1,'breakthrough'),(0,'control')]:
            v=pd.to_numeric(z[z.target==target].sequence_order_score,errors='coerce').dropna()
            if len(v):rows.append({'offset':int(offset),'class':label,'n':len(v),'mean_sequence_order_score':v.mean(),'median_sequence_order_score':v.median()})
    return pd.DataFrame(rows)
