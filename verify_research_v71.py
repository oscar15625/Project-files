"""Independent inventory, event-count, mass, revenue and source-preservation checks."""
from research_v71 import *
import platform
def main():
    seal=seal71();assert len(csvread(O/'paper_defense_ledger.csv'))==21
    baseline=csvread(O/'g00_recomputed_states.csv');assert len(baseline)==76 and sum(r['status']=='PASS' for r in baseline)==75
    static=csvread(O/'e01_placebo_static.csv')
    for r in static:assert abs(sum(float(r[k]) for k in ['share_non','share_drive','share_maas'])-1)<1e-12
    tests=csvread(O/'e01_invariance_unit_tests.csv');assert len(tests)==12 and all(r['status']=='PASS' for r in tests)
    original=read(OUT/'manifest.json');phys=csvread(O/'pt_physical_flow_vs_sales_channel.csv');ods=csvread(O/'pt_od_event_probabilities.csv')
    for run in {r['run'] for r in phys}:
        p=ROOT/original[run]['path'] if run in original else ROOT/'results/v4'/run.split('/')[1]
        r=read(p/'metrics.json');m=Model(**r['config']);group=[a for a in phys if a['run']==run];od=[a for a in ods if a['run']==run]
        assert abs(sum(float(a['demand']) for a in group)-m.total)<1e-6
        assert abs(sum(float(a['maas_sales']) for a in od)-r['maas_receipts'])<1e-6
        for a in group:
            assert float(a['any_actual_pt_trips'])<=float(a['pt_vehicle_link_traversals'])+1e-7
            assert float(a['actual_mod_and_pt_trips'])<=float(a['any_actual_pt_trips'])+1e-7
            assert float(a['initial_pt_but_no_pt_ride'])<=float(a['initial_pt'])+1e-7
        for op in ['mod','pt']:
            assert abs(sum(float(a['demand'])*float(a['share'])*float(a['conditional_wholesale_'+op]) for a in od)-r['wholesale_'+op])<1e-6
    economic=csvread(O/'e03_all_results_reaudited.csv');assert len(economic)==64
    assert sum(r['L1']=='IMPROVING' for r in economic)==31 and sum(r['L2']=='IMPROVING' for r in economic)==14
    for r in economic:
        assert r['L3']=='NOT_IDENTIFIED'
        for op in ['mod','pt']:assert abs(float(r['delta_profit_'+op])-float(r['delta_retail_'+op])-float(r['wholesale_'+op]))<1e-6
    bench=csvread(O/'m01_convergence_runs.csv');assert len(bench)==27
    assert len({(r['case'],r['method'],r['initial_factor']) for r in bench})==27
    operator_summary=[]
    for p in sorted((O/'m01_runs').glob('*/metrics.json')):
        r=read(p);ev=csvread(p.parent/'operator_evaluations.csv');assert len(ev)==r['total_h_calls']
        assert sum(int(x['pumcm_graph_solves']) for x in ev)==r['pumcm_calls']
        assert r['solver_h_calls']<=20000
        m=Model(**r['config']);y=np.load(p.parent/'state.npy');current,d=metrics(m,y)
        assert abs(d['natural_direct']-r['natural_direct'])<1e-10
        assert (r['status']=='PASS')==r['economic_claim_eligible']
        operator_summary.append(dict(run=p.parent.name,h_solver=r['solver_h_calls'],h_validation=r['validation_h_calls'],h_total=r['total_h_calls'],pumcm_total=r['pumcm_calls'],operator_seconds=sum(float(x['evaluation_seconds']) for x in ev),status=r['status'],evidence_class='DIAGNOSTIC_ONLY' if r['status']=='PASS' else 'FAILED_NUMERICAL_CHECK'))
        if r['status']!='PASS':write(O/'failed_runs'/f'm01_{p.parent.name}.json',dict(source=str(p.parent.relative_to(ROOT)),status=r['status'],stop_reason=r['stop_reason'],natural=r['natural_direct'],economic_claim_eligible=False,evidence_class='FAILED_NUMERICAL_CHECK'))
    outcsv('m01_operator_evaluations.csv',operator_summary)
    probes=csvread(O/'m02_timing_comparison.csv');assert len(probes)==12
    for r in probes:
        if float(r['price_factor'])==1:assert abs(float(r['reequilibrated_gain']))<1e-6
    edge=csvread(O/'e03_local_boundary.csv');assert len(edge)==9
    nested=csvread(O/'m03_same_vi_prototype.csv');assert len(nested)==2
    for r in nested:
        if r['status']=='INTERRUPTED_NOT_COMPLETED':
            assert not (O/'m03_runs'/r['method']/'metrics.json').exists()
            continue
        p=O/'m03_runs'/r['method'];meta=read(p/'metrics.json');m=Model(**meta['config']);current,d=metrics(m,np.load(p/'state.npy'),np.load(p/'coordinates.npy'))
        assert max(abs(current[k]-meta[k]) for k in current)<1e-6
        if r['status']=='PASS':assert d['natural_aux']<1e-6 and meta['full_scaled']<1e-6
    write(O/'environment.json',dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),numpy=np.__version__,thread_variables={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']},git_sha_at_verification=gitsha(),execution_version_archive='provenance/',main_paper_text_hash=digest(ROOT.parents[1]/'sources/maas.txt')))
    micro=csvread(O/'m01_boundary_microtest.csv');assert len(micro)==15
    assert all(float(r['iterate_change'])==0 and float(r['natural_residual'])>1e-6 for r in micro if float(r['fixed_flow'])==0)
    files=[p for p in O.rglob('*') if p.is_file() and p not in [O/'validation.json',O/'manifest.json']]
    hashes={str(p.relative_to(ROOT)):digest(p) for p in files}
    hashes.update({str(p.relative_to(ROOT)):digest(p) for p in ROOT.glob('*v71*.py')})
    write(O/'manifest.json',dict(date='2026-11-10',source_tag='research-handoff-20261108',active_branch='research-v7-1-critical-validation',evidence_sha256=hashes,completed=['R00','G00-G02','E01-P static','E02-PT','E03-D/V','M01 27 attempts','M02 12 probes','M03 JOINT_AUX only','boundary scalar diagnostic'],not_run=['M01 Sioux and additional contracts','Phase C market extensions','E01-P re-equilibrated clone'],interrupted=['M03 NESTED_SAME_VI: no final state; not resumed under user low-compute scope'],old_source_files=len(seal)))
    write(O/'validation.json',dict(status='PASS_INTEGRITY_AND_REPORTING',source_files_unchanged=len(seal),m01_attempts=27,m01_accepted=sum(r['status']=='PASS' for r in bench),m03_status={r['method']:r['status'] for r in nested},original_failure_preserved=read(OUT/'manifest.json')['E03_coarse/mod_3.5_pt_1.5']['status']=='FAILED_VI',evidence_files=len(hashes),checks='hashes, source metric replay, mass, probabilities, revenue transfers, complete operator call counts, raw final residuals; numerical experiment failures remain failures'))
    print('v7.1 integrity PASS;',len(seal),'old files unchanged;',len(hashes),'evidence files;',sum(r['status']=='PASS' for r in bench),'/27 M01 accepted')
if __name__=='__main__':main()
