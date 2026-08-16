import numpy as np, pandas as pd
from pbsk.modeling import evaluate_models, ablation_table, BASE, LEGACY, BOOK, temporal_holdout_table


def synthetic_rows():
    rng=np.random.default_rng(2); rows=[]
    for g in range(14):
        for j,target in enumerate([1,0,0]):
            for off in [5,3,1]:
                val=.34+.20*target+.025*(5-off)/2+rng.normal(0,.035)
                row={'region_id':f'{g}-{j}-{off}','match_case_id':f'C{g}','offset':off,'target':target,'book_realm':['Nature','Life','Machines'][g%3],
                     'pbs':np.clip(val,0,1),'skg':np.clip(val-.04,0,1),'bookwide_pbsk':np.clip(val+.02,0,1)}
                for f in set(BASE+LEGACY+BOOK): row.setdefault(f,float(np.clip(val+rng.normal(0,.05),0,1)))
                row['n_docs']=50+10*target+rng.integers(0,20); row['mean_citations']=5+2*target+rng.random(); row['activity_recent']=20+4*target+rng.integers(0,5); row['activity_prior']=15+rng.integers(0,5)
                rows.append(row)
    return pd.DataFrame(rows)


def test_models_run():
    perf,p=evaluate_models(synthetic_rows()); assert len(perf)>=6; assert perf.roc_auc.between(0,1).all(); assert not p.empty


def test_ablation_runs():
    a=ablation_table(synthetic_rows()); assert 'none' in set(a.removed_component); assert a.roc_auc.between(0,1).all()


def test_temporal_models_run():
    t=temporal_holdout_table(synthetic_rows()); assert set(t.offset)=={1,3,5}; assert t.roc_auc.between(0,1).all()


def test_evaluate_models_empty_frame_does_not_crash():
    import pandas as pd
    perf,preds=evaluate_models(pd.DataFrame())
    assert perf.empty and preds.empty

def test_evaluate_models_missing_labels_does_not_crash():
    import pandas as pd
    df=pd.DataFrame({'region_id':['x'],'offset':[1],'bookwide_pbsk':[0.5]})
    perf,preds=evaluate_models(df)
    assert perf.empty and preds.empty
