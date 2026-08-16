from __future__ import annotations
from pathlib import Path
import datetime as dt, hashlib, json, os, random, time
import numpy as np


def ensure(path):
    p=Path(path); p.mkdir(parents=True, exist_ok=True); return p


def stable_key(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:24]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path, payload):
    p=Path(path); ensure(p.parent); p.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding='utf-8')


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def set_seed(seed:int):
    random.seed(seed); np.random.seed(seed)


def env_flag(name, default=False):
    v=os.getenv(name)
    if v is None: return default
    return v.strip().lower() in {'1','true','yes','on'}


def backoff_sleep(attempt:int, base:float=.5, cap:float=20.0):
    time.sleep(min(cap, base*(2**attempt)))
