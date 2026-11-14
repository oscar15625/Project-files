"""Read-only cloud archive audit, isolated local output."""
from research_v71 import *
import importlib.util
P=ROOT/'results/vi_cloud_20261114'
CLOUD=ROOT.parents[1]/'MaaS_Cloud_Nested_Choice_v8_20261110/new_results'
PLAN=ROOT.parents[1]/'MaaS_Cloud_Replay_Audit_and_Plan_20261110'
def loadmodule(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
    P.mkdir(parents=True,exist_ok=True)
    seal={str(p):digest(p) for d in [CLOUD,PLAN] for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    write(P/'cloud_input_hashes.json',seal)
    declared=read(CLOUD/'PACKAGE_MANIFEST.json');bad=[r['path'] for r in declared['files'] if digest(CLOUD/r['path'])!=r['sha256']];assert not bad,bad
    for n in ['nested_extension.py','nested_solver.py','test_nested.py','verify_nested_archive.py']:
        dest=P/'sources'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(CLOUD/n,dest)
    sys.path.insert(0,str(P/'sources'))
    from nested_extension import NestedModel
    from nested_solver import residual
    test=loadmodule('cloud_kernel_tests',P/'sources/test_nested.py');test.BASE=ROOT/'backups/v71_delivery_20261110_r2/portable_smoke'
    tests=test.test();assert len(tests)==18
    write(P/'kernel_tests.json',tests)
    replay=[]
    for p in sorted((CLOUD/'audited').glob('*_lambda*')):
        old=read(p/'audit.json');cfg=read(CLOUD/'experiments'/old['case']/'config.json');cfg.pop('source_reference')
        m=NestedModel(**cfg);y=np.load(p/'state.npy');x=np.load(p/'coordinates.npy');h,r=m.evaluate(y,True);flow=m.last_flows.copy()
        err=max(abs(r[k]-old[k]) for k in r if k in old);fs=float(np.linalg.norm(residual(m,x)))
        hc=h.copy();hc[:m.nt][m.congest]=m.cap[m.congest]*x[:m.nt][m.congest]-flow[m.congest]
        aux=float(np.linalg.norm(y-m.project(y-1e-4*hc)));direct=float(np.linalg.norm(y-m.project(y-1e-4*h)))
        cap=float(np.maximum(flow[~m.congest]-m.cap[~m.congest],0).max());comp=float(np.max(abs((y[:m.nt]-m.t0)[~m.congest]*(m.cap-flow)[~m.congest])))
        assert err<1e-6 and fs<1e-6 and aux<1e-6 and cap<1e-4 and comp<1e-3,(p,err,fs,aux)
        # Repeat every archived finite price probe, without changing the source states.
        gain=0
        for i,key in [(-2,'profit_mod'),(-1,'profit_pt')]+[(m.nt+j,'profit_maas') for j in range(m.nod)]:
            for delta in [-.2,-.05,.05,.2]:
                z=y.copy();z[i]+=delta
                if z[i]<0:continue
                gain=max(gain,m.evaluate(z)[1][key]-r[key])
        assert gain<1e-4
        dst=P/'cloud_reference'/p.name;dst.mkdir(parents=True,exist_ok=True)
        for n in ['state.npy','coordinates.npy','audit.json']:shutil.copy2(p/n,dst/n)
        write(dst/'config.json',cfg)
        replay.append(dict(case=p.name,status='PASS_ARCHIVED_CRITERIA',max_metric_error=err,full_scaled=fs,natural_aux=aux,natural_direct=direct,capacity=cap,complementarity=comp,finite_local_deviation_gain=gain,config=cfg))
    assert len(replay)==10
    assert all(digest(Path(p))==h for p,h in seal.items())
    write(P/'cloud_replay.json',replay)
    # Cloud plan calls the last-two retail-price difference the maximum price difference.
    a=np.load(O/'m03_runs/JOINT_AUX/state.npy');b=np.load(O/'m03_followup_20261110/NESTED_SAME_VI_attempt2/state.npy');m=Model(**read(O/'m03_runs/JOINT_AUX/metrics.json')['config'])
    write(P/'audit_status.json',dict(status='PASS_MODEL_AND_SAVED_STATES',declared_file_hashes=len(declared['files']),kernel_tests=len(tests),saved_states=len(replay),original_inputs_unchanged=True,qualification='Cloud price audit is local finite deviations, not global Nash proof. Additional broadened audits will be applied to new solver outputs.',plan_correction=dict(retail_price_max_difference=float(np.max(abs(a[-2:]-b[-2:]))),all_prices_max_difference=float(np.max(abs(a[m.nt:]-b[m.nt:]))),issue='Plan 2.66e-9 refers only to retail prices; all prices including MaaS fares differ by 4.01e-8. Not a model error.')))
    print('CLOUD AUDIT PASS:',len(tests),'kernel tests;',len(replay),'states;',len(seal),'input files unchanged')
if __name__=='__main__':main()
