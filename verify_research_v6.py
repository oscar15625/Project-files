"""Final protected-state, economic identity, and evidence inventory checks."""
from research_experiments import *
def main():
    protected=json.loads((OUT/'G00/protected_hashes.json').read_text())
    assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in protected.items())
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert len(manifest)==76, 'All three E01, nine pilot and 64 coarse attempts must be finalized'
    checks=[]
    for key,record in manifest.items():
        path=ROOT/record['path']; meta=json.loads((path/'configuration.json').read_text())
        assert meta['config_hash']==sha(meta['model_config'])
        if record['status']!='PASS':
            checks.append(dict(run=key,status=record['status'],economic_claim_eligible=False)); continue
        r=json.loads((path/'metrics.json').read_text()); v=json.loads((path/'validation.json').read_text())
        assert r['status']==v['status']=='PASS'
        assert abs(r['profit_pt']-r['retail_pt']-r['wholesale_pt'])<1e-6
        assert abs(r['profit_mod']-r['retail_mod']-r['wholesale_mod'])<1e-6
        assert abs(r['profit_maas']-r['maas_receipts']+r['wholesale_mod']+r['wholesale_pt'])<1e-6
        assert abs(r['social_welfare']-r['traveler_welfare']-r['profit_total'])<1e-6
        od=np.loadtxt(path/'od_results.csv',delimiter=',',skiprows=1,ndmin=2)
        assert abs(od[:,2].sum()-1000)<1e-10
        assert np.max(abs(od[:,4:7].sum(axis=1)-1))<1e-10
        assert abs(od[:,2]@od[:,7]-r['traveler_welfare'])<1e-6
        checks.append(dict(run=key,status='PASS',economic_claim_eligible=True))
    contrasts=list(csv.DictReader((OUT/'E01_contrasts.csv').open(encoding='utf-8-sig')))
    for key in ['profit_mod','profit_pt','profit_maas','traveler_welfare','social_welfare','transfer_flow']:
        assert abs(float(contrasts[0][key])+float(contrasts[1][key])-float(contrasts[2][key]))<1e-7
    files=[p for p in OUT.rglob('*') if p.is_file() and p.suffix in ['.json','.csv','.npy'] and p.name!='final_verification.json']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report=dict(date='2026-11-06',protected_files_unchanged=len(protected),cases=checks,evidence_sha256=hashes)
    write(OUT/'final_verification.json',report)
    print('Verified',len(checks),'runs;',len(protected),'protected files unchanged;',len(hashes),'evidence hashes')
if __name__=='__main__': main()
