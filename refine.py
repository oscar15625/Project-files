"""Root refinement of the same VI; does not claim to reproduce Algorithm 1 trajectory."""
import run
import numpy as np
from scipy.optimize import root, least_squares
from pathlib import Path
import json,time,argparse
from src.model import Model

def refine(m,tag,start=None,maxiter=300):
    y=m.initial() if start is None else start.copy(); history=[]; tick=time.time(); calls=0
    mask=m.congest
    m.optimize_fares=m.maas
    if m.maas: y=np.r_[y[:m.nt],y[-2:]]
    def decode(x):
        y=x.copy(); y[:m.nt][mask]=m.t0[mask]*(1+.15*np.maximum(x[:m.nt][mask],0)**4)
        if m.maas: y=np.r_[y[:m.nt],np.zeros(m.nod),y[-2:]]
        return m.project(y)
    x=y.copy(); x[:m.nt][mask]=(np.maximum(y[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25
    def fun(x):
        nonlocal calls
        y=decode(x); h,_=m.evaluate(y); f=m.last_flows
        r=np.r_[h[:m.nt],h[-2:]]
        r[:m.nt][mask]=x[:m.nt][mask]-f[mask]/m.cap[mask]
        r[:m.nt][~mask]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~mask]
        r[-2:]/=max(m.retail_mass,1e-8)
        r[-2:]=y[-2:]-np.maximum(0,y[-2:]-r[-2:])
        calls+=1
        return r
    def callback(x,f):
        history.append([len(history),float(np.linalg.norm(f)),time.time()-tick])
        print(tag,len(history),np.linalg.norm(f),flush=True)
    if m.name=='small':
        lower=np.r_[np.where(mask,0,m.t0),np.zeros(len(x)-m.nt)]
        x=np.maximum(x,lower+1e-8)
        opt=least_squares(fun,x,bounds=(lower,np.full(len(x),200.)),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=maxiter)
        callback(opt.x,opt.fun)
    else:
        opt=root(fun,x,method='krylov',callback=callback,options={'fatol':1e-8,'maxiter':maxiter,'line_search':'armijo'})
    y=decode(opt.x); h,r=m.evaluate(y)
    # Recover inverse-BPR supply from the solver coordinates to avoid cancellation
    # when tiny positive flows produce travel times indistinguishable from t0.
    h[:m.nt][mask]=m.cap[mask]*np.maximum(opt.x[:m.nt][mask],0)-m.last_flows[mask]
    r.update(network=m.name,maas=m.maas,theta=m.theta,penalty=m.penalty,wholesale=m.wholesale.tolist(),method='Flow-coordinate root refinement of equivalent VI',solver_success=bool(opt.success),message=str(opt.message),calls=calls,seconds=time.time()-tick,natural_residual=float(np.linalg.norm(y-m.project(y-1e-4*h))),scaled_residual=float(np.linalg.norm(fun(opt.x))))
    r['access_scope']=m.access_scope
    r['converged']=r['natural_residual']<1e-6
    out=Path('results')/tag; out.mkdir(parents=True,exist_ok=True); np.save(out/'state.npy',y); np.save(out/'coordinates.npy',opt.x); (out/'metrics.json').write_text(json.dumps(r,indent=2)); np.savetxt(out/'history.csv',history,delimiter=',',header='iteration,scaled_residual,seconds',comments='')
    print(json.dumps(r,indent=2)); return y,r
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--network',default='small'); p.add_argument('--maas',action='store_true'); p.add_argument('--theta',type=float,default=1); p.add_argument('--penalty',type=float); p.add_argument('--tag',default='refined'); p.add_argument('--start'); p.add_argument('--maxiter',type=int,default=300); a=p.parse_args()
    refine(Model(a.network,a.maas,a.theta,a.penalty),a.tag,np.load(a.start) if a.start else None,a.maxiter)
