import os,sys
from pathlib import Path
sys.path.insert(0,str(Path('.vendor').resolve()))
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MPLCONFIGDIR',str(Path('.mplconfig').resolve()))
import argparse,json,time
import numpy as np
from src.model import Model

def solve(m,steps=10000,step=1e-4,tol=1e-6,start=None):
    y=m.initial() if start is None else start.copy(); history=[]; tick=time.time()
    for it in range(steps):
        h,_=m.evaluate(y); natural=np.linalg.norm(y-m.project(y-step*h))
        if natural<tol: break
        half=m.project(y-step*h); hh,_=m.evaluate(half); new=m.project(y-step*hh)
        diff=np.linalg.norm(new-y); y=new
        if it%100==0:
            history.append([it,natural,diff,time.time()-tick]); print(it,natural,flush=True)
    h,result=m.evaluate(y); result.update(iterations=it+1,natural_residual=float(np.linalg.norm(y-m.project(y-step*h))),step=step,theta=m.theta,seconds=time.time()-tick,network=m.name,maas=m.maas,penalty=m.penalty,converged=bool(np.linalg.norm(y-m.project(y-step*h))<tol))
    return y,result,history

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--network',default='small'); p.add_argument('--maas',action='store_true'); p.add_argument('--steps',type=int,default=10000); p.add_argument('--step',type=float,default=1e-4); p.add_argument('--theta',type=float,default=1); p.add_argument('--penalty',type=float); p.add_argument('--tag',default='run'); p.add_argument('--start'); a=p.parse_args()
    m=Model(a.network,a.maas,a.theta,a.penalty)
    y,r,h=solve(m,a.steps,a.step,start=np.load(a.start) if a.start else None)
    out=Path('results')/a.tag; out.mkdir(parents=True,exist_ok=True)
    np.save(out/'state.npy',y); np.savetxt(out/'history.csv',h,delimiter=',',header='iteration,natural_residual,step_difference,seconds',comments='')
    (out/'metrics.json').write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
