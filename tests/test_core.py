import pandas as pd, numpy as np
from pbsk.features import normalized_entropy, compute_region_features, compute_scores, compute_transformation_features, BOOK_FEATURES
from pbsk.smoke import synthetic_frame
from pbsk.config import load_config
from pbsk.benchmark import load_cases, load_controls, validate_matching


def test_entropy_bounds():
    assert normalized_entropy([10,0,0]) == 0
    assert .99 <= normalized_entropy([1,1,1,1]) <= 1.01


def test_book_feature_bounds():
    cfg=load_config(); f=compute_region_features(synthetic_frame(),2019,{**cfg['analysis'],'min_documents_for_semantics':12})
    for k in BOOK_FEATURES:
        assert 0 <= f[k] <= 1, (k,f[k])
    skg,pbs,bwide=compute_scores(f,cfg['analysis']['fixed_pbs_weights'])
    assert 0 <= skg <= 1 and 0 <= pbs <= 1 and 0 <= bwide <= 1


def test_temporal_filter_changes_n():
    cfg=load_config(); d=synthetic_frame(); a=compute_region_features(d,2014,{**cfg['analysis'],'min_documents_for_semantics':12}); b=compute_region_features(d,2019,{**cfg['analysis'],'min_documents_for_semantics':12})
    assert a['n_docs'] <= b['n_docs']


def test_transformation_bounds():
    t=compute_transformation_features(synthetic_frame(),synthetic_frame(19,80,2021,2025),2020)
    for k in ['post_growth','topic_diffusion','normalization_index','post_adoption','transformation']:
        assert 0 <= t[k] <= 1


def test_benchmark_matching_and_realms():
    c=load_cases(); k=load_controls(); assert validate_matching(c,k); assert len(k)>=len(c); assert 'book_realm' in c.columns and 'book_realm' in k.columns


def test_40_chapter_map_exists():
    d=pd.read_csv('data/book_operationalization.csv'); assert len(d)==40; assert set(d.chapter)==set(range(1,41))


def test_transformation_empty_frames_do_not_crash():
    t=compute_transformation_features(pd.DataFrame(),pd.DataFrame(),2020)
    assert t['post_docs']==0
    for k in ['post_growth','topic_diffusion','normalization_index','post_adoption','transformation']:
        assert 0 <= t[k] <= 1


def test_transformation_partial_schema_does_not_crash():
    pre=pd.DataFrame({'title':['a']})
    post=pd.DataFrame({'title':['b']})
    t=compute_transformation_features(pre,post,2020)
    assert t['post_docs']==0


def test_normalizers_keep_schema_on_empty_provider_response():
    from pbsk.normalize import openalex_to_frame, pubmed_to_frame, SCHEMA_COLUMNS
    for frame in [openalex_to_frame([]),pubmed_to_frame([])]:
        assert list(frame.columns[:len(SCHEMA_COLUMNS)]) == SCHEMA_COLUMNS
        assert frame.empty


def test_restore_labels_repairs_live_feature_metadata():
    import pandas as pd
    from pbsk.experiment import _restore_labels
    from pbsk.retrieval import RegionSpec
    specs=[RegionSpec('r1','case1','Case 1','query','Life',2010,1,'Life')]
    df=pd.DataFrame({'source':['OpenAlex'],'region_id':['r1'],'offset':[1],'bookwide_pbsk':[0.7]})
    out=_restore_labels(df,specs)
    assert out.loc[0,'target']==1
    assert out.loc[0,'match_case_id']=='case1'


def test_replication_plot_handles_live_frames(tmp_path):
    from pbsk.plots import replication
    oa=pd.DataFrame({
        'offset':[1,1,1,1], 'match_case_id':['c1','c1','c2','c2'], 'target':[1,0,1,0],
        'bookwide_pbsk':[.8,.4,.7,.35]})
    pm=pd.DataFrame({
        'offset':[1,1,1,1], 'match_case_id':['c1','c1','c2','c2'], 'target':[1,0,1,0],
        'bookwide_pbsk':[.75,.45,.72,.30]})
    path=tmp_path/'replication.png'
    assert replication(oa,pm,path) is True
    assert path.exists()


def test_replication_plot_missing_metric_is_skipped(tmp_path):
    from pbsk.plots import replication
    oa=pd.DataFrame({'offset':[1], 'match_case_id':['c1'], 'target':[1]})
    pm=pd.DataFrame({'offset':[1], 'match_case_id':['c1'], 'target':[1]})
    assert replication(oa,pm,tmp_path/'x.png') is False


def test_zero_difference_statistics_are_stable():
    from pbsk.statistics import hypothesis_table
    rows=[]
    for g in ['a','b','c','d']:
        for target in [1,0]:
            rows.append({'offset':1,'target':target,'match_case_id':g,'bookwide_pbsk':.5})
    out=hypothesis_table(pd.DataFrame(rows),permutation_iterations=50,seed=1)
    assert not out.empty
    r=out[out.metric=='bookwide_pbsk'].iloc[0]
    assert r.wilcoxon_one_sided_p == 1.0
    assert r.permutation_one_sided_p == 1.0


def test_all_plot_functions_sparse_frames_do_not_crash(tmp_path):
    from pbsk import plots
    empty=pd.DataFrame()
    funcs=[
        lambda: plots.temporal_score(empty,tmp_path/'a.png'),
        lambda: plots.stage_profile(empty,tmp_path/'b.png'),
        lambda: plots.distribution(empty,tmp_path/'c.png'),
        lambda: plots.model_performance(empty,tmp_path/'d.png'),
        lambda: plots.temporal_performance(empty,tmp_path/'e.png'),
        lambda: plots.ablation(empty,tmp_path/'f.png'),
        lambda: plots.transformation(empty,tmp_path/'g.png'),
        lambda: plots.sequence_plot(empty,tmp_path/'h.png'),
        lambda: plots.replication(empty,empty,tmp_path/'i.png'),
        lambda: plots.realm_profile(empty,tmp_path/'j.png'),
        lambda: plots.retrieval_qc(empty,tmp_path/'k.png'),
    ]
    assert all(f() is False for f in funcs)


def test_quality_gate_excludes_tiny_corpus():
    cfg=load_config(); d=synthetic_frame(1,8,2010,2012)
    f=compute_region_features(d,2012,{**cfg['analysis'],'min_documents_for_semantics':5,'min_documents_for_inference':60,'min_years_covered_for_inference':5})
    assert f['quality_eligible']==0


def test_stage_weighted_book_score_bounds():
    cfg=load_config(); f=compute_region_features(synthetic_frame(),2019,{**cfg['analysis'],'min_documents_for_semantics':12,'min_documents_for_inference':10,'min_years_covered_for_inference':2})
    skg,pbs,b=compute_scores(f,cfg['analysis']['fixed_pbs_weights'])
    assert 0 <= b <= 1
    assert all(k in f for k in ['stage_possibility','stage_question','stage_pattern','stage_imagination','stage_insight','stage_discovery_readiness','core_geometry_score'])


def test_power_cohort_is_future_outcome_defined_without_predictor_use():
    from pbsk.power_validation import build_power_cohort
    class Fake:
        def sample_topics(self,n,minimum_works):
            domains=['Life Sciences','Physical Sciences','Computer Science']
            return [{'id':f'https://openalex.org/T{i}','display_name':f'Topic {i}','domain':{'display_name':domains[i%3]},'field':{'display_name':'F'},'works_count':5000} for i in range(80)]
        def topic_year_counts(self,tid,start,end):
            i=int(tid.split('T')[-1]); out={}
            for y in range(start,end+1):
                out[str(y)]=10 if y<=2018 else (10 + (i%20)*3)
            return out
    cfg=load_config(); cfg['power_validation']['target_positive_topics']=12; cfg['power_validation']['controls_per_positive']=2; cfg['power_validation']['minimum_pre_count']=20
    p,c,s=build_power_cohort(Fake(),cfg)
    assert len(p)==12 and len(c)>=12 and len(s)>=24
    assert set(x.cohort for x in s)=={'power_validation'}
