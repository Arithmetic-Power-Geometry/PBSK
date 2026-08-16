from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, balanced_accuracy_score

BASE=['n_docs','mean_citations','activity_recent','activity_prior','momentum','topic_entropy','years_covered']
LEGACY=['density_gap','boundary_activity','complementarity','momentum','recombination','convergence','skg','pbs']
STAGES=['stage_possibility','stage_question','stage_pattern','stage_imagination','stage_insight','stage_discovery_readiness']
BOOK=['possibility_pressure','question_pressure','anomaly_pressure','doubt_tension','pattern_formation',
      'cross_domain_similarity','analogical_transfer','bridge_formation','collision_index','surprise_geometry',
      'insight_coherence','leap_nonlinearity','originality_risk','sequence_order_score','bookwide_pbsk','core_geometry_score']+STAGES


def _eligible(df):
    if 'quality_eligible' not in df.columns:return df.copy()
    return df[pd.to_numeric(df.quality_eligible,errors='coerce').fillna(0).astype(int)==1].copy()


def _cv_predictions(df, features, model, group_col='match_case_id'):
    if df is None or not isinstance(df,pd.DataFrame) or df.empty:return None
    required={'target',group_col}
    if not required.issubset(df.columns):return None
    d=_eligible(df)
    features=[f for f in features if f in d.columns]
    if not features:return None
    d=d.dropna(subset=features+['target',group_col]).copy()
    if d.empty:return None
    y=d.target.astype(int).to_numpy(); groups=d[group_col].astype(str).to_numpy()
    uniq=np.unique(groups); n=min(5,len(uniq))
    if n<2 or len(np.unique(y))<2:return None
    pred=np.full(len(d),np.nan)
    cv=GroupKFold(n_splits=n)
    for tr,te in cv.split(d[features],y,groups):
        if len(np.unique(y[tr]))<2:continue
        m=clone(model); m.fit(d.iloc[tr][features],y[tr]); pred[te]=m.predict_proba(d.iloc[te][features])[:,1]
    ok=~np.isnan(pred)
    if ok.sum()==0:return None
    return y[ok],pred[ok],d.iloc[np.where(ok)[0]],features


def _group_bootstrap_ci(y,p,groups,metric='auc',iterations=1000,seed=17):
    y=np.asarray(y); p=np.asarray(p); groups=np.asarray(groups)
    ug=np.unique(groups); rng=np.random.default_rng(seed); vals=[]
    for _ in range(int(iterations)):
        samp=rng.choice(ug,size=len(ug),replace=True)
        idx=np.concatenate([np.where(groups==g)[0] for g in samp])
        yy=y[idx]; pp=p[idx]
        if len(np.unique(yy))<2:continue
        if metric=='auc': vals.append(roc_auc_score(yy,pp))
        elif metric=='pr': vals.append(average_precision_score(yy,pp))
        elif metric=='brier': vals.append(brier_score_loss(yy,pp))
    if not vals:return (np.nan,np.nan)
    return tuple(np.quantile(vals,[.025,.975]).astype(float))


def _metrics_row(name,y,p,d,used,bootstrap_iterations=1000):
    groups=d.match_case_id.astype(str).to_numpy()
    alo,ahi=_group_bootstrap_ci(y,p,groups,'auc',bootstrap_iterations,17)
    plo,phi=_group_bootstrap_ci(y,p,groups,'pr',bootstrap_iterations,19)
    blo,bhi=_group_bootstrap_ci(y,p,groups,'brier',bootstrap_iterations,23)
    return {'model':name,'n':len(y),'n_groups':len(np.unique(groups)),'n_features':len(used),
            'roc_auc':roc_auc_score(y,p),'roc_auc_ci_low':alo,'roc_auc_ci_high':ahi,
            'pr_auc':average_precision_score(y,p),'pr_auc_ci_low':plo,'pr_auc_ci_high':phi,
            'brier':brier_score_loss(y,p),'brier_ci_low':blo,'brier_ci_high':bhi,
            'balanced_accuracy_at_0_5':balanced_accuracy_score(y,(p>=.5).astype(int))}


def evaluate_models(df,bootstrap_iterations=100, compact=False):
    logit=lambda: Pipeline([('z',StandardScaler()),('m',LogisticRegression(max_iter=5000,class_weight='balanced',random_state=17,C=0.5))])
    full=sorted(set(BASE+LEGACY+BOOK))
    models={
      'Activity/citation baseline':(BASE,logit()),
      'Legacy PBS only':(['pbs'],logit()),
      'Book-wide PBSK only':(['bookwide_pbsk'],logit()),
      'Core geometry only':(['core_geometry_score'],logit()),
      'Book stages':(STAGES,logit()),
      'Baseline + legacy PBS':(sorted(set(BASE+LEGACY)),logit()),
      'Baseline + book-wide PBSK':(sorted(set(BASE+['bookwide_pbsk'])),logit()),
      'Baseline + core geometry':(sorted(set(BASE+['core_geometry_score'])),logit()),
      'Full theory logistic':(full,logit()),
      'Random forest full':(full,RandomForestClassifier(n_estimators=350,min_samples_leaf=3,max_features='sqrt',class_weight='balanced',random_state=17,n_jobs=-1)),
      'HistGradientBoosting full':(full,HistGradientBoostingClassifier(max_iter=250,max_leaf_nodes=15,l2_regularization=1.0,random_state=17)),
    }
    if compact:
        keep={'Activity/citation baseline','Book-wide PBSK only','Core geometry only','Baseline + core geometry','Full theory logistic'}
        models={k:v for k,v in models.items() if k in keep}
    rows=[]; preds=[]
    for name,(features,model) in models.items():
        res=_cv_predictions(df,features,model)
        if res is None:continue
        y,p,d,used=res
        if len(np.unique(y))<2:continue
        rows.append(_metrics_row(name,y,p,d,used,bootstrap_iterations))
        q=d[['region_id','match_case_id','offset','target','book_realm']].copy(); q['model']=name; q['probability']=p; preds.append(q)
    return pd.DataFrame(rows), pd.concat(preds,ignore_index=True) if preds else pd.DataFrame()


def incremental_value_table(preds,iterations=2000,seed=31):
    if preds is None or preds.empty:return pd.DataFrame()
    pairs=[('Activity/citation baseline','Baseline + legacy PBS'),('Activity/citation baseline','Baseline + book-wide PBSK'),
           ('Activity/citation baseline','Baseline + core geometry'),('Activity/citation baseline','Full theory logistic')]
    rows=[]; rng=np.random.default_rng(seed)
    key=['region_id','match_case_id','offset','target','book_realm']
    for base,aug in pairs:
        a=preds[preds.model==base][key+['probability']].rename(columns={'probability':'p0'})
        b=preds[preds.model==aug][key+['probability']].rename(columns={'probability':'p1'})
        m=a.merge(b,on=key)
        if m.empty or m.target.nunique()<2:continue
        obs=roc_auc_score(m.target,m.p1)-roc_auc_score(m.target,m.p0)
        groups=m.match_case_id.unique(); dif=[]
        for _ in range(int(iterations)):
            gs=rng.choice(groups,size=len(groups),replace=True)
            idx=np.concatenate([np.where(m.match_case_id.to_numpy()==g)[0] for g in gs])
            z=m.iloc[idx]
            if z.target.nunique()<2:continue
            dif.append(roc_auc_score(z.target,z.p1)-roc_auc_score(z.target,z.p0))
        lo,hi=(np.quantile(dif,[.025,.975]) if dif else (np.nan,np.nan))
        p=float((1+sum(x<=0 for x in dif))/(1+len(dif))) if dif else np.nan
        rows.append({'baseline_model':base,'augmented_model':aug,'n':len(m),'n_groups':len(groups),'delta_roc_auc':obs,'delta_ci_low':lo,'delta_ci_high':hi,'bootstrap_one_sided_p':p})
    return pd.DataFrame(rows)


def ablation_table(df):
    full=sorted(set(BASE+STAGES+['bookwide_pbsk','core_geometry_score']))
    model=Pipeline([('z',StandardScaler()),('m',LogisticRegression(max_iter=5000,class_weight='balanced',random_state=17,C=.5))])
    removals=['none']+[x for x in STAGES+['bookwide_pbsk','core_geometry_score'] if x in df.columns]
    rows=[]
    for removed in removals:
        fs=full if removed=='none' else [x for x in full if x!=removed]
        res=_cv_predictions(df,fs,model)
        if res is None:continue
        y,p,_,used=res
        rows.append({'removed_component':removed,'n':len(y),'n_features':len(used),'roc_auc':roc_auc_score(y,p),'pr_auc':average_precision_score(y,p),'brier':brier_score_loss(y,p)})
    out=pd.DataFrame(rows)
    if not out.empty and (out.removed_component=='none').any():
        ref=float(out.loc[out.removed_component=='none','roc_auc'].iloc[0]); out['delta_roc_auc_vs_full']=out.roc_auc-ref
    return out


def temporal_holdout_table(df):
    rows=[]
    if df.empty:return pd.DataFrame()
    for offset in sorted(pd.to_numeric(df.offset,errors='coerce').dropna().unique(),reverse=True):
        z=df[pd.to_numeric(df.offset,errors='coerce')==offset].copy(); perf,_=evaluate_models(z,bootstrap_iterations=80,compact=True)
        if perf.empty:continue
        perf.insert(0,'offset',int(offset)); rows.append(perf)
    return pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()


def realm_generalization(preds):
    if preds.empty:return pd.DataFrame()
    rows=[]
    for (model,realm),d in preds.groupby(['model','book_realm']):
        y=d.target.to_numpy(); p=d.probability.to_numpy()
        if len(np.unique(y))<2:continue
        rows.append({'model':model,'book_realm':realm,'n':len(d),'roc_auc':roc_auc_score(y,p),'pr_auc':average_precision_score(y,p),'brier':brier_score_loss(y,p)})
    return pd.DataFrame(rows)
