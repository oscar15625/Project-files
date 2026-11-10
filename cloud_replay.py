"""Portable, read-only Small-network replay. No optimizer runs by default."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import argparse,csv,hashlib,json,platform,sys,time
ROOT=Path(__file__).resolve().parent
os.chdir(ROOT)
import numpy as np
import scipy
from src.model import Model,inputs

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulate-steps',type=int,default=0,help='Optional NEW diagnostic EG steps, 1..200 only; never a reproduction claim.')
    args=parser.parse_args()
    if not 0<=args.simulate_steps<=200:parser.error('Allowed range is 0..200; extended experiments require a separate registered runner.')
    # Input facts are also supplied as JSON/CSV rather than hidden in Python.
    provided=json.loads((ROOT/'data/small_network.json').read_text())
    rows,lines,ods=inputs('small')
    assert json.loads(json.dumps(dict(roads=rows,pt_lines=lines,ods=ods)))==provided
    index=json.loads((ROOT/'representative_results/index.json').read_text())
    result=[]
    for name in index:
        p=ROOT/'representative_results'/name;r=json.loads((p/'metrics.json').read_text());m=Model(**r['config'])
        y=np.load(p/'state.npy',allow_pickle=False);h,now=m.evaluate(y)
        difference=max(abs(float(now[k])-float(r[k])) for k in now if k in r and isinstance(r[k],(int,float)))
        natural=float(np.linalg.norm(y-m.project(y-1e-4*h)))
        aux=None
        if (p/'coordinates.npy').exists():
            x=np.load(p/'coordinates.npy',allow_pickle=False);ha=h.copy();ha[:m.nt][m.congest]=m.cap[m.congest]*np.maximum(x[:m.nt][m.congest],0)-m.last_flows[m.congest]
            aux=float(np.linalg.norm(y-m.project(y-1e-4*ha)))
        assert difference<1e-6,(name,difference)
        status=index[name]['stored_status']
        if status=='PASS':assert aux is not None and aux<1e-6
        if status=='FAILED_NUMERICAL_CHECK':assert natural>=1e-6
        result.append(dict(case=name,stored_status=status,metric_replay_max_error=difference,natural_direct=natural,natural_aux=aux,state_sha256=sha(p/'state.npy')))
    output=ROOT/'cloud_runs'/time.strftime('%Y%m%d_%H%M%S')
    output.mkdir(parents=True,exist_ok=False)
    report=dict(status='PASS_SAVED_STATE_REPLAY',not_a_new_equilibrium=True,python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),cases=result)
    if args.simulate_steps:
        config=json.loads((ROOT/'representative_results/C_reference/metrics.json').read_text())['config'];m=Model(**config);y=m.initial();tick=time.perf_counter()
        for _ in range(args.simulate_steps):
            h,_=m.evaluate(y);half=m.project(y-1e-4*h);hh,_=m.evaluate(half);y=m.project(y-1e-4*hh)
        h,r=m.evaluate(y);nr=float(np.linalg.norm(y-m.project(y-1e-4*h)))
        report['optional_simulation']=dict(steps=args.simulate_steps,h_calls=2*args.simulate_steps+1,natural_residual=nr,status='DIAGNOSTIC_ONLY_NOT_ACCEPTED_EQUILIBRIUM',seconds=time.perf_counter()-tick)
        np.save(output/'diagnostic_state.npy',y)
    (output/'replay.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    print('Output:',output.relative_to(ROOT))
if __name__=='__main__':main()
