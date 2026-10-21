import run
import numpy as np
from scipy.optimize import minimize_scalar
from pathlib import Path
import json
from src.model import Model

def audit(tag):
    folder=Path('results')/tag; r=json.loads((folder/'metrics.json').read_text()); y=np.load(folder/'state.npy')
    m=Model(r['network'],r['maas'],r['theta'],r['penalty'],r['wholesale'],r['access_scope'])
    h,base=m.evaluate(y); ans={}
    for idx,key in [(-2,'profit_mod'),(-1,'profit_pt')]:
        failed=[]
        def obj(p):
            z=y.copy(); z[idx]=p
            try: return -m.evaluate(z)[1][key]
            except ValueError:
                failed.append(float(p)); return np.inf
        grid=np.unique(np.r_[np.linspace(0,10,31),y[idx],20,50,100,200])
        vals=np.array([obj(p) for p in grid]); j=vals.argmin()
        fit=minimize_scalar(obj,bounds=(grid[max(0,j-1)],grid[min(len(grid)-1,j+1)]),method='bounded',options={'xatol':1e-8})
        best=min(vals.min(),fit.fun); ans[key]={'equilibrium':base[key],'best_grid_refined':float(-best),'unilateral_gain':max(0,float(-best-base[key])),'failed_price_evaluations':failed}
    # Root equation and terminal balance are independently observable diagnostics.
    ans['flow_conservation_error']=base['flow_conservation_error']
    ans['all_retail_deviation_gains_below_1e-4']=all(ans[k]['unilateral_gain']<1e-4 for k in ['profit_mod','profit_pt'])
    (folder/'audit.json').write_text(json.dumps(ans,indent=2)); print(tag,ans,flush=True)
if __name__=='__main__':
    for tag in ['small_node_theta1_without','small_node_theta1_with','sioux_node_theta1_without','sioux_node_theta1_with']:
        audit(tag)
