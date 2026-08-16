from __future__ import annotations
from dataclasses import dataclass
from .normalize import openalex_to_frame, pubmed_to_frame

@dataclass
class RegionSpec:
    region_id:str
    match_case_id:str
    label:str
    query:str
    domain:str
    landmark_year:int
    target:int
    book_realm:str='Unassigned'
    topic_id:str=''
    cohort:str='landmark'


def _realm(domain):
    d=str(domain).lower()
    if 'physical' in d or 'earth' in d or 'environment' in d or 'natural' in d: return 'Nature'
    if 'life' in d or 'health' in d or 'bio' in d or 'medicine' in d: return 'Life'
    if 'psych' in d or 'cogn' in d or 'neuro' in d: return 'Minds'
    if 'social' in d or 'human' in d or 'culture' in d: return 'Cultures'
    if 'computer' in d or 'engineering' in d or 'machine' in d or 'technology' in d: return 'Machines'
    return 'Unassigned'


def region_specs(cases, controls):
    rows=[]
    for r in cases.itertuples(index=False):
        realm=getattr(r,'book_realm',None) or _realm(r.domain)
        rows.append(RegionSpec(r.case_id,r.case_id,r.label,r.query,r.domain,int(r.landmark_year),1,realm,getattr(r,'topic_id','') or '',getattr(r,'cohort','landmark') or 'landmark'))
    for c in controls.itertuples(index=False):
        case=cases.loc[cases.case_id==c.match_case_id].iloc[0]
        realm=getattr(c,'book_realm',None) or getattr(case,'book_realm',None) or _realm(c.domain)
        rows.append(RegionSpec(c.control_id,c.match_case_id,c.label,c.query,c.domain,int(case.landmark_year),0,realm,getattr(c,'topic_id','') or '',getattr(c,'cohort','landmark') or 'landmark'))
    return rows


def retrieve_openalex_window(client, spec, start_year, end_year, max_records, per_year_cap=100):
    rec=client.get_works_balanced(search=None if spec.topic_id else spec.query,topic_id=spec.topic_id or None,
                                  start_year=int(start_year),end_year=int(end_year),max_records=max_records,per_year_cap=per_year_cap)
    return openalex_to_frame(rec)


def retrieve_pubmed_window(client, spec, start_year, end_year, max_records):
    ids=client.search(spec.query,int(start_year),int(end_year),retmax=max_records)
    return pubmed_to_frame(client.fetch(ids))
