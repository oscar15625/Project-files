"""M01 minimal interface: identical Model.evaluate/project, original variables.

Smoke tests are not the handoff's full 3-solvers x 2-networks x 3-starts
time-to-convergence benchmark. No performance ranking is inferred.
"""
from research_experiments import np
import time
def natural_residual(model,y,h,gamma=1e-4):
    return float(np.linalg.norm(y-model.project(y-gamma*h)))
def solve_projection(model,start,method='EG_FIXED',step=1e-6,max_steps=2,tol=1e-6,eta=.7,min_step=1e-12):
    if method not in ['PG','EG_FIXED','EG_ADAPT']: raise ValueError(method)
    y=start.copy(); model.optimize_fares=False; calls=0; trace=[]; tick=time.perf_counter()
    def H(z):
        nonlocal calls
        calls+=1; return model.evaluate(z)[0]
    status='MAX_STEPS_SMOKE'
    for it in range(max_steps):
        h=H(y); residual=natural_residual(model,y,h)
        trace.append(dict(iteration=it,h_evaluations=calls,residual=residual,step=step,seconds=time.perf_counter()-tick))
        if residual<tol: status='PASS_RESIDUAL'; break
        half=model.project(y-step*h)
        if method=='PG': y=half; continue
        hh=H(half)
        if method=='EG_ADAPT':
            while step*np.linalg.norm(hh-h)>eta*np.linalg.norm(half-y):
                step*=.5
                if step<min_step: return y,dict(status='FAILED_LINESEARCH',trace=trace,h_evaluations=calls)
                half=model.project(y-step*h); hh=H(half)
        y=model.project(y-step*hh)
    h=H(y); residual=natural_residual(model,y,h)
    return y,dict(status=status,residual=residual,h_evaluations=calls,seconds=time.perf_counter()-tick,trace=trace,final_step=step,scope='INTERFACE_SMOKE_ONLY')

def smoke():
    from research_experiments import Model,OUT,write
    records=[]
    for name in ['small','sioux']:
        for seed,factor in enumerate([.99,1.,1.01]):
            m=Model(name,True,mod_access_scope='node',pt_access_scope='node')
            start=m.project(m.initial()*factor)
            # Independent explicit first-step formula guards predictor/corrector order.
            h=m.evaluate(start)[0]; half=m.project(start-1e-6*h); hh=m.evaluate(half)[0]
            expected={'PG':half,'EG_FIXED':m.project(start-1e-6*hh)}
            for method in ['PG','EG_FIXED','EG_ADAPT']:
                one,check=solve_projection(m,start,method,max_steps=1)
                if method in expected: assert np.max(abs(one-expected[method]))<1e-12
                y,r=solve_projection(m,start,method,max_steps=2)
                assert np.all(np.isfinite(y)) and np.max(abs(y-m.project(y)))<1e-12
                records.append(dict(network=name,seed=seed,initial_factor=factor,method=method,**r))
    write(OUT/'M01/interface_smoke.json',records)
    print('18 finite feasible interface smoke checks; not a convergence benchmark')
if __name__=='__main__': smoke()
