"""Evidence integrity, mass/accounting/hitting-probability and solver gate checks."""
from research_v7 import *
import platform,scipy
def rows(name):return list(csv.DictReader((V7/name).open(encoding='utf-8-sig')))
def main():
    hashes=seal();assert len(hashes)==8683
    summary=read(V7/'phase1_status.json');assert (summary['level1'],summary['level2'])==(31,14)
    manifest=read(OUT/'manifest.json');physical=rows('physical_usage.csv');ods=rows('od_usage_and_sales.csv');checks=[]
    for label in sorted({r['run'] for r in physical}):
        p=ROOT/manifest[label]['path'] if label in manifest else ROOT/'results/v4'/label.split('/')[1]
        old=read(p/'metrics.json');m=Model(**old['config']);y=np.load(p/'state.npy');h,r=m.evaluate(y)
        assert max(abs(r[k]-old[k]) for k in r)<1e-6
        local=[x for x in physical if x['run']==label];od=[x for x in ods if x['run']==label]
        assert abs(sum(float(a['demand']) for a in local)-m.total)<1e-6
        assert abs(sum(float(a['maas_sales']) for a in od)-r['maas_receipts'])<1e-6
        for op in ['mod','pt']:
            w=sum(float(a['demand'])*float(a['share'])*float(a['conditional_wholesale_'+op]) for a in od)
            assert abs(w-r['wholesale_'+op])<1e-6
        for a in od:
            assert -1e-9<=float(a['actual_mod_pt_probability'])<=float(a['actual_pt_probability'])+1e-9<=1+2e-9
        for a in local:
            assert float(a['initial_pt_but_no_pt_ride'])<=float(a['initial_pt'])+1e-7
            assert abs(float(a['pt_paid_links'])-float(a['pt_vehicle_link_traversals']))<1e-7
        checks.append(dict(run=label,status='PASS',mass_and_accounting=True))
    strat=rows('strategic_counterfactual.csv');assert len(strat)==18 and all(r['traffic_pass']=='True' for r in strat)
    assert max(abs(float(r['reequilibrated_gain'])) for r in strat if float(r['price_factor'])==1)<1e-6
    # Original failure stays failed despite a separate successful neighbor-start diagnosis.
    failed='E03_coarse/mod_3.5_pt_1.5';assert manifest[failed]['status']=='FAILED_VI'
    assert all(r['status']=='PASS' for r in rows('multistart.csv'))
    diag=[]
    for method in ['PG','EG_FIXED','EG_ADAPT']:
        dest=V7/'M01'/f'{method}_1';meta=read(dest/'metrics.json');assert meta['h_evaluations']==6000 and meta['validation_h_evaluations']==1
        m=Model(**meta['config']);y=np.load(dest/'state.npy');h,r=m.evaluate(y);res=y-m.project(y-1e-4*h)
        assert abs(np.linalg.norm(res)-meta['natural_residual'])<1e-10
        for idx in np.argsort(abs(res))[-8:][::-1]:
            diag.append(dict(method=method,index=int(idx),component='traffic' if idx<m.nt else 'retail_price' if idx>=len(y)-2 else 'maas_fare',natural_component=float(res[idx]),value=float(y[idx]),excess_time=float(y[idx]-m.t0[idx]) if idx<m.nt else None,flow=float(m.last_flows[idx]) if idx<m.nt else None))
    csvout('benchmark_residual_components.csv',diag)
    # Exact duplicate algebra independently checked from saved probability output.
    for r in rows('placebo_od.csv'):
        p=float(r['base_non']);pd=float(r['base_drive']);pn=float(r['non_copy']);pc=float(r['clone_copy']);dv=float(r['drive'])
        assert abs(pn+pc+dv-1)<1e-12
        if r['diagnostic']=='independent_duplicate':assert abs(float(r['delta_logsum'])-np.log1p(p))<1e-12
        else:assert abs(pn+pc-p)<1e-12 and abs(dv-pd)<1e-12 and abs(float(r['delta_logsum']))<1e-12
    meta=dict(date='2026-11-09',python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),processor=platform.processor(),threads={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']},git_sha=gitsha(),baseline_tag='research-handoff-20261108',request_source='notes/V7_REQUEST.txt')
    write(V7/'environment.json',meta)
    source=ROOT.parents[1]/'sources/maas.txt';write(V7/'source_provenance.json',dict(main_paper_text_path=str(source),main_paper_text_sha256=digest(source),tables='2 and 3',algorithm='Equations 23-25 and Algorithm 1',model_sha256=digest(ROOT/'src/model.py')))
    inventory={str(p.relative_to(ROOT)):digest(p) for p in V7.rglob('*') if p.is_file() and p.name!='verification.json'}
    for pattern in ['research_v7*.py','verify_research_v7.py','RESEARCH_V7_*.md','notes/*V7*','output/pdf/MaaS_Research_v7_*.pdf']:
        for p in ROOT.glob(pattern):
            if p.is_file():inventory[str(p.relative_to(ROOT))]=digest(p)
    write(V7/'verification.json',dict(status='PASS',checks=checks,protected_files=len(hashes),traffic_probes=18,original_failure_preserved=True,benchmark_failures_preserved=3,evidence_sha256=inventory))
    print('Verified',len(checks),'physical states; baseline unchanged:',len(hashes),'files; evidence:',len(inventory))
if __name__=='__main__':main()
