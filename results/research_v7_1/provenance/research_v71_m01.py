"""Isolated-process PG/EG comparison; same numerical contract and counted operator budget."""
from research_v71 import *
import argparse,platform
CASES=['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage']
def worker(case_id,method,factor):
    dest=O/'m01_runs'/f'{case_id}_{method}_{factor:g}';dest.mkdir(parents=True,exist_ok=True)
    if (dest/'metrics.json').exists():return
    m,ref,base=case(case_id);m.optimize_fares=False;y=m.project(m.initial()*factor);budget=20000;step=1e-4
    tick=time.perf_counter();cpu=time.process_time();calls=0;solver_calls=0;peak=memory_rss();trace=[];delta=None;hit=None;reject=0;phase='solver';segments=[]
    protocol=dict(case=case_id,method=method,initial_factor=factor,h_budget=budget,initial_step=step,config=m.config(),config_hash=sha(m.config()),source_state_hash=digest(folder('E01',case_id)/'state.npy'),residual_gamma=1e-4,tolerance=1e-6,evidence_class='DIAGNOSTIC_ONLY',start='project(Model.initial()*factor)',process_id=os.getpid())
    write(dest/'configuration.json',protocol)
    if (dest/'checkpoint.npz').exists():
        cp=np.load(dest/'checkpoint.npz');y=cp['y'];step=float(cp['step']);calls=int(cp['calls']);delta=None
        trace=read(dest/'trace_checkpoint.json');segments=read(dest/'segments.json') if (dest/'segments.json').exists() else [];segments.append(dict(resume_at_calls=calls))
    events=(dest/'operator_evaluations.csv').open('a',newline='',encoding='utf-8');writer=csv.writer(events)
    if events.tell()==0:writer.writerow(['h_call','phase','pumcm_graph_solves','evaluation_seconds','wall_seconds','evidence_class'])
    original=Model.evaluate
    def counted(self,z,details=False):
        nonlocal calls,peak
        begin=time.perf_counter();calls+=1
        try:return original(self,z,details)
        finally:
            peak=max(peak,memory_rss());writer.writerow([calls,phase,sum(len(g) for _,g in self.graphs),time.perf_counter()-begin,time.perf_counter()-tick,'DIAGNOSTIC_ONLY'])
    Model.evaluate=counted
    def H(z):
        if calls>=budget:raise StopIteration
        return m.evaluate(z)[0]
    status='FAILED_NUMERICAL_CHECK';stop_reason='H_BUDGET_EXHAUSTED'
    try:
        while calls<budget:
            h=H(y);nr=float(np.linalg.norm(y-m.project(y-1e-4*h)))
            if delta is not None and delta<1e-6 and hit is None:hit=dict(h_calls=calls,natural_residual=nr,iterate_change=delta)
            if not trace or calls-trace[-1]['h_calls']>=250 or nr<1e-6:
                trace.append(dict(h_calls=calls,natural_residual=nr,iterate_change=delta,step=step,wall_seconds=time.perf_counter()-tick))
                np.savez(dest/'checkpoint.npz',y=y,calls=calls,step=step);write(dest/'trace_checkpoint.json',trace);write(dest/'segments.json',segments);events.flush()
            if nr<1e-6:stop_reason='NATURAL_TOLERANCE_REACHED';break
            half=m.project(y-step*h)
            if method=='PG':new=half
            else:
                hh=H(half)
                if method=='EG_ADAPT':
                    while step*np.linalg.norm(hh-h)>.7*np.linalg.norm(half-y):
                        step*=.5;reject+=1
                        if step<1e-14:stop_reason='MINIMUM_STEP';raise StopIteration
                        half=m.project(y-step*h);hh=H(half)
                new=m.project(y-step*hh)
            delta=float(np.linalg.norm(new-y));y=new
    except StopIteration:pass
    except Exception as exc:
        stop_reason='EXCEPTION';write(dest/'exception.json',dict(error=repr(exc)))
    solver_calls=calls;solver_seconds=time.perf_counter()-tick;phase='validation'
    r,d=metrics(m,y);nr=d['natural_direct']
    # A reference-based root correction is never applied to projection output.
    full_vi=nr<1e-6 and d['scaled']<1e-6 and d['complementarity']<1e-3 and d['capacity_violation']<1e-4
    deviation=None
    if full_vi:
        from scipy.optimize import minimize_scalar
        gains=[]
        for idx,key in [(-2,'profit_mod'),(-1,'profit_pt')]:
            def value(p):
                z=y.copy();z[idx]=p;return m.evaluate(z)[1][key]
            grid=np.linspace(0,max(5,y[idx]*2),101);vals=np.array([value(p) for p in grid]);j=int(vals.argmax());a=grid[max(0,j-1)];b=grid[min(100,j+1)]
            opt=minimize_scalar(lambda p:-value(p),bounds=(a,b),method='bounded');gains.append(max(0,-opt.fun-r[key],vals.max()-r[key]))
        if m.maas:
            z=y.copy();m.optimize_fares=True;val=m.evaluate(z)[1]['profit_maas'];m.optimize_fares=False;gains.append(max(0,val-r['profit_maas']))
        deviation=max(gains);status='PASS' if deviation<1e-4 and d['conservation']<1e-6 and d['accounting']<1e-6 else 'FAILED_NUMERICAL_CHECK'
    row=dict(**protocol,**d,status=status,stop_reason=stop_reason,solver_h_calls=solver_calls,validation_h_calls=calls-solver_calls,total_h_calls=calls,pumcm_calls=calls*sum(len(g) for _,g in m.graphs),solver_seconds=solver_seconds,wall_seconds=time.perf_counter()-tick,cpu_seconds=time.process_time()-cpu,peak_rss_mb=peak/2**20,final_step=step,line_search_rejections=reject,last_iterate_change=delta,first_iterate_tol_hit=hit,deviation_gain=deviation,price_mod=r['price_mod'],price_pt=r['price_pt'],profit_mod=r['profit_mod'],profit_pt=r['profit_pt'],profit_maas=r['profit_maas'],traveler_welfare=r['traveler_welfare'],economic_claim_eligible=status=='PASS',resumed=bool(segments),processor=platform.processor())
    np.save(dest/'state.npy',y);write(dest/'trace.json',trace);write(dest/'metrics.json',row);events.close()
    print(case_id,method,factor,status,stop_reason,nr,flush=True)
def campaign():
    assert read(O/'milestone_A.json')['status']=='PASS'
    for case_id in CASES:
        for factor in [.95,1.,1.05]:
            for method in ['PG','EG_FIXED','EG_ADAPT']:
                dest=O/'m01_runs'/f'{case_id}_{method}_{factor:g}';dest.mkdir(parents=True,exist_ok=True)
                if (dest/'metrics.json').exists():continue
                write(O/'running.json',dict(status='RUNNING',pid=os.getpid(),case=case_id,method=method,factor=factor))
                print('START',case_id,method,factor,flush=True)
                with (dest/'execution.log').open('a',encoding='utf-8') as log:
                    proc=subprocess.run([sys.executable,__file__,'worker','--case',case_id,'--method',method,'--factor',str(factor)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                if proc.returncode:write(dest/'failed_process.json',dict(status='FAILED_NUMERICAL_CHECK',exit_code=proc.returncode))
                existing=[read(p) for p in (O/'m01_runs').glob('*/metrics.json')];outcsv('m01_convergence_runs.csv',existing)
                print('FINISHED',len(existing),flush=True)
    write(O/'running.json',dict(status='FINISHED',pid=os.getpid()))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['campaign','worker']);p.add_argument('--case');p.add_argument('--method');p.add_argument('--factor',type=float,default=1.);a=p.parse_args()
    if a.mode=='worker':worker(a.case,a.method,a.factor)
    else:campaign()
