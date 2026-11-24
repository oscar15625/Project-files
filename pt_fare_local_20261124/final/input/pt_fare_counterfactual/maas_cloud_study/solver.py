"""Independent small-network VI residual solve. No global Nash/EG claim."""
import numpy as np
from scipy.optimize import least_squares
from time import perf_counter

def solve(m, guess=None, max_nfev=70, verbose=0, optimize_fares=True):
    start=perf_counter()
    m.optimize_fares=bool(m.maas and optimize_fares)
    y=m.initial() if guess is None else np.array(guess,copy=True,dtype=float)
    mask=m.congest
    if m.maas and optimize_fares:
        if len(y)==m.nt+m.nod+2:y=np.r_[y[:m.nt],y[-2:]]
    def decode(x):
        u=x.copy();u[:m.nt][mask]=m.t0[mask]*(1+.15*np.maximum(x[:m.nt][mask],0)**4)
        if m.maas and optimize_fares:u=np.r_[u[:m.nt],np.zeros(m.nod),u[-2:]]
        return m.project(u)
    x=y.copy();x[:m.nt][mask]=(np.maximum(y[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25
    lower=np.r_[np.where(mask,0,m.t0),np.zeros(len(x)-m.nt)]
    x=np.maximum(x,lower+1e-9)
    calls=0
    def resid(x):
        nonlocal calls
        calls+=1
        yy=decode(x);h,_=m.evaluate(yy);f=m.last_flows
        r=np.r_[h[:m.nt],h[-2:]] if (m.maas and optimize_fares) else h.copy()
        r[:m.nt][mask]=x[:m.nt][mask]-f[mask]/m.cap[mask]
        r[:m.nt][~mask]=(yy[:m.nt]-np.maximum(m.t0,yy[:m.nt]-h[:m.nt]/m.cap))[~mask]
        if m.maas and not optimize_fares:
            ids=slice(m.nt,m.nt+m.nod)
            f=y[ids] if False else yy[ids]
            r[ids]=f-np.maximum(0,f-r[ids]/np.maximum(m.total/m.nod/3,1))
        r[-2:]/=np.maximum(m.retail_volume,1e-8)
        r[-2:]=yy[-2:]-np.maximum(0,yy[-2:]-r[-2:])
        return r
    opt=least_squares(resid,x,bounds=(lower,np.full(len(x),200.)),max_nfev=max_nfev,xtol=1e-11,ftol=1e-11,gtol=1e-11,verbose=verbose)
    yy=decode(opt.x);h,r=m.evaluate(yy,details=True)
    # More stable direct time complementarity without inverse BPR cancellation.
    hh=h.copy();hh[:m.nt][mask]=m.cap[mask]*np.maximum(opt.x[:m.nt][mask],0)-m.last_flows[mask]
    projected=np.linalg.norm(yy-m.project(yy-1e-4*hh))
    residual=np.linalg.norm(resid(opt.x))
    return dict(y=yy,meta=dict(success=bool(opt.success),status=int(opt.status),nfev=int(opt.nfev),calls=int(calls),seconds=round(perf_counter()-start,2),scaled_residual=residual,natural_projected=projected,flow_conservation=r['flow_conservation_error'],accounting=r['accounting_error'],message=str(opt.message)),metrics=r, model=m)
if __name__=='__main__':
    import sys
    sys.path.insert(0,'.')
    from src.model import Model
    for maas in [False,True]:
        m=Model('small',maas=maas,access_scope='node',penalty=1)
        r=solve(m,max_nfev=80);print(maas,r['meta'],{k:v for k,v in r['metrics'].items() if k in ['profit_pt','profit_mod','profit_maas','share_maas','traveler_welfare']})
