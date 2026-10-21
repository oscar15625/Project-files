"""Root refinement of the same VI; does not claim to reproduce Algorithm 1 trajectory."""
import run
import numpy as np
from scipy.optimize import root
from pathlib import Path
import json,time,argparse
from src.model import Model

def refine(m,tag,start=None,maxiter=300):
    y=m.initial() if start is None else start.copy(); history=[]; tick=time.time(); calls=0
    def fun(y):
        nonlocal calls
        y=m.project(y); h,_=m.evaluate(y); f=m.last_flows
        r=h.copy(); mask=m.congest
        target=m.t0[mask]*(1+.15*(f[mask]/m.cap[mask])**4)
        r[:m.nt][mask]=y[:m.nt][mask]-target
        r[:m.nt][~mask]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~mask]
        r[m.nt:]/=m.total
        if m.maas: r[m.nt:-2]*=m.total/m.ods[:,2]
        r[m.nt:]=y[m.nt:]-np.maximum(0,y[m.nt:]-r[m.nt:])
        calls+=1
        return r
    def callback(x,f):
        history.append([len(history),float(np.linalg.norm(f)),time.time()-tick])
        print(tag,len(history),np.linalg.norm(f),flush=True)
    opt=root(fun,y,method='krylov',callback=callback,options={'fatol':1e-10,'maxiter':maxiter,'line_search':'armijo'})
    y=m.project(opt.x); h,r=m.evaluate(y); r.update(network=m.name,maas=m.maas,theta=m.theta,penalty=m.penalty,wholesale=m.wholesale.tolist(),method='Krylov root refinement of equivalent VI',solver_success=bool(opt.success),message=str(opt.message),calls=calls,seconds=time.time()-tick,natural_residual=float(np.linalg.norm(y-m.project(y-1e-4*h))),scaled_residual=float(np.linalg.norm(fun(y))))
    r['converged']=r['natural_residual']<1e-6
    out=Path('results')/tag; out.mkdir(parents=True,exist_ok=True); np.save(out/'state.npy',y); (out/'metrics.json').write_text(json.dumps(r,indent=2)); np.savetxt(out/'history.csv',history,delimiter=',',header='iteration,scaled_residual,seconds',comments='')
    print(json.dumps(r,indent=2)); return y,r
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--network',default='small'); p.add_argument('--maas',action='store_true'); p.add_argument('--theta',type=float,default=1); p.add_argument('--penalty',type=float); p.add_argument('--tag',default='refined'); p.add_argument('--start'); p.add_argument('--maxiter',type=int,default=300); a=p.parse_args()
    refine(Model(a.network,a.maas,a.theta,a.penalty),a.tag,np.load(a.start) if a.start else None,a.maxiter)
