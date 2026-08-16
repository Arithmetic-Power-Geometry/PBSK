from __future__ import annotations
import argparse, json
from .smoke import run_smoke
from .experiment import run_full


def main():
    p=argparse.ArgumentParser(prog='pbsk',description='PBSK reproducible research pipeline')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ['smoke','full']:
        q=sub.add_parser(name); q.add_argument('--config',default='config/default.yaml')
    sub.add_parser('test')
    a=p.parse_args()
    if a.command=='smoke': print(json.dumps(run_smoke(a.config),indent=2)); return 0
    if a.command=='full': print(json.dumps(run_full(a.config),indent=2)); return 0
    if a.command=='test':
        import pytest; return pytest.main(['-q'])
    return 2

if __name__=='__main__': raise SystemExit(main())
