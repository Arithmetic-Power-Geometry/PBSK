from __future__ import annotations
import pandas as pd

SCHEMA_COLUMNS = [
    'id','title','abstract','publication_year','cited_by_count',
    'referenced_works_count','topic_ids'
]


def _frame(rows):
    """Return a normalized scholarly-record frame with a stable schema.

    Empty API responses are common for narrow PubMed/OpenAlex windows.  A stable
    schema prevents downstream feature code from failing merely because a provider
    returned zero records.
    """
    df=pd.DataFrame(rows)
    for col in SCHEMA_COLUMNS:
        if col not in df.columns:
            if col=='topic_ids':
                df[col]=pd.Series([[] for _ in range(len(df))],dtype=object)
            elif col in {'cited_by_count','referenced_works_count'}:
                df[col]=pd.Series([0 for _ in range(len(df))],dtype='int64')
            else:
                df[col]=pd.Series([None for _ in range(len(df))],dtype=object)
    return df[SCHEMA_COLUMNS + [c for c in df.columns if c not in SCHEMA_COLUMNS]]


def invert_abstract(inv):
    if not inv: return ''
    pairs=[]
    for word, positions in inv.items():
        for pos in positions: pairs.append((int(pos),word))
    return ' '.join(w for _,w in sorted(pairs))


def openalex_to_frame(records):
    rows=[]
    for w in (records or []):
        topics=[]
        for t in (w.get('topics') or []):
            tid=t.get('id') or t.get('display_name')
            if tid: topics.append(tid)
        rows.append({
            'id':w.get('id'),'title':w.get('title') or w.get('display_name') or '',
            'abstract':invert_abstract(w.get('abstract_inverted_index')),
            'publication_year':w.get('publication_year'),'cited_by_count':w.get('cited_by_count') or 0,
            'referenced_works_count':len(w.get('referenced_works') or []),'topic_ids':topics,
        })
    return _frame(rows)


def pubmed_to_frame(records):
    return _frame(records or [])
