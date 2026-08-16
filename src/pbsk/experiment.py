from __future__ import annotations
from pathlib import Path
import shutil, warnings
import numpy as np, pandas as pd
from .config import load_config
from .benchmark import load_cases, load_controls, validate_matching
from .openalex import OpenAlexClient
from .pubmed import PubMedClient
from .retrieval import region_specs, retrieve_openalex_window, retrieve_pubmed_window
from .features import compute_region_features, compute_scores, compute_transformation_features
from .statistics import hypothesis_table, transformation_test, sequence_test
from .modeling import evaluate_models, ablation_table, temporal_holdout_table, realm_generalization, incremental_value_table
from .power_validation import build_power_cohort
from .audit import leakage_audit
from .plots import (benchmark_timeline, temporal_score, stage_profile, distribution, model_performance,
                    temporal_performance, ablation, transformation, sequence_plot, replication, realm_profile, retrieval_qc)
from .report import generate_html
from .utils import ensure, set_seed, write_json, now_utc

LIFE_REALMS={'Life'}
FEATURE_META_COLUMNS=['source','cohort','region_id','match_case_id','label','target','domain','book_realm','landmark_year','offset','cutoff_year','max_publication_year']
TRANSFORM_META_COLUMNS=['source','cohort','region_id','match_case_id','label','target','domain','book_realm','landmark_year']
QC_COLUMNS=['source','cohort','region_id','match_case_id','target','book_realm','window','start_year','end_year','records','status','message']


def _stable_frame(rows, columns):
    df=pd.DataFrame(rows)
    for c in columns:
        if c not in df.columns:df[c]=pd.Series(dtype='object')
    return df


def _restore_labels(df,specs):
    if df is None or df.empty:return _stable_frame([],FEATURE_META_COLUMNS)
    meta=pd.DataFrame([{'region_id':s.region_id,'match_case_id':s.match_case_id,'label':s.label,'target':int(s.target),
                       'domain':s.domain,'book_realm':s.book_realm,'landmark_year':int(s.landmark_year),'cohort':s.cohort} for s in specs]).drop_duplicates('region_id')
    for c in ['match_case_id','label','target','domain','book_realm','landmark_year','cohort']:
        if c in df.columns:df=df.drop(columns=[c])
    df=df.merge(meta,on='region_id',how='left',validate='many_to_one')
    missing=df[['match_case_id','target']].isna().any(axis=1)
    if missing.any():raise ValueError(f'Feature rows could not be linked to benchmark labels: {sorted(df.loc[missing,"region_id"].astype(str).unique())[:10]}')
    df['target']=pd.to_numeric(df.target,errors='raise').astype(int)
    return df


def _model_contract(df):
    required=['region_id','match_case_id','target','offset']; missing=[c for c in required if c not in df.columns]
    d=df.copy()
    if 'quality_eligible' in d.columns:d=d[pd.to_numeric(d.quality_eligible,errors='coerce').fillna(0).astype(int)==1]
    classes=sorted(pd.to_numeric(d.target,errors='coerce').dropna().astype(int).unique().tolist()) if 'target' in d else []
    groups=int(d.match_case_id.dropna().astype(str).nunique()) if 'match_case_id' in d else 0
    return {'ready':bool(not missing and not d.empty and len(classes)>=2 and groups>=2),'missing_columns':missing,
            'rows_all':int(len(df)),'rows_eligible':int(len(d)),'classes':classes,'matched_groups':groups}


def _concat_frames(*frames):
    usable=[f for f in frames if isinstance(f,pd.DataFrame) and not f.empty]
    if not usable:return pd.DataFrame()
    if len(usable)==1:return usable[0].copy()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',FutureWarning); return pd.concat(usable,ignore_index=True,sort=False)


def _safe_plot(name,fn,*args,**kwargs):
    try:
        made=bool(fn(*args,**kwargs)); return {'figure':name,'status':'OK' if made else 'SKIPPED','message':''}
    except Exception as e:return {'figure':name,'status':'ERROR','message':f'{type(e).__name__}: {str(e)[:300]}'}


def _retrieve_and_measure(specs,source,retriever,cfg,maxrec=None,per_year_cap=None):
    rows=[]; transforms=[]; qc=[]; exp=cfg['experiment']
    ana={**cfg['analysis'],'min_documents_for_semantics':exp.get('min_documents_for_semantics',20),
         'min_documents_for_inference':exp.get('min_documents_for_inference',60),'min_years_covered_for_inference':exp.get('min_years_covered_for_inference',5)}
    lookback=int(exp['lookback_years']); post_years=int(exp.get('post_landmark_years',10)); maxrec=int(maxrec or exp['max_records_per_region_window'])
    current=int(exp.get('current_year',2026)); per_year_cap=int(per_year_cap or exp.get('balanced_records_per_year',100))
    for s in specs:
        pre_start=max(int(exp.get('minimum_year',1950)),s.landmark_year-lookback); pre_end=s.landmark_year-1
        post_start=s.landmark_year+1; post_end=min(current,s.landmark_year+post_years)
        try:
            pre=retriever(s,pre_start,pre_end,maxrec,per_year_cap)
            qc.append({'source':source,'cohort':s.cohort,'region_id':s.region_id,'match_case_id':s.match_case_id,'target':s.target,'book_realm':s.book_realm,
                       'window':'pre','start_year':pre_start,'end_year':pre_end,'records':len(pre),'status':'OK','message':''})
        except Exception as e:
            pre=pd.DataFrame(); qc.append({'source':source,'cohort':s.cohort,'region_id':s.region_id,'match_case_id':s.match_case_id,'target':s.target,'book_realm':s.book_realm,
                       'window':'pre','start_year':pre_start,'end_year':pre_end,'records':0,'status':'ERROR','message':str(e)[:300]})
        try:
            if post_start<=post_end:
                post=retriever(s,post_start,post_end,maxrec,per_year_cap)
                status='OK'; msg=''
            else:
                post=pd.DataFrame(); status='SKIPPED'; msg='No completed post-landmark years available at current_year cutoff.'
            qc.append({'source':source,'cohort':s.cohort,'region_id':s.region_id,'match_case_id':s.match_case_id,'target':s.target,'book_realm':s.book_realm,
                       'window':'post','start_year':post_start,'end_year':post_end,'records':len(post),'status':status,'message':msg})
        except Exception as e:
            post=pd.DataFrame(); qc.append({'source':source,'cohort':s.cohort,'region_id':s.region_id,'match_case_id':s.match_case_id,'target':s.target,'book_realm':s.book_realm,
                       'window':'post','start_year':post_start,'end_year':post_end,'records':0,'status':'ERROR','message':str(e)[:300]})
        if not pre.empty:
            for offset in exp['offsets']:
                cutoff=s.landmark_year-int(offset); f=compute_region_features(pre,cutoff,ana); skg,pbs,bwide=compute_scores(f,cfg['analysis']['fixed_pbs_weights'])
                pre_years=pd.to_numeric(pre.get('publication_year',pd.Series(index=pre.index,dtype=float)),errors='coerce'); used=pre[pre_years.fillna(9999).astype(int)<=cutoff]
                rows.append({'source':source,'cohort':s.cohort,'region_id':s.region_id,'match_case_id':s.match_case_id,'label':s.label,'target':s.target,
                             'domain':s.domain,'book_realm':s.book_realm,'landmark_year':s.landmark_year,'offset':int(offset),'cutoff_year':cutoff,
                             'max_publication_year':pd.to_numeric(used.get('publication_year',pd.Series(index=used.index,dtype=float)),errors='coerce').max() if not used.empty else np.nan,
                             **f,'skg':skg,'pbs':pbs,'bookwide_pbsk':bwide})
        if not pre.empty or not post.empty:
            tf=compute_transformation_features(pre,post,s.landmark_year)
            transforms.append({'source':source,'cohort':s.cohort,'region_id':s.region_id,'match_case_id':s.match_case_id,'label':s.label,'target':s.target,
                               'domain':s.domain,'book_realm':s.book_realm,'landmark_year':s.landmark_year,**tf})
    return _stable_frame(rows,FEATURE_META_COLUMNS),_stable_frame(transforms,TRANSFORM_META_COLUMNS),_stable_frame(qc,QC_COLUMNS)


def _cross_source_table(oa,pm):
    if oa.empty or pm.empty:return pd.DataFrame()
    metrics=['bookwide_pbsk','core_geometry_score','skg','possibility_pressure','question_pressure','collision_index','insight_coherence','sequence_order_score']
    rows=[]
    for metric in metrics:
        if metric not in oa or metric not in pm:continue
        a=oa[oa.offset==1].groupby(['match_case_id','target'])[metric].mean().rename('oa'); p=pm[pm.offset==1].groupby(['match_case_id','target'])[metric].mean().rename('pm')
        m=pd.concat([a,p],axis=1).dropna()
        if len(m)>=3:rows.append({'metric':metric,'n':len(m),'pearson_r':m.oa.corr(m.pm),'spearman_rho':m.oa.corr(m.pm,method='spearman'),'mean_abs_difference':float(np.mean(np.abs(m.oa-m.pm)))})
    return pd.DataFrame(rows)


def run_full(config_path='config/default.yaml'):
    cfg=load_config(config_path); set_seed(int(cfg['experiment']['random_seed']))
    out=ensure('results'); tabs=ensure(out/'tables'); figs=ensure(out/'figures')
    cases=load_cases(); ctrls=load_controls(); validate_matching(cases,ctrls); specs=region_specs(cases,ctrls)
    bop=Path('data/book_operationalization.csv')
    if bop.exists():shutil.copy2(bop,tabs/'table_book_operationalization.csv')

    oa=OpenAlexClient(cfg['openalex'])
    oa_retr=lambda s,a,b,n,py:retrieve_openalex_window(oa,s,a,b,n,py)
    oa_features,oa_transform,oa_qc=_retrieve_and_measure(specs,'OpenAlex',oa_retr,cfg)
    oa_features=_restore_labels(oa_features,specs)

    pm=PubMedClient(cfg['pubmed']); pm_specs=[s for s in specs if s.book_realm in LIFE_REALMS]
    pm_retr=lambda s,a,b,n,py:retrieve_pubmed_window(pm,s,a,b,n)
    pm_features,pm_transform,pm_qc=_retrieve_and_measure(pm_specs,'PubMed',pm_retr,cfg) if pm_specs else (_stable_frame([],FEATURE_META_COLUMNS),_stable_frame([],TRANSFORM_META_COLUMNS),_stable_frame([],QC_COLUMNS))
    pm_features=_restore_labels(pm_features,pm_specs) if pm_specs else pm_features

    # Independent high-powered prospective topic cohort. Outcome labels use only post-cutoff growth;
    # all PBSK predictors are computed strictly before the cutoff.
    pv_pos=pv_ctrl=pd.DataFrame(); pv_specs=[]; pv_features=pv_transform=pv_qc=pd.DataFrame(); pv_pm_features=pd.DataFrame(); pv_pm_qc=pd.DataFrame()
    if bool(cfg.get('power_validation',{}).get('enabled',False)):
        pv_pos,pv_ctrl,pv_specs=build_power_cohort(oa,cfg)
        if pv_specs:
            pcfg=cfg['power_validation']
            pv_features,pv_transform,pv_qc=_retrieve_and_measure(pv_specs,'OpenAlex',oa_retr,cfg,maxrec=int(pcfg['max_records_per_topic_window']),per_year_cap=int(pcfg['balanced_records_per_year']))
            pv_features=_restore_labels(pv_features,pv_specs)
            life=[s for s in pv_specs if s.book_realm=='Life']
            if life:
                pv_pm_features,_,pv_pm_qc=_retrieve_and_measure(life,'PubMed',pm_retr,cfg,maxrec=int(pcfg['replication_pubmed_max_records']),per_year_cap=int(pcfg['balanced_records_per_year']))
                pv_pm_features=_restore_labels(pv_pm_features,life)
        pv_pos.to_csv(tabs/'table_power_validation_positive_topics.csv',index=False); pv_ctrl.to_csv(tabs/'table_power_validation_controls.csv',index=False)

    allf=_concat_frames(oa_features,pm_features,pv_features,pv_pm_features); allt=_concat_frames(oa_transform,pm_transform,pv_transform); qc=_concat_frames(oa_qc,pm_qc,pv_qc,pv_pm_qc)
    allf.to_csv(tabs/'table_region_features_all_sources.csv',index=False); oa_features.to_csv(tabs/'table_openalex_bookwide_features.csv',index=False)
    if not pm_features.empty:pm_features.to_csv(tabs/'table_pubmed_bookwide_features.csv',index=False)
    if not pv_features.empty:pv_features.to_csv(tabs/'table_power_validation_features_openalex.csv',index=False)
    if not pv_pm_features.empty:pv_pm_features.to_csv(tabs/'table_power_validation_features_pubmed.csv',index=False)
    allt.to_csv(tabs/'table_transformation_outcomes.csv',index=False); qc.to_csv(tabs/'table_retrieval_qc.csv',index=False); cases.to_csv(tabs/'table_landmark_benchmark.csv',index=False); ctrls.to_csv(tabs/'table_matched_controls.csv',index=False)

    # Landmark analysis remains transparent/exploratory after v3 inspection.
    h=hypothesis_table(oa_features,cfg['experiment']['permutation_iterations'],cfg['experiment']['random_seed'],'landmark_exploratory'); h.to_csv(tabs/'table_hypothesis_tests_openalex.csv',index=False)
    seq=sequence_test(oa_features); seq.to_csv(tabs/'table_sequence_architecture.csv',index=False)
    tr=transformation_test(oa_transform,cfg['experiment']['permutation_iterations'],cfg['experiment']['random_seed']); tr.to_csv(tabs/'table_transformation_tests_openalex.csv',index=False)
    contract=_model_contract(oa_features); write_json(out/'modeling_contract.json',contract)
    perf,preds=evaluate_models(oa_features,cfg['experiment']['bootstrap_iterations']) if contract['ready'] else (pd.DataFrame(),pd.DataFrame())
    perf.to_csv(tabs/'table_predictive_performance_openalex.csv',index=False); preds.to_csv(tabs/'table_oof_predictions_openalex.csv',index=False)
    incremental_value_table(preds).to_csv(tabs/'table_incremental_value_openalex.csv',index=False)
    temp=temporal_holdout_table(oa_features) if contract['ready'] else pd.DataFrame(); temp.to_csv(tabs/'table_temporal_predictive_performance.csv',index=False)
    abl=ablation_table(oa_features) if contract['ready'] else pd.DataFrame(); abl.to_csv(tabs/'table_ablation_openalex.csv',index=False)
    realm_generalization(preds).to_csv(tabs/'table_creative_universe_generalization.csv',index=False)

    # Independent v4 validation: this is the confirmatory home for v3-derived core_geometry_score.
    pv_h=pv_perf=pv_preds=pv_inc=pd.DataFrame(); pv_contract={'ready':False}
    if not pv_features.empty:
        pv_h=hypothesis_table(pv_features,cfg['experiment']['permutation_iterations'],cfg['experiment']['random_seed']+101,'power_validation_confirmatory'); pv_h.to_csv(tabs/'table_power_validation_hypotheses.csv',index=False)
        pv_contract=_model_contract(pv_features); write_json(out/'power_validation_modeling_contract.json',pv_contract)
        if pv_contract['ready']:
            pv_perf,pv_preds=evaluate_models(pv_features,cfg['experiment']['bootstrap_iterations']); pv_perf.to_csv(tabs/'table_power_validation_predictive_performance.csv',index=False)
            pv_preds.to_csv(tabs/'table_power_validation_oof_predictions.csv',index=False); pv_inc=incremental_value_table(pv_preds); pv_inc.to_csv(tabs/'table_power_validation_incremental_value.csv',index=False)
            temporal_holdout_table(pv_features).to_csv(tabs/'table_power_validation_temporal_performance.csv',index=False)
            ablation_table(pv_features).to_csv(tabs/'table_power_validation_ablation.csv',index=False)

    audit=leakage_audit(allf); audit.to_csv(tabs/'table_temporal_leakage_audit.csv',index=False)
    pmh=pmt=cross=pd.DataFrame()
    if not pm_features.empty:
        pmh=hypothesis_table(pm_features,cfg['experiment']['permutation_iterations'],cfg['experiment']['random_seed'],'pubmed_landmark_replication'); pmh.to_csv(tabs/'table_pubmed_replication_hypotheses.csv',index=False)
        pmt=transformation_test(pm_transform,cfg['experiment']['permutation_iterations'],cfg['experiment']['random_seed']); pmt.to_csv(tabs/'table_pubmed_replication_transformation.csv',index=False)
        cross=_cross_source_table(oa_features,pm_features); cross.to_csv(tabs/'table_cross_source_agreement.csv',index=False)
    if not pv_pm_features.empty:
        hypothesis_table(pv_pm_features,cfg['experiment']['permutation_iterations'],cfg['experiment']['random_seed']+202,'pubmed_power_replication').to_csv(tabs/'table_power_validation_pubmed_replication.csv',index=False)
        _cross_source_table(pv_features,pv_pm_features).to_csv(tabs/'table_power_validation_cross_source_agreement.csv',index=False)

    plot_rows=[
      _safe_plot('figure_01_benchmark_timeline',benchmark_timeline,cases,figs/'figure_01_benchmark_timeline.png'),
      _safe_plot('figure_02_bookwide_pbsk_trajectory',temporal_score,oa_features,figs/'figure_02_bookwide_pbsk_trajectory.png','bookwide_pbsk','OpenAlex'),
      _safe_plot('figure_03_book_stage_profile_tminus1',stage_profile,oa_features,figs/'figure_03_book_stage_profile_tminus1.png','OpenAlex',1),
      _safe_plot('figure_04_bookwide_pbsk_distribution',distribution,oa_features,figs/'figure_04_bookwide_pbsk_distribution.png','bookwide_pbsk','OpenAlex',1),
      _safe_plot('figure_05_sequence_architecture',sequence_plot,seq,figs/'figure_05_sequence_architecture.png'),
      _safe_plot('figure_06_predictive_performance',model_performance,perf,figs/'figure_06_predictive_performance.png'),
      _safe_plot('figure_07_temporal_prediction',temporal_performance,temp,figs/'figure_07_temporal_prediction.png'),
      _safe_plot('figure_08_bookwide_ablation',ablation,abl,figs/'figure_08_bookwide_ablation.png'),
      _safe_plot('figure_09_transformation',transformation,oa_transform,figs/'figure_09_transformation.png'),
      _safe_plot('figure_10_creative_universe_realms',realm_profile,oa_features,figs/'figure_10_creative_universe_realms.png'),
      _safe_plot('figure_11_pubmed_replication',replication,oa_features,pm_features,figs/'figure_11_pubmed_replication.png') if not pm_features.empty else {'figure':'figure_11_pubmed_replication','status':'SKIPPED','message':'No PubMed feature rows'},
      _safe_plot('figure_12_retrieval_qc',retrieval_qc,qc,figs/'figure_12_retrieval_qc.png')]
    if not pv_features.empty:
        plot_rows += [
          _safe_plot('figure_13_power_validation_core_trajectory',temporal_score,pv_features,figs/'figure_13_power_validation_core_trajectory.png','core_geometry_score','OpenAlex power validation'),
          _safe_plot('figure_14_power_validation_performance',model_performance,pv_perf,figs/'figure_14_power_validation_performance.png')]
    pd.DataFrame(plot_rows).to_csv(tabs/'table_figure_generation_qc.csv',index=False)

    temporal_ok=bool(audit.temporal_lock_pass.all()) if not audit.empty else False
    retrieval_ok=bool((oa_qc[oa_qc.window=='pre'].status=='OK').all()) if not oa_qc.empty else False
    quality_pairs=int(oa_features[oa_features.get('quality_eligible',0)==1].match_case_id.nunique()) if not oa_features.empty and 'quality_eligible' in oa_features else 0
    power_required=bool(cfg.get('power_validation',{}).get('enabled',False))
    power_min=int(cfg.get('power_validation',{}).get('minimum_required_positive_topics',0))
    power_ok=(not power_required) or (len(pv_pos)>=power_min and bool(pv_contract.get('ready',False)))
    summary={'status':'PASS' if (not oa_features.empty and temporal_ok and retrieval_ok and power_ok) else 'FAIL','generated_utc':now_utc(),'software_version':cfg['project']['version'],
      'repository':cfg['project']['repository'],'license':'Apache-2.0','conceptual_source':cfg['project']['conceptual_source'],
      'book_arc':'Possibility -> Question -> Pattern -> Imagination -> Insight -> Discovery -> Transformation','book_chapters_operationalized':40,
      'benchmark_cases':int(len(cases)),'matched_controls':int(len(ctrls)),'landmark_quality_matched_groups':quality_pairs,
      'openalex_feature_rows':int(len(oa_features)),'pubmed_feature_rows':int(len(pm_features)),'temporal_lock_pass':temporal_ok,'modeling_ready':bool(contract['ready']),
      'power_validation_enabled':bool(cfg['power_validation']['enabled']),'power_validation_positive_topics':int(len(pv_pos)),'power_validation_controls':int(len(pv_ctrl)),
      'power_validation_feature_rows':int(len(pv_features)),'power_validation_modeling_ready':bool(pv_contract.get('ready',False)),'power_validation_minimum_required_positives':power_min,'power_validation_integrity_pass':bool(power_ok),
      'openalex_models_evaluated':int(len(perf)),'power_validation_models_evaluated':int(len(pv_perf)),'openalex_hypothesis_tests':int(len(h)),
      'power_validation_hypothesis_tests':int(len(pv_h)),'pubmed_replication_tests':int(len(pmh)),'figures_generated':len(list(figs.glob('*.png'))),
      'figure_errors':int(sum(r['status']=='ERROR' for r in plot_rows)),'tables_generated':len(list(tabs.glob('*.csv'))),
      'scientific_guardrail':'v4 does not tune the book theory to the v3 landmark outcomes. The v3-derived core geometry score is explicitly labeled exploratory on landmarks and confirmatory only in the independent post-cutoff topic-validation cohort. Low-coverage regions are excluded from inference by pre-specified quality rules.'}
    write_json(out/'run_summary.json',summary); generate_html(out); return summary
