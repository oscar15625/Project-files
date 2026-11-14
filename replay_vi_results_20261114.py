"""Portable saved-state replay; no solver, external cloud folders, or Windows API."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parent
P=ROOT/'results/vi_cloud_20261114'
sys.path.insert(0,str(P/'sources'))
import numpy as np
from src.model import Model
from nested_extension import NestedModel
def main():
    checks=[]
    for p in sorted((P/'runs').glob('*/metrics.json')):
        r=json.loads(p.read_text(encoding='utf-8'));cfg=r['model_config'];m=NestedModel(**cfg) if 'nest_lambda' in cfg else Model(**cfg)
        y=np.load(p.parent/'state.npy',allow_pickle=False);x=np.load(p.parent/'coordinates.npy',allow_pickle=False);h,v=m.evaluate(y)
        err=max(abs(v[k]-r[k]) for k in v);assert err<1e-6
        direct=float(np.linalg.norm(y-m.project(y-1e-4*h)));h[:m.nt][m.congest]=m.cap[m.congest]*x[:m.nt][m.congest]-m.last_flows[m.congest]
        aux=float(np.linalg.norm(y-m.project(y-1e-4*h)));assert abs(aux-r['natural_aux'])<1e-8
        if r['strict_original_time_pass']:assert direct<1e-6 and aux<1e-6
        checks.append(dict(case=p.parent.name,stored_status=r['status'],max_economic_error=err,natural_direct=direct,natural_aux=aux))
    assert len(checks)==24
    print(json.dumps(dict(status='PASS_SAVED_STATE_REPLAY_NOT_NEW_EQUILIBRIUM',cases=len(checks),checks=checks),indent=2))
if __name__=='__main__':main()
