from __future__ import annotations
import math, re, warnings
from itertools import combinations
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Book-wide operational features. These are observable literature proxies for the
# conceptual sequence in THE IMPOSSIBLE IDEA, not direct measurements of private cognition.
BOOK_FEATURES = [
    'possibility_pressure','question_pressure','anomaly_pressure','doubt_tension',
    'pattern_formation','cross_domain_similarity','analogical_transfer','bridge_formation',
    'collision_index','surprise_geometry','insight_coherence','leap_nonlinearity',
    'originality_risk','density_gap','boundary_activity','complementarity','momentum',
    'recombination','convergence','sequence_order_score',
    'stage_possibility','stage_question','stage_pattern','stage_imagination','stage_insight','stage_discovery_readiness',
    'core_geometry_score'
]
LEGACY_FEATURES=['density_gap','boundary_activity','complementarity','momentum','recombination','convergence']

LEXICONS = {
    'question': ['question','unknown','unanswered','problem','challenge','gap','open problem','we ask','whether','why','how'],
    'anomaly': ['anomal','unexpected','contradict','inconsisten','paradox','uncertain','confus','failure','deviation','discrepanc','unexplained'],
    'doubt': ['assumption','challenge','limitation','impossible','unlikely','controvers','debate','skeptic','doubt','boundary','constraint'],
    'insight': ['insight','framework','mechanism','unified','coherent','explain','architecture','model','principle','structure'],
    'possibility': ['possible','possibility','potential','could','may enable','opportunity','future','novel','new approach','emerg'],
    'normalization': ['established','standard','widely used','routine','common','canonical','accepted','mature','conventional'],
}


def _safe_float(x, default=0.0):
    try:
        v=float(x)
        return v if np.isfinite(v) else default
    except Exception:
        return default


def normalized_entropy(values):
    a=np.asarray(values,dtype=float); a=a[a>0]
    if len(a)<=1 or a.sum()<=0: return 0.0
    p=a/a.sum(); return float(-(p*np.log(p)).sum()/np.log(len(p)))


def _topic_entropy(df):
    counts={}
    if 'topic_ids' not in df: return 0.0
    for ts in df.topic_ids:
        if not isinstance(ts,(list,tuple)): continue
        for t in set(ts): counts[t]=counts.get(t,0)+1
    return normalized_entropy(list(counts.values()))


def _topic_bridge_share(df):
    if 'topic_ids' not in df or len(df)==0: return 0.0
    vals=[]
    for ts in df.topic_ids:
        vals.append(1.0 if isinstance(ts,(list,tuple)) and len(set(ts))>=2 else 0.0)
    return float(np.mean(vals)) if vals else 0.0


def _text(df):
    if df.empty: return pd.Series(dtype=str)
    return (df.get('title',pd.Series('',index=df.index)).fillna('')+' '+df.get('abstract',pd.Series('',index=df.index)).fillna('')).str.lower().str.strip()


def _lexical_rate(df, terms):
    texts=_text(df)
    if texts.empty: return 0.0
    pat='|'.join(re.escape(t) for t in terms)
    return float(texts.str.contains(pat,regex=True,na=False).mean())


def _semantic_state(df, cutoff_year, cfg):
    docs=_text(df).tolist()
    min_docs=int(cfg.get('min_documents_for_semantics',12))
    empty={k:0.0 for k in ['density_gap','boundary_activity','convergence','surprise_geometry','insight_coherence','pattern_formation','cross_domain_similarity','originality_risk']}
    empty['Z']=None; empty['years']=None; empty['labels']=None
    if len(docs)<min_docs or sum(bool(x) for x in docs)<min_docs: return empty
    try:
        vec=TfidfVectorizer(stop_words='english',max_features=int(cfg.get('tfidf_max_features',6000)),ngram_range=(1,2),min_df=2)
        X=vec.fit_transform(docs)
        if X.shape[1]<3: return empty
        k=min(int(cfg.get('svd_components',30)),max(2,X.shape[1]-1),max(2,X.shape[0]-1))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', RuntimeWarning); warnings.simplefilter('ignore', ConvergenceWarning)
            Z=TruncatedSVD(n_components=k,random_state=17).fit_transform(X)
        if np.unique(np.round(Z,10),axis=0).shape[0] < 2: return empty
        km=KMeans(n_clusters=2,n_init=20,random_state=17).fit(Z); labels=km.labels_; cents=km.cluster_centers_
        sim=float(cosine_similarity(cents[0].reshape(1,-1),cents[1].reshape(1,-1))[0,0])
        density_gap=float(np.clip(1-(sim+1)/2,0,1))
        sims=cosine_similarity(Z,cents); margin=np.abs(sims[:,0]-sims[:,1])
        boundary=float(np.mean(margin<float(cfg.get('boundary_margin',0.12))))
        years=pd.to_numeric(df.publication_year,errors='coerce').fillna(cutoff_year).astype(int).to_numpy()
        early_mask=years<=cutoff_year-4; recent_mask=years>=cutoff_year-2

        def two_cluster_similarity(A):
            if len(A)<6 or np.unique(np.round(A,10),axis=0).shape[0]<2: return np.nan
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', ConvergenceWarning)
                lab=KMeans(n_clusters=2,n_init=10,random_state=19).fit(A).labels_
            if len(set(lab))<2:return np.nan
            ca=A[lab==0].mean(axis=0).reshape(1,-1); cb=A[lab==1].mean(axis=0).reshape(1,-1)
            return float(cosine_similarity(ca,cb)[0,0])

        es,rs=two_cluster_similarity(Z[early_mask]),two_cluster_similarity(Z[recent_mask])
        convergence=0.0 if np.isnan(es) or np.isnan(rs) else float(np.clip((rs-es+1)/2,0,1))

        # Surprise: distance of recent work from the earlier knowledge centroid.
        surprise=0.0; originality=0.0; coherence=0.0; pattern=0.0
        if early_mask.sum()>=3 and recent_mask.sum()>=3:
            ec=Z[early_mask].mean(axis=0).reshape(1,-1)
            rec=Z[recent_mask]
            rcos=cosine_similarity(rec,ec).reshape(-1)
            surprise=float(np.clip(np.mean((1-rcos)/2),0,1)); originality=surprise
            def cohesion(A):
                if len(A)<3:return 0.0
                c=A.mean(axis=0).reshape(1,-1); return float(np.clip((cosine_similarity(A,c).mean()+1)/2,0,1))
            ce,cr=cohesion(Z[early_mask]),cohesion(rec)
            coherence=float(np.clip((cr-ce+1)/2,0,1))
            # Pattern formation rewards simultaneous reorganization and recent coherence.
            pattern=float(np.clip(0.5*coherence+0.5*(1-surprise),0,1))
        cross_similarity=float(np.clip((sim+1)/2,0,1))
        return {'density_gap':density_gap,'boundary_activity':boundary,'convergence':convergence,
                'surprise_geometry':surprise,'insight_coherence':coherence,'pattern_formation':pattern,
                'cross_domain_similarity':cross_similarity,'originality_risk':originality,
                'Z':Z,'years':years,'labels':labels}
    except (ValueError,MemoryError):
        return empty


def _annual_signal(df, year, lexicon):
    x=df[pd.to_numeric(df.publication_year,errors='coerce').fillna(-1).astype(int)==int(year)]
    return _lexical_rate(x,LEXICONS[lexicon]) if len(x) else 0.0


def _sequence_score(df, cutoff_year):
    """Order agreement for the book-derived pre-discovery sequence.

    Expected observable proxy order: possibility -> question -> anomaly/doubt -> collision/pattern -> insight -> leap.
    We estimate onset years from annual signal maxima/upper quantiles. A value of 1 means fully concordant,
    0 means fully discordant, and 0.5 is neutral/tied-heavy.
    """
    years=sorted(set(pd.to_numeric(df.publication_year,errors='coerce').dropna().astype(int)))
    years=[y for y in years if y<=cutoff_year]
    if len(years)<4:return 0.5
    counts={y:int((pd.to_numeric(df.publication_year,errors='coerce')==y).sum()) for y in years}
    signals={
        'P':[(_annual_signal(df,y,'possibility')) for y in years],
        'Q':[(_annual_signal(df,y,'question')) for y in years],
        'A':[max(_annual_signal(df,y,'anomaly'),_annual_signal(df,y,'doubt')) for y in years],
        'C':[math.log1p(counts[y]) for y in years],
        'I':[(_annual_signal(df,y,'insight')) for y in years],
        'L':[math.log1p(counts[y])-math.log1p(counts.get(y-1,0)) for y in years],
    }
    onset=[]
    for key in ['P','Q','A','C','I','L']:
        a=np.asarray(signals[key],dtype=float)
        if np.allclose(a,a[0]): onset.append(years[len(years)//2]); continue
        threshold=float(np.quantile(a,0.7))
        idx=np.where(a>=threshold)[0]
        onset.append(years[int(idx[0])] if len(idx) else years[-1])
    concord=0; total=0
    for i,j in combinations(range(len(onset)),2):
        total+=1
        if onset[i]<onset[j]: concord+=1
        elif onset[i]==onset[j]: concord+=0.5
    return float(concord/total) if total else 0.5


def _geomean01(values, eps=1e-6):
    a=np.clip(np.asarray(values,dtype=float),eps,1.0)
    return float(np.exp(np.mean(np.log(a)))) if len(a) else 0.0


def compute_region_features(df:pd.DataFrame, cutoff_year:int, cfg:dict):
    years_all=pd.to_numeric(df.get('publication_year',pd.Series(dtype=float)),errors='coerce')
    x=df[years_all.fillna(9999).astype(int)<=int(cutoff_year)].copy()
    if x.empty:
        base={k:0.0 for k in BOOK_FEATURES}
        return {**base,'n_docs':0,'mean_citations':0.0,'topic_entropy':0.0,'activity_recent':0,'activity_prior':0,'question_rate':0.0,'years_covered':0,'quality_eligible':0}
    years=pd.to_numeric(x.publication_year,errors='coerce').dropna().astype(int)
    counts=years.value_counts().sort_index()
    recent=int(counts[counts.index>=cutoff_year-2].sum())
    prior=int(counts[(counts.index>=cutoff_year-5)&(counts.index<=cutoff_year-3)].sum())
    momentum=float((np.tanh((math.log1p(recent)-math.log1p(prior))/2)+1)/2)
    complementarity=_topic_entropy(x)
    refs=pd.to_numeric(x.get('referenced_works_count',pd.Series(0,index=x.index)),errors='coerce').fillna(0).astype(float)
    recombination=float(np.tanh(refs.mean()/30.0)) if len(refs) else 0.0
    sem=_semantic_state(x,cutoff_year,{**cfg,'min_documents_for_semantics':cfg.get('min_documents_for_semantics',12)})
    q=_lexical_rate(x,LEXICONS['question']); a=_lexical_rate(x,LEXICONS['anomaly']); d=_lexical_rate(x,LEXICONS['doubt']); p=_lexical_rate(x,LEXICONS['possibility'])
    bridge=_topic_bridge_share(x)
    # collision requires variety + a bridge + semantic separation.
    collision=float(np.clip(complementarity*bridge*(0.5+0.5*sem['density_gap']),0,1))
    analogical=float(np.clip(bridge*sem['cross_domain_similarity']*max(recombination,0.05),0,1))
    possibility=float(np.clip(0.35*sem['density_gap']+0.25*complementarity+0.20*p+0.20*sem['boundary_activity'],0,1))
    # bounded lexical transformations keep sparse scholarly language from dominating.
    question=float(np.tanh(4*q)); anomaly=float(np.tanh(5*a)); doubt=float(np.tanh(5*d))
    seq=_sequence_score(x,cutoff_year)
    cites=pd.to_numeric(x.get('cited_by_count',pd.Series(0,index=x.index)),errors='coerce').fillna(0).astype(float)
    leap=_leap_score(counts)
    stage_possibility=_geomean01([possibility,sem['density_gap'],sem['boundary_activity']])
    stage_question=_geomean01([question,anomaly,doubt])
    stage_pattern=_geomean01([sem['pattern_formation'],analogical,bridge,collision,max(complementarity,1e-6)])
    stage_imagination=_geomean01([sem['surprise_geometry'],sem['originality_risk'],sem['cross_domain_similarity']])
    stage_insight=_geomean01([sem['insight_coherence'],sem['convergence'],max(recombination,1e-6)])
    stage_discovery=_geomean01([leap,momentum,seq])
    years_covered=int(years.nunique()) if len(years) else 0
    min_docs=int(cfg.get('min_documents_for_inference',60)); min_years=int(cfg.get('min_years_covered_for_inference',5))
    quality=int(len(x)>=min_docs and years_covered>=min_years and recent>0 and prior>0)
    core_geometry=_geomean01([max(sem['density_gap']*sem['boundary_activity']*max(complementarity,1e-6),1e-9)**(1/3),collision,seq])
    return {
        'possibility_pressure':possibility,'question_pressure':question,'anomaly_pressure':anomaly,'doubt_tension':doubt,
        'pattern_formation':sem['pattern_formation'],'cross_domain_similarity':sem['cross_domain_similarity'],
        'analogical_transfer':analogical,'bridge_formation':bridge,'collision_index':collision,
        'surprise_geometry':sem['surprise_geometry'],'insight_coherence':sem['insight_coherence'],
        'leap_nonlinearity':leap,'originality_risk':sem['originality_risk'],
        'density_gap':sem['density_gap'],'boundary_activity':sem['boundary_activity'],'complementarity':float(complementarity),
        'momentum':momentum,'recombination':recombination,'convergence':sem['convergence'],'sequence_order_score':seq,
        'stage_possibility':stage_possibility,'stage_question':stage_question,'stage_pattern':stage_pattern,
        'stage_imagination':stage_imagination,'stage_insight':stage_insight,'stage_discovery_readiness':stage_discovery,
        'core_geometry_score':core_geometry,
        'n_docs':int(len(x)),'mean_citations':float(cites.mean()) if len(cites) else 0.0,'topic_entropy':float(complementarity),
        'activity_recent':recent,'activity_prior':prior,'question_rate':q,'years_covered':years_covered,'quality_eligible':quality,
    }


def _leap_score(counts):
    if counts is None or len(counts)<3:return 0.0
    idx=range(int(counts.index.min()),int(counts.index.max())+1)
    arr=np.array([math.log1p(float(counts.get(y,0))) for y in idx])
    dif=np.diff(arr)
    if len(dif)==0:return 0.0
    return float(np.clip((np.tanh(float(np.max(dif)))+1)/2,0,1))


def compute_transformation_features(pre_df:pd.DataFrame, post_df:pd.DataFrame, landmark_year:int):
    # Empty or partial provider responses must be valid inputs.  This is especially
    # important for PubMed replication windows where a query can legitimately
    # return zero records.  Missing publication_year is treated as no usable rows,
    # never as a fatal workflow error.
    pre_df = pre_df if isinstance(pre_df,pd.DataFrame) else pd.DataFrame()
    post_df = post_df if isinstance(post_df,pd.DataFrame) else pd.DataFrame()
    pre_years=pd.to_numeric(pre_df.get('publication_year',pd.Series(index=pre_df.index,dtype=float)),errors='coerce')
    post_years=pd.to_numeric(post_df.get('publication_year',pd.Series(index=post_df.index,dtype=float)),errors='coerce')
    pre=pre_df[pre_years.fillna(-1).astype(int)<int(landmark_year)].copy()
    post=post_df[post_years.fillna(-1).astype(int)>int(landmark_year)].copy()
    pre_n=max(len(pre),1); post_n=len(post)
    growth=float((np.tanh((math.log1p(post_n)-math.log1p(pre_n))/2)+1)/2)
    pre_ent=_topic_entropy(pre); post_ent=_topic_entropy(post)
    diffusion=float(np.clip((post_ent-pre_ent+1)/2,0,1))
    pre_norm=_lexical_rate(pre,LEXICONS['normalization']); post_norm=_lexical_rate(post,LEXICONS['normalization'])
    normalization=float(np.clip((np.tanh(5*(post_norm-pre_norm))+1)/2,0,1))
    post_cites=pd.to_numeric(post.get('cited_by_count',pd.Series(dtype=float)),errors='coerce').fillna(0)
    adoption=float(np.tanh(float(post_cites.mean())/50.0)) if len(post_cites) else 0.0
    transformation=float(np.mean([growth,diffusion,normalization,adoption]))
    return {'post_docs':int(post_n),'post_growth':growth,'topic_diffusion':diffusion,'normalization_index':normalization,
            'post_adoption':adoption,'transformation':float(transformation)}


def compute_scores(feature_dict, weights):
    # Structured Knowledge Gap remains a mechanism inside the broader book-wide architecture.
    dg=max(_safe_float(feature_dict.get('density_gap')),1e-9); ba=max(_safe_float(feature_dict.get('boundary_activity')),1e-9); co=max(_safe_float(feature_dict.get('complementarity')),1e-9)
    skg=float((dg*ba*co)**(1/3))
    legacy=sum(float(weights.get(k,0))*float(np.clip(feature_dict.get(k,0.0),0,1)) for k in LEGACY_FEATURES)
    # v4 theory score: equal weight across six book-derived stages, not across raw proxies.
    # This prevents a stage with many proxies from dominating merely because it has more columns.
    stages=['stage_possibility','stage_question','stage_pattern','stage_imagination','stage_insight','stage_discovery_readiness']
    book_score=_geomean01([feature_dict.get(k,0.0) for k in stages])
    return skg,float(legacy),book_score
