"""PT retail tariff adapter; original pinned Model and physical supply are untouched."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import sys,json,time,hashlib,importlib.util
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from src.model import Model,Graph,inputs
import numpy as np
sys.path.insert(0,str(ROOT/'input/pt_fare_counterfactual'))
# Import only definitions, never the package's experiment runners.
spec=importlib.util.spec_from_file_location('cloud_tariff_definitions',ROOT/'input/pt_fare_counterfactual/fare_models.py')
fm=importlib.util.module_from_spec(spec);spec.loader.exec_module(fm)
def make(name,tariff,maas):
 if name=='small':m=Model('small',maas=maas,access_scope='node',penalty=1.)
 else:m=Model('sioux',maas=maas,mod_access_scope='aggregate',pt_access_scope='node',penalty=.5,wholesale=[1.5,1.])
 if name!='small' and tariff=='zones':raise ValueError('No Sioux Falls zone map supplied: no zone counterfactual authorized by data')
 return fm.change_non_maas_tariff(m,tariff)
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist()),encoding='utf-8');tmp.replace(path)
def fixed_checks(m,y):
 m.optimize_fares=False;h,r=m.evaluate(y.copy(),True);flow=m.last_flows.copy();mask=m.congest
 direct=float(np.linalg.norm(y-m.project(y-1e-4*h)))
 cap=float(np.maximum(flow[~mask]-m.cap[~mask],0).max())
 comp=float(np.max(abs((y[:m.nt]-m.t0)[~mask]*(m.cap-flow)[~mask])))
 fd=[]
 for i,key in [(-2,'profit_mod'),(-1,'profit_pt')]+([(m.nt,'profit_maas'),(m.nt+m.nod//2,'profit_maas'),(m.nt+m.nod-1,'profit_maas')] if m.maas else []):
  eps=1e-5;yp=y.copy();ym=y.copy();yp[i]+=eps;ym[i]-=eps
  slope=(m.evaluate(yp)[1][key]-m.evaluate(ym)[1][key])/(2*eps)
  fd.append(dict(variable=i,analytic=-h[i],finite_difference=slope,absolute_error=abs(slope+h[i]),relative_error=abs(slope+h[i])/max(1,abs(slope),abs(h[i]))))
 m.evaluate(y.copy(),True)
 return dict(natural_direct=direct,capacity_violation=cap,complementarity=comp,gradient_checks=fd,flow_conservation=abs(r['flow_conservation_error']),accounting_error=abs(r['accounting_error']),metrics=r)
def audit():
 os.chdir(ROOT);out=ROOT/'audit';out.mkdir(exist_ok=True);checks=[]
 for tariff in ['link','flat','zones']:
  for maas in [False,True]:
   case=tariff+('_with_MaaS' if maas else '_without_MaaS');p=ROOT/'input/pt_fare_counterfactual/results'
   expected=json.loads((p/(case+'.json')).read_text());y=np.load(p/(case+'.npy'));m=make('small',tariff,maas);rr=fixed_checks(m,y)
   err=max(abs(rr['metrics'][k]-expected[k]) for k in rr['metrics']);assert err<1e-6,(case,err)
   assert max(v['absolute_error'] for v in rr['gradient_checks'])<1e-5
   rr.update(case=case,source_claimed_pass=expected['passed'],max_economic_replay_error=err,status='PASS_REPLAY',strict_time_pass=rr['natural_direct']<1e-6)
   checks.append(rr);write(out/'small_six_replay.json',checks)
 zero=[];benchmark=[]
 for name in ['small','sioux']:
  for maas in [False,True]:
   m=make(name,'link',maas);y=m.initial();y[-1]=0;m.optimize_fares=False;h0,r0=m.evaluate(y.copy());f0=m.last_flows.copy()
   for tariff in (['flat','zones'] if name=='small' else ['flat']):
    mf=make(name,tariff,maas);hh,rr=mf.evaluate(y.copy());err=max(abs(r0['traveler_welfare']-rr['traveler_welfare']),float(np.max(abs(f0-mf.last_flows))))
    assert err<1e-6,(name,maas,tariff,err)
    assert np.array_equal(m.cap,mf.cap) and np.array_equal(m.t0,mf.t0)
    zero.append(dict(network=name,maas=maas,tariff=tariff,max_error=err,status='PASS'))
   if name=='sioux':
    for tariff in ['link','flat']:
     mm=make(name,tariff,maas);yy=mm.initial();mm.optimize_fares=maas;t=time.perf_counter();hh,rr=mm.evaluate(yy.copy(),True);secs=time.perf_counter()-t
     benchmark.append(dict(tariff=tariff,maas=maas,H_seconds=secs,traffic_variables=mm.nt,ODs=mm.nod,demand=mm.total,graph_states=sum(g.n for _,gr in mm.graphs for g in gr.values()),graph_edges=sum(len(g.i) for _,gr in mm.graphs for g in gr.values()),initial_conservation=rr['flow_conservation_error'],config=mm.config()))
 write(out/'zero_PT_regression.json',zero);write(out/'full_network_benchmark.json',benchmark)
 # State-transition charge checks include initial PT boarding and MoD -> PT transfer.
 m=make('sioux','flat',True);counts=dict(initial_PT=0,MOD_to_PT=0,reentry=0)
 for _,gr in m.graphs:
  g=gr['non']
  for (s,j),a in zip(g.edge_labels,g.attr):
   expected=int(isinstance(j[0],int) and s[-1]==0)
   assert a[3]==expected
   if isinstance(j[0],int):
    if s[0]=='gate' and s[-1]==0:counts['initial_PT']+=1
    if s[0]=='M' and s[-1]==0:counts['MOD_to_PT']+=1
    if s[-1]==1:counts['reentry']+=1
 assert min(counts.values())>0;write(out/'first_boarding_transition_checks.json',dict(status='PASS',counts=counts))
 write(out/'GATE.json',dict(status='PASS_MODEL_REPLAY_AND_TARIFF_INVARIANCE',small_states=6,small_strict_time_pass=sum(r['strict_time_pass'] for r in checks),zero_price_checks=len(zero),new_solves=0,zone_extension='NOT_RUN_NO_SIOUX_ZONE_MAP'))
 print(json.dumps(dict(small_strict_time_pass=sum(r['strict_time_pass'] for r in checks),benchmarks=benchmark),indent=2))
if __name__=='__main__':audit()
