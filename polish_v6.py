"""Exact active-set cleanup for numerically slack small-network PT resources.

Preserve every original file. Only remove <1e-6 excess delay when capacity is
strictly slack, then recompute fares/residuals; never change economic parameters.
"""
import run, json, shutil
from pathlib import Path
import numpy as np
from src.model import Model
from campaign_v6 import validate,write,OUT

def polish(tag):
    folder=OUT/tag; original=folder/'before_active_set_polish'
    if original.exists(): return
    r=json.loads((folder/'metrics.json').read_text()); y=np.load(folder/'state.npy'); x=np.load(folder/'coordinates.npy'); m=Model(**r['config'])
    m.evaluate(y); f=m.last_flows.copy()
    active=(~m.congest)&(y[:m.nt]-m.t0<1e-6)&(m.cap-f>1e-3)
    original.mkdir()
    for name in ['state.npy','coordinates.npy','metrics.json','validation.json','audit.json','COMPLETE']:
        if (folder/name).exists(): shutil.copy2(folder/name,original/name)
    maximum=float(np.max(y[:m.nt][active]-m.t0[active])); y[:m.nt][active]=m.t0[active]; x[:m.nt][active]=m.t0[active]
    m.optimize_fares=m.maas; h,now=m.evaluate(y); flow=m.last_flows.copy(); h[:m.nt][m.congest]=m.cap[m.congest]*x[:m.nt][m.congest]-flow[m.congest]
    residual=np.r_[h[:m.nt],h[-2:]]
    residual[:m.nt][m.congest]=x[:m.nt][m.congest]-flow[m.congest]/m.cap[m.congest]
    residual[:m.nt][~m.congest]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~m.congest]
    residual[-2:]/=np.maximum(m.retail_volume,1e-8); residual[-2:]=y[-2:]-np.maximum(0,y[-2:]-residual[-2:])
    r.update(now); r.update(natural_residual=float(np.linalg.norm(y-m.project(y-1e-4*h))),scaled_residual=float(np.linalg.norm(residual)),active_set_polish=dict(resources=int(active.sum()),maximum_time_change=maximum,preserved_original='before_active_set_polish'))
    r['converged']=r['natural_residual']<1e-6
    np.save(folder/'state.npy',y); np.save(folder/'coordinates.npy',x); write(folder/'metrics.json',r)
    # Full cost audit must be regenerated because the state changed.
    import spec_audit_v5 as cost
    cost.OUT=OUT/'cost_audits'; cost.audit(tag,source_root=OUT,price_profile=False)
    v=validate(tag); (folder/'COMPLETE').write_text('PASS\n' if v['pass'] else 'FAILED_VALIDATION\n')
    manifest=json.loads((OUT/'manifest.json').read_text()); manifest[tag]['status']='PASS' if v['pass'] else 'FAILED_VALIDATION'; manifest[tag]['numerical_polish']=r['active_set_polish']; write(OUT/'manifest.json',manifest)
    print(tag,r['active_set_polish'],v['pass'])

if __name__=='__main__':
    for name in ['small_node_without','small_node_paper','small_node_pt2']: polish(name)
