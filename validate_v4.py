import run
import numpy as np,json
from pathlib import Path
from src.model import Model
from refine import refine

report={}
for name in ['small','sioux']:
    m=Model(name,True); y=m.initial(); h,r=m.evaluate(y)
    for _,group in m.graphs:
        for g in group.values(): g.stable=False
    old,rr=m.evaluate(y)
    err=float(np.max(abs(h-old))); assert err<1e-7,err
    report[name+'_potential_equivalence']=err
for route,mode in [(1,.03),(.03,.03),(.01,.01)]:
    m=Model('sioux',True,theta=route,mode_theta=mode,mod_access_scope='aggregate',pt_access_scope='node')
    y=m.initial(); h,r=m.evaluate(y); errors=[]
    for idx,key in [(-2,'profit_mod'),(-1,'profit_pt'),(m.nt,'profit_maas')]:
        eps=1e-6; yp=y.copy(); ym=y.copy(); yp[idx]+=eps; ym[idx]-=eps
        fd=(m.evaluate(yp)[1][key]-m.evaluate(ym)[1][key])/(2*eps)
        errors.append(float(abs(fd+h[idx])/max(1,abs(fd))))
    assert max(errors)<2e-5,errors
    assert abs(r['accounting_error'])<1e-6
    assert abs(r['share_non_mod']+r['share_non_pt']-r['share_non'])<1e-8
    report[f'scales_{route}_{mode}']=dict(gradient_errors=errors,accounting_error=r['accounting_error'],conservation=r['flow_conservation_error'])
m=Model('small',False,access_scope='node')
start=np.load('results/small_node_theta1_without/state.npy'); start[-2:]*=1.02
try: refine(m,'v4/test_resume',start=start,maxiter=80,stop_after=2)
except InterruptedError: pass
y,r=refine(m,'v4/test_resume',maxiter=100,resume=True)
z,s=refine(Model('small',False,access_scope='node'),'v4/test_uninterrupted',start=start,maxiter=100)
assert r['converged'] and s['converged']
error=float(np.max(abs(y-z))); assert error<1e-5,error
report['interrupted_restart_state_error']=error
Path('results/v4/validation.json').write_text(json.dumps(report,indent=2)); print(report)
