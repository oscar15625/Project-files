"""Bounded, resumable final mechanism campaign. No automatic parameter fitting."""
import run
from pathlib import Path
import argparse, json, time, traceback
import numpy as np
from scipy.special import wrightomega, logsumexp
from src.model import Model
from refine import refine
from audit import audit as retail_audit
import spec_audit_v5 as costs

OUT=Path('results/v6'); OUT.mkdir(parents=True,exist_ok=True)

def write(path,obj):
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8'); tmp.replace(path)

def cases():
    result=[]
    for name in ['sioux','small']:
        common=dict(name=name,mod_access_scope='node',pt_access_scope='node')
        for label,maas,pt in [('without',False,1 if name=='sioux' else 1.3),('paper',True,1 if name=='sioux' else 1.3),('pt2',True,2)]+([('pt1',True,1)] if name=='small' else []):
            tag=f'{name}_node_{label}'
            source=f'v4/{name}_node_node_total0_'+('with' if maas else 'without')
            result.append(dict(tag=tag,phase='core',config=dict(common,maas=maas,wholesale=[1.5 if name=='sioux' else 1.3,pt]),source=source))
    for label,maas,pt in [('without',False,1),('paper',True,1),('pt2',True,2)]:
        result.append(dict(tag=f'sioux_aggregate_{label}',phase='core',config=dict(name='sioux',maas=maas,mod_access_scope='aggregate',pt_access_scope='node',wholesale=[1.5,pt]),source='v4/sioux_aggregate_node_total0_'+('with' if maas else 'without')))
    for variant,updates in [('initial1',dict(initial_pt_wait=1)),('transfer1',dict(transfer_pt_wait=1))]:
        for maas in [False,True]:
            label='paper' if maas else 'without'
            result.append(dict(tag=f'sioux_{variant}_{label}',phase='diagnostic',config=dict(name='sioux',maas=maas,mod_access_scope='node',pt_access_scope='node',**updates),source=f'v6/sioux_node_{label}'))
    for name in ['sioux','small']:
        result.append(dict(tag=f'{name}_no_discount',phase='diagnostic',config=dict(name=name,maas=True,mod_access_scope='node',pt_access_scope='node',penalty=8 if name=='sioux' else 10),source=f'v6/{name}_node_paper'))
    return result

def validate(tag):
    folder=OUT/tag; r=json.loads((folder/'metrics.json').read_text()); m=Model(**r['config']); y=np.load(folder/'state.npy')
    h,b=m.evaluate(y,True); flow=m.last_flows.copy(); ods=np.array(m.last_od)
    np.savetxt(folder/'od_results.csv',ods,delimiter=',',header='origin,destination,demand,maas_fare,share_non,share_drive,share_maas,value,conditional_wholesale_mod,conditional_wholesale_pt',comments='')
    a=retail_audit('v6/'+tag)
    fixed=~m.congest
    capacity_violation=float(np.maximum(flow[fixed]-m.cap[fixed],0).max())
    complement=float(np.max(np.abs((y[:m.nt][fixed]-m.t0[fixed])*(m.cap[fixed]-flow[fixed]))))
    # Exact OD fare best response with all competitors and resource times fixed.
    fare_gain=0.; fare_gradient_error=0.
    if m.maas:
        probe=y.copy(); mf=Model(**r['config']); mf.optimize_fares=True
        best=mf.evaluate(probe)[1]
        fare_gain=max(0.,best['profit_maas']-b['profit_maas'])
        for idx in np.unique(np.linspace(0,m.nod-1,min(5,m.nod)).astype(int)):
            yp=y.copy(); ym=y.copy(); eps=1e-5; yp[m.nt+idx]+=eps; ym[m.nt+idx]-=eps
            fd=(m.evaluate(yp)[1]['profit_maas']-m.evaluate(ym)[1]['profit_maas'])/(2*eps)
            fare_gradient_error=max(fare_gradient_error,abs(fd+h[m.nt+idx]))
    out=dict(retail_test=a,capacity_violation=capacity_violation,capacity_complementarity=complement,maas_exact_fare_gain=fare_gain,maas_fare_gradient_error=fare_gradient_error,flow_conservation_error=b['flow_conservation_error'],accounting_error=b['accounting_error'],natural_residual=r['natural_residual'],scaled_residual=r['scaled_residual'])
    out['pass']=bool(r['natural_residual']<1e-6 and r['scaled_residual']<1e-6 and a['all_retail_deviation_gains_below_1e-4'] and fare_gain<1e-4 and fare_gradient_error<1e-3 and capacity_violation<1e-4 and complement<1e-3 and abs(b['accounting_error'])<1e-6 and b['flow_conservation_error']<1e-6)
    write(folder/'validation.json',out)
    costs.OUT=OUT/'cost_audits'; costs.OUT.mkdir(exist_ok=True)
    if not (costs.OUT/tag/'COMPLETE').exists(): costs.audit(tag,source_root=OUT,price_profile=False)
    return out

def execute(case):
    tag=case['tag']; folder=OUT/tag; folder.mkdir(exist_ok=True)
    if (folder/'COMPLETE').exists(): return json.loads((folder/'validation.json').read_text())
    m=Model(**case['config']); write(folder/'run_definition.json',case)
    if not (folder/'metrics.json').exists():
        start=np.load(Path('results')/case['source']/'state.npy')
        # Deliberately perturb leader starts so this is a new solve, not re-export.
        start[-2:]*=[1.03,.97]
        resume=(folder/'checkpoints').exists() and any((folder/'checkpoints').glob('*.npz'))
        refine(m,'v6/'+tag,start,maxiter=100,resume=resume)
    validation=validate(tag)
    (folder/'COMPLETE').write_text('PASS\n' if validation['pass'] else 'FAILED_VALIDATION\n')
    return validation

def main():
    p=argparse.ArgumentParser(); p.add_argument('phase',choices=['core','diagnostic','all']); args=p.parse_args()
    manifest=json.loads((OUT/'manifest.json').read_text()) if (OUT/'manifest.json').exists() else {}
    for case in cases():
        if args.phase!='all' and case['phase']!=args.phase: continue
        tag=case['tag']; print('START',tag,flush=True)
        try:
            result=execute(case); manifest[tag]=dict(status='PASS' if result['pass'] else 'FAILED_VALIDATION',definition=case)
        except Exception:
            message=traceback.format_exc(); (OUT/tag/'error.txt').write_text(message); print(message,flush=True)
            manifest[tag]=dict(status='ERROR',definition=case,error=message)
        write(OUT/'manifest.json',manifest); print('FINISHED',tag,manifest[tag]['status'],flush=True)

if __name__=='__main__': main()
