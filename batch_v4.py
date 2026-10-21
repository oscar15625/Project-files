"""Resumable, explicitly labelled structural and scale sensitivity experiments."""
import run
import json,traceback,argparse
from pathlib import Path
import numpy as np
from src.model import Model
from refine import refine
from audit import audit

def execute(m,tag,start=None,maxiter=100):
    folder=Path('results')/tag
    try:
        if (folder/'metrics.json').exists():
            r=json.loads((folder/'metrics.json').read_text()); y=np.load(folder/'state.npy')
        else:
            resume=(folder/'checkpoints').exists() and any((folder/'checkpoints').glob('*.npz'))
            y,r=refine(m,tag,start,maxiter,resume=resume)
        if r['converged']:
            if not (folder/'audit.json').exists(): audit(tag)
            m.evaluate(y,True)
            np.savetxt(folder/'od_results.csv',m.last_od,delimiter=',',header='origin,destination,demand,maas_fare,share_non,share_drive,share_maas,value,conditional_wholesale_mod,conditional_wholesale_pt',comments='')
            np.savetxt(folder/'resource_results.csv',np.c_[np.arange(m.nt),m.t0,m.cap,m.congest,y[:m.nt],m.last_flows],delimiter=',',header='resource,t0,capacity,congestible,time,flow',comments='')
            a=json.loads((folder/'audit.json').read_text())
            if a['all_retail_deviation_gains_below_1e-4']: return y,r
        return None,r
    except Exception:
        folder.mkdir(parents=True,exist_ok=True); (folder/'error.txt').write_text(traceback.format_exc()); traceback.print_exc(); return None,None

def pair(config,tag,warm=None):
    base=Model(maas=False,**config); y,r=execute(base,tag+'_without',warm)
    m=Model(maas=True,**config)
    start=np.r_[y[:m.nt],np.full(m.nod,5.),y[-2:]] if y is not None else None
    z,s=execute(m,tag+'_with',start)
    return y,z

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['scope','common','mode']); a=p.parse_args()
    if a.phase=='scope':
        for name in ['sioux','small']:
            for ms,ps,total in [('node','node',False),('aggregate','node',False),('aggregate','line_node',False),('node','node',True)]:
                warm=np.load(f'results/{name}_node_theta1_without/state.npy') if ms==ps=='node' and not total else None
                pair(dict(name=name,mod_access_scope=ms,pt_access_scope=ps,pt_capacity_total=total),f'v4/{name}_{ms}_{ps}_total{int(total)}',warm)
    else:
        for name in ['sioux','small']:
            warm=np.load(f'results/{name}_node_theta1_without/state.npy')
            for scale in [.5,.2,.1,.05,.03,.01]:
                config=dict(name=name,access_scope='node',theta=scale if a.phase=='common' else 1.,mode_theta=scale)
                y,z=pair(config,f'v4/{name}_{a.phase}_{scale:g}',warm)
                if y is not None: warm=y
