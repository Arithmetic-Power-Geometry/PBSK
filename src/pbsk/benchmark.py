from __future__ import annotations
from pathlib import Path
import pandas as pd

REQUIRED_CASE={'case_id','label','query','domain','landmark_year','doi','pmid'}
REQUIRED_CTRL={'control_id','match_case_id','label','query','domain'}


def load_cases(path='data/landmark_benchmark.csv'):
    df=pd.read_csv(path, dtype={'pmid':'string'})
    miss=REQUIRED_CASE-set(df.columns)
    if miss: raise ValueError(f'Missing case columns: {sorted(miss)}')
    if not df.case_id.is_unique: raise ValueError('case_id must be unique')
    if df.landmark_year.isna().any(): raise ValueError('landmark_year may not be missing')
    return df


def load_controls(path='data/matched_controls.csv'):
    df=pd.read_csv(path)
    miss=REQUIRED_CTRL-set(df.columns)
    if miss: raise ValueError(f'Missing control columns: {sorted(miss)}')
    if not df.control_id.is_unique: raise ValueError('control_id must be unique')
    return df


def validate_matching(cases, controls):
    ids=set(cases.case_id)
    bad=sorted(set(controls.match_case_id)-ids)
    if bad: raise ValueError(f'Controls reference unknown cases: {bad}')
    merged=controls.merge(cases[['case_id','domain']], left_on='match_case_id', right_on='case_id', suffixes=('_ctrl','_case'))
    mismatch=merged[merged.domain_ctrl != merged.domain_case]
    if not mismatch.empty:
        raise ValueError('Control domains must match case domains')
    return True
