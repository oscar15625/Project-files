"""Small-network diagnostic VI root in BPR flow coordinates.

Original auxiliary scheme preserved as documentation; this is an explicitly new
solver of a *different* nested-root VI. It is not Algorithm 1 or a Nash proof.
"""
import time, numpy as np
from scipy.optimize import least_squares


def encode(m,y):
    x=y.copy();road=m.congest
    x[:m.nt][road]=(np.maximum(y[:m.nt][road]/m.t0[road]-1,0)/.15)**.25
    return x


def decode(m,x):
    y=x.copy();road=m.congest
    y[:m.nt][road]=m.t0[road]*(1+.15*np.maximum(x[:m.nt][road],0)**4)
    return m.project(y)


def residual(m,x):
    y=decode(m,x)
    h,_=m.evaluate(y,details=True)
    road=m.congest
    r=np.empty_like(x)
    r[:m.nt][road]=x[:m.nt][road]-m.last_flows[road]/m.cap[road]
    r[:m.nt][~road]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~road]
    if m.maas:
        ods=np.asarray(m.last_od)
        denom=np.maximum(ods[:,2]*ods[:,6],1e-7)
        hf=h[m.nt:-2]/denom
        r[m.nt:-2]=y[m.nt:-2]-np.clip(y[m.nt:-2]-hf,0,200)
    scaled=h[-2:]/np.maximum(m.retail_volume,1e-7)
    r[-2:]=y[-2:]-np.clip(y[-2:]-scaled,0,200)
    return r


def solve(m,y0,max_nfev=100,ftol=2e-12,verbose=False):
    start=time.perf_counter();x=encode(m,y0)
    lower=np.r_[np.where(m.congest,0,m.t0),np.zeros(len(x)-m.nt)]
    upper=np.r_[np.where(m.congest,4,200),np.full(len(x)-m.nt,200.)]
    x=np.maximum(x,lower+1e-9);x=np.minimum(x,upper-1e-9)
    calls=[0]
    def fun(v):calls[0]+=1;return residual(m,v)
    opt=least_squares(fun,x,bounds=(lower,upper),max_nfev=max_nfev,ftol=ftol,xtol=ftol,gtol=ftol,x_scale='jac',verbose=2 if verbose else 0)
    y=decode(m,opt.x);h,economy=m.evaluate(y,details=True)
    ha=h.copy();ha[:m.nt][m.congest]=m.cap[m.congest]*np.maximum(opt.x[:m.nt][m.congest],0)-m.last_flows[m.congest]
    aux=float(np.linalg.norm(y-m.project(y-1e-4*ha)))
    direct=float(np.linalg.norm(y-m.project(y-1e-4*h)))
    rv=float(np.linalg.norm(residual(m,opt.x)))
    fixed=~m.congest
    resource_violation=float(max(0.,np.max(m.last_flows[fixed]-m.cap[fixed])))
    complementary=float(np.max(np.abs((y[:m.nt][fixed]-m.t0[fixed])*(m.cap[fixed]-m.last_flows[fixed]))))
    result={**economy,'solver_success':bool(opt.success),'solver_message':str(opt.message),'nfev_reported':int(opt.nfev),'H_calls':int(calls[0]),'wall_seconds':time.perf_counter()-start,'root_scaled_residual':rv,'original_direct_natural':direct,'aux_coordinate_natural':aux,'capacity_violation':resource_violation,'capacity_complementarity':complementary,'state_price_maas':y[m.nt:-2].tolist(),'state_price_retail':y[-2:].tolist(),'lambda':m.nest_lambda}
    # CONDITIONAL, and only when original problem's relevant core tests pass.
    result['provisional_pass']=bool(rv<1e-7 and aux<1e-6 and resource_violation<1e-4 and abs(economy['accounting_error'])<1e-7 and economy['flow_conservation_error']<1e-7)
    return y,opt.x,result
