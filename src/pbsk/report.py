from __future__ import annotations
from pathlib import Path
import html, json, pandas as pd
from .utils import now_utc


def generate_html(results_dir='results'):
    r=Path(results_dir); tabs=r/'tables'; figs=r/'figures'
    summary={}
    sf=r/'run_summary.json'
    if sf.exists():
        try:summary=json.loads(sf.read_text(encoding='utf-8'))
        except Exception:pass
    sections=[]
    for f in sorted(tabs.glob('*.csv')):
        try:table=pd.read_csv(f).head(300).to_html(index=False,border=0,classes='data')
        except Exception:continue
        sections.append(f'<section><h2>{html.escape(f.stem)}</h2>{table}</section>')
    images=''.join(f'<section><h2>{html.escape(f.stem)}</h2><img src="figures/{f.name}" alt="{html.escape(f.stem)}"></section>' for f in sorted(figs.glob('*.png')))
    stages='Possibility → Question → Anomaly/Doubt → Pattern/Analogy/Collision → Insight → Leap/Discovery → Transformation'
    status=html.escape(str(summary.get('status','RUNNING')))
    doc=f'''<!doctype html><html><head><meta charset="utf-8"><title>PBSK Results</title><style>
body{{font-family:Arial,sans-serif;max-width:1250px;margin:36px auto;padding:0 22px;color:#1f2937;line-height:1.45}}h1,h2{{color:#111827}}.hero{{padding:18px 22px;background:#f5f7fa;border-left:5px solid #111827}}.data{{border-collapse:collapse;width:100%;font-size:12px}}.data th,.data td{{border:1px solid #ddd;padding:5px}}.data th{{background:#f3f4f6;position:sticky;top:0}}img{{max-width:100%;height:auto;border:1px solid #eee}}section{{margin:30px 0;overflow-x:auto}}code{{background:#f3f4f6;padding:2px 4px}}</style></head><body>
<div class="hero"><h1>PBSK — Possibility-to-Breakthrough Structure in Knowledge</h1><p><strong>Status:</strong> {status}</p><p><strong>Book-derived arc:</strong> {stages}</p><p>Conceptual source: Mohammad Amir Khusru Akhtar (Shunya), <em>THE IMPOSSIBLE IDEA: How New Realities Enter the World</em> (2026), https://a.co/d/03buY0qI.</p><p>Generated {now_utc()}.</p></div>
<p>PBSK operationalizes observable scholarly proxies for the book's 40-chapter architecture. Cognitive constructs such as curiosity, doubt, incubation, analogy, and insight are treated as literature-level proxies rather than direct measurements of private mental states. Predictive analyses use pre-landmark data only; post-landmark information is reserved for transformation outcomes.</p>
{images}{''.join(sections)}</body></html>'''
    (r/'PBSK_RESULTS.html').write_text(doc,encoding='utf-8')
