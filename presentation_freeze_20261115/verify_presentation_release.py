"""Read-only portable evidence verification. Never runs an equilibrium solver."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import sys,json,hashlib,csv,collections
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'baseline'));sys.path.insert(0,str(ROOT/'baseline/results/vi_cloud_20261114/sources'))
import numpy as np
from src.model import Model
from nested_extension import NestedModel
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def facts():
 a,b,c=[read(ROOT/f'representative_results/{x}_reference/metrics.json') for x in 'ABC']
 placebo=collections.defaultdict(float)
 for r in rows(ROOT/'sources/e01_placebo_static.csv'):
  if r['frozen_state']=='A':placebo[r['choice_set']]+=float(r['weighted_utility'])
 er=rows(ROOT/'sources/e03_all_results_reaudited.csv'); e=[r for r in er if r['run'].startswith('E03_coarse/')]
 mr=rows(ROOT/'sources/m01_convergence_runs.csv')
 runs=[read(p) for p in sorted((ROOT/'baseline/results/vi_cloud_20261114/runs').glob('*/metrics.json'))]
 cloud=[read(p) for p in sorted((ROOT/'baseline/results/vi_cloud_20261114/cloud_reference').glob('*/audit.json'))]
 m03=read(ROOT/'sources/m03_summary.json')
 pt=collections.defaultdict(lambda:collections.defaultdict(float))
 for r in rows(ROOT/'sources/pt_channel_summary.csv'):
  if r['run'].startswith('E01/'):
   for k in ['any_actual_pt_trips','pt_vehicle_link_traversals']:pt[r['run']][k]+=float(r[k])
 out=dict(E01_AB=b['traveler_welfare']-a['traveler_welfare'],E01_BC=c['traveler_welfare']-b['traveler_welfare'],E01_AC=c['traveler_welfare']-a['traveler_welfare'],placebo={k:v-placebo['no_maas'] for k,v in placebo.items()},E03_total=len(e),E03_PASS=sum(r['status']=='PASS' for r in e),E03_L1=sum(r.get('L1')=='IMPROVING' for r in e),E03_L2=sum(r.get('L2')=='IMPROVING' for r in e),E03_failures=[r['run'] for r in e if r['status']!='PASS'],M01_total=len(mr),M01_PASS=sum(r['status']=='PASS' for r in mr),M01_h_budgets=sorted({int(r['h_budget']) for r in mr}),Root_total=len(runs),Root_strict_PASS=sum(r['strict_original_time_pass'] for r in runs),Root_status=dict(collections.Counter(r['status'] for r in runs)),PT=dict(pt),cloud=[dict(case=r['case'],profit_maas=r['profit_maas'],welfare_gain=r['traveler_welfare_gain_vs_A'],harmed_od=r['od_harmed_count']) for r in cloud],M03=m03,M02_probes=len(rows(ROOT/'sources/m02_timing_comparison.csv')))
 out['Root_groups']={k:dict(total=len(rr),PASS=sum(r['strict_original_time_pass'] for r in rr)) for k,rr in [('original_SCORE',[r for r in runs if 'lambda' not in r['case'] and r['score']=='SCORE']),('nested_default',[r for r in runs if 'lambda' in r['case'] and r['factor']==1]),('nested_restarts',[r for r in runs if 'lambda' in r['case'] and r['factor']!=1]),('DEMAND',[r for r in runs if r['score']=='DEMAND'])]}
 out['E03_L1_with_OD_loss']=sum(r.get('L1')=='IMPROVING' and int(float(r['harmed_od_count']))>0 for r in e)
 return out
def verify(check_manifest=True):
 if check_manifest:
  manifest=read(ROOT/'RELEASE_MANIFEST.json')
  for n,h in manifest['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
  declared=set(manifest['files'])|{'RELEASE_MANIFEST.json','SHA256SUMS.txt'}
  actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
  assert actual==declared,dict(extra=sorted(actual-declared),missing=sorted(declared-actual))
  for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
   h,n=line.split('  ',1);assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
 import replay_vi_results_20261114 as replay
 # Explicit replay below preserves status and includes the original residual calculation.
 checks=[]
 entries=read(ROOT/'baseline_audit/state_index.json')
 for p in sorted((ROOT/'baseline/results/vi_cloud_20261114/runs').glob('*/metrics.json')):
  entries.append(dict(path=p.parent.relative_to(ROOT).as_posix(),kind='Root24',stored_status=read(p)['status'],source=p.parent.name))
 for e in entries:
  p=ROOT/e['path'];r=read(p/('audit.json' if e['kind']=='cloud' else 'metrics.json'))
  cfg=r.get('model_config',r.get('config'))
  if cfg is None:cfg=read(p/'config.json')
  m=NestedModel(**cfg) if 'nest_lambda' in cfg else Model(**cfg)
  y=np.load(p/'state.npy',allow_pickle=False);h,v=m.evaluate(y)
  common=[k for k in v if k in r and isinstance(v[k],(int,float))]
  assert len(common)>=(6 if e['kind']=='M01' else 20),(e['source'],common)
  err=max(abs(v[k]-r[k]) for k in common);assert err<1e-6,(e['source'],err)
  direct=float(np.linalg.norm(y-m.project(y-1e-4*h)))
  aux=None
  if (p/'coordinates.npy').exists():
   x=np.load(p/'coordinates.npy',allow_pickle=False);h[:m.nt][m.congest]=m.cap[m.congest]*x[:m.nt][m.congest]-m.last_flows[m.congest]
   aux=float(np.linalg.norm(y-m.project(y-1e-4*h)))
   if 'natural_aux' in r:assert abs(aux-r['natural_aux'])<1e-8,(e['source'],aux,r['natural_aux'])
  if e['kind']=='Root24':
   assert (r['status']=='PASS')==bool(r['strict_original_time_pass'])
   if r['strict_original_time_pass']:
    assert direct<1e-6 and aux<1e-6 and r['full_scaled']<1e-6
    assert r['capacity_violation']<1e-4 and r['complementarity']<1e-3
    assert r['price_audit_gain']<1e-4 and r['finite_difference_error']<1e-5
  if e['kind'] in ['cloud','M03']:assert direct<1e-6 and e['stored_status']=='PASS'
  if 'status' in r:assert r['status']==e['stored_status'],e['source']
  checks.append(dict(source=e['source'],kind=e['kind'],original_status=e['stored_status'],max_economic_error=err,natural_direct=direct,natural_aux=aux))
 # Reconstruct E03 classifications from original state metrics and OD means.
 original=read(ROOT/'baseline_audit/state_index.json')
 amap=next(e for e in original if '/E01/A_no_maas/' in e['source'])
 am=read(ROOT/amap['path']/'metrics.json')
 aod=np.loadtxt(ROOT/amap['path']/'od_results.csv',delimiter=',',skiprows=1)
 for r in rows(ROOT/'sources/e03_all_results_reaudited.csv'):
  e=next(e for e in original if e['source']=='results/research_v6/'+r['run']+'/ROOT_AUX/0')
  assert r['status']==e['stored_status']
  rr=read(ROOT/e['path']/'metrics.json')
  for k in ['profit_mod','profit_pt','profit_maas','traveler_welfare','retail_mod','retail_pt','wholesale_mod','wholesale_pt']:
   assert abs(float(r[k])-rr[k])<1e-6
  if r['status']=='PASS':
   od=np.loadtxt(ROOT/e['path']/'od_results.csv',delimiter=',',skiprows=1)
   assert np.array_equal(od[:,:3],aod[:,:3])
   delta=od[:,7]-aod[:,7]
   gains=[rr['profit_mod']-am['profit_mod'],rr['profit_pt']-am['profit_pt'],rr['profit_maas'],rr['traveler_welfare']-am['traveler_welfare']]
   l1='IMPROVING' if min(gains)>1e-3 else 'NOT_IMPROVING' if min(gains)<-1e-3 else 'ZERO_NEAR_ZERO'
   l2='IMPROVING' if l1=='IMPROVING' and min(delta)>=-1e-8 else 'NOT_IMPROVING'
   assert r['L1']==l1 and r['L2']==l2 and int(r['harmed_od_count'])==int((delta<-1e-8).sum())
 import test_nested
 test_nested.BASE=ROOT;kernel=test_nested.test();assert len(kernel)==18
 f=facts()
 expected=dict(E01_AB=103.29,E01_BC=69.58,E03_total=64,E03_PASS=63,E03_L1=31,E03_L2=14,E03_L1_with_OD_loss=17,M01_total=27,M01_PASS=0,Root_total=24,Root_strict_PASS=21,M02_probes=12)
 comparisons=[]
 for k,v in expected.items():
  tol=.005 if isinstance(v,float) else 0
  assert abs(f[k]-v)<=tol,(k,f[k],v)
  comparisons.append(dict(claim=k,source_value=f[k],spec_value=v,tolerance=tol,status='PASS'))
 for k,v in [('independent_clone',575.18),('split_corrected',0),('actual_B_product_B_fares',113.56)]:assert abs(f['placebo'][k]-v)<.005
 for suffix,profit,welfare,harmed in [('1.00',123.40,103.29,0),('0.55',44.40,26.94,1)]:
  rr=next(r for r in f['cloud'] if r['case']=='B_lambda'+suffix)
  assert abs(rr['profit_maas']-profit)<.005 and abs(rr['welfare_gain']-welfare)<.005 and rr['harmed_od']==harmed
 assert [r['total_h_calls'] for r in f['M03']['results']]==[1490,12309]
 m03=[e for e in entries if e['kind']=='M03'];ys=[np.load(ROOT/e['path']/'state.npy') for e in m03]
 assert np.max(abs(ys[0][-5:]-ys[1][-5:]))<1e-7
 assert f['M01_h_budgets']==[20000]
 if check_manifest:
  assert f==read(ROOT/'baseline_audit/facts.json')
  ledger=rows(ROOT/'CLAIM_LEDGER.csv');allowed={'ORIGINAL_PAPER','REPRODUCED_MECHANISM','NEW_COUNTERFACTUAL','DIAGNOSTIC_ONLY','NOT_IDENTIFIED'}
  fields='claim_id,topic,paper_section,paper_claim,reimplementation_assumption,experiment_id,source_path,git_commit,input_sha256,parameters,observed_result,validation_status,evidence_class,allowed_presentation_wording,caveat'.split(',')
  for r in ledger:
   assert set(fields)<=set(r) and r['evidence_class'] in allowed
   assert hashlib.sha256((ROOT/r['source_path']).read_bytes()).hexdigest()==r['input_sha256']
 return dict(status='PASS_INTEGRITY_AND_SAVED_STATE_REPLAY',replayed_states=len(checks),root_strict_pass=21,root_failed_validation=3,kernel_checks=kernel,numeric_claim_checks=comparisons,checks=checks,facts=f,note='Saved-state audit only. Original failure statuses unchanged. Price-deviation searches are archived validation, not rerun optimizers.')
if __name__=='__main__':print(json.dumps(verify(),indent=2,ensure_ascii=False))
