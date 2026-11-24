"""Read-only manifest and saved-state verification. No optimization or file writes."""
from extension import *
import csv
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def verify(require_manifest=True):
 os.chdir(ROOT);checks=[]
 if require_manifest:
  manifest=read(ROOT/'RELEASE_MANIFEST.json')
  for n,h in manifest['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
  for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines():
   h,n=line.split('  ',1);assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
 prov=read(ROOT/'PROVENANCE.json')
 for n,h in prov['pinned_files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
 for tariff in ['link','flat','zones']:
  for maas in [False,True]:
   case=tariff+('_with_MaaS' if maas else '_without_MaaS');p=ROOT/'input/pt_fare_counterfactual/results';m=make('small',tariff,maas);y=np.load(p/(case+'.npy'),allow_pickle=False);h,r=m.evaluate(y.copy());expected=read(p/(case+'.json'))
   err=max(abs(r[k]-expected[k]) for k in r);natural=float(np.linalg.norm(y-m.project(y-1e-4*h)));assert err<1e-6 and natural<1e-6
   checks.append(dict(case=case,type='Small input',economic_error=err,natural_direct=natural))
 for p in sorted((ROOT/'results').glob('*/metrics.json')):
  old=read(p);m=make('sioux',old['tariff'],old['maas']);m.optimize_fares=False;y=np.load(p.parent/'state.npy',allow_pickle=False);x=np.load(p.parent/'coordinates.npy',allow_pickle=False);h,r=m.evaluate(y.copy(),True)
  err=max(abs(r[k]-old[k]) for k in r);natural=float(np.linalg.norm(y-m.project(y-1e-4*h)));assert err<1e-6 and natural<1e-6,(p.parent.name,err,natural)
  assert old['status']==read(p.parent/'COMPLETE.json')['status']=='STRICT_PASS'
  f=m.last_flows;mask=m.congest;ha=h.copy();ha[:m.nt][mask]=m.cap[mask]*x[:m.nt][mask]-f[mask]
  aux=float(np.linalg.norm(y-m.project(y-1e-4*ha)));assert aux<1e-6 and abs(aux-old['natural_aux'])<1e-8
  cap=float(np.maximum(f[~mask]-m.cap[~mask],0).max());comp=float(np.max(abs((y[:m.nt]-m.t0)[~mask]*(m.cap-f)[~mask])))
  assert cap<1e-4 and comp<1e-3 and abs(r['accounting_error'])<1e-6 and r['flow_conservation_error']<1e-6
  assert np.max(abs(np.asarray(m.last_od)-np.asarray(old['od'])))<1e-6
  assert old['markov_node_balance_error']<1e-6 and old['PT_revenue_error']<1e-6 and old['price_deviation_gain']<1e-4 and old['finite_difference_error']<1e-5
  checks.append(dict(case=p.parent.name,type='Sioux full-demand',economic_error=err,natural_direct=natural,natural_aux=aux))
 assert len(checks)==18
 # Reconstruct every matched comparison from its two saved states.
 with (ROOT/'paired_comparison.csv').open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   a=read(ROOT/'results'/f"{row['tariff']}_A_primary/metrics.json");c=read(ROOT/'results'/f"{row['tariff']}_C_primary/metrics.json")
   for key in ['profit_pt','profit_mod','profit_maas','retail_pt','wholesale_pt','traveler_welfare','social_welfare']:assert abs(float(row['delta_'+key])-(c[key]-a[key]))<1e-6
 # Zero-price invariance is tested again on the full network, not trusted only from logs.
 for maas in [False,True]:
  a=make('sioux','link',maas);b=make('sioux','flat',maas);y=a.initial();y[-1]=0;_,ra=a.evaluate(y.copy());fa=a.last_flows.copy();_,rb=b.evaluate(y.copy())
  assert abs(ra['traveler_welfare']-rb['traveler_welfare'])<1e-6 and np.max(abs(fa-b.last_flows))<1e-6
 return dict(status='PASS_MANIFEST_AND_REPLAY' if require_manifest else 'PASS_SOURCE_REPLAY',saved_states=18,full_network_strict_pass=12,checks=checks,scope='Replays economics/VI and zero-price invariance; archived price-deviation searches are not rerun.')
if __name__=='__main__':print(json.dumps(verify('--source' not in sys.argv),indent=2))
