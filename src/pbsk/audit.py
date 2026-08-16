from __future__ import annotations
import pandas as pd

AUDIT_COLUMNS=['source','region_id','offset','cutoff_year','max_publication_year','temporal_lock_pass']


def leakage_audit(features):
    if features is None or not isinstance(features,pd.DataFrame) or features.empty:
        return pd.DataFrame(columns=AUDIT_COLUMNS)
    required={'source','region_id','offset','cutoff_year','max_publication_year'}
    if not required.issubset(features.columns):
        return pd.DataFrame(columns=AUDIT_COLUMNS)
    rows=[]
    for r in features.itertuples(index=False):
        max_year=getattr(r,'max_publication_year',None); cutoff=getattr(r,'cutoff_year',None)
        if pd.isna(cutoff): ok=False
        else: ok=(pd.isna(max_year) or int(max_year)<=int(cutoff))
        rows.append({'source':getattr(r,'source',None),'region_id':getattr(r,'region_id',None),'offset':getattr(r,'offset',None),
                     'cutoff_year':cutoff,'max_publication_year':max_year,'temporal_lock_pass':bool(ok)})
    return pd.DataFrame(rows,columns=AUDIT_COLUMNS)
