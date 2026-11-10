"""Finite H-budget benchmark, with checkpoints; no method ranking from failures."""
from research_v7 import *
import platform
def benchmark(method, factor=1.,budget=6000):
    dest=V7/'M01'/f'{method}_{factor:g}';dest.mkdir(parents=True,exist_ok=True)
    if (dest/'metrics.json').exists():return read(dest/'metrics.json')
    m,reference,_=case('C_maas_paper_advantage');m.optimize_fares=False
    y=m.project(m.initial()*factor);calls=0;step=1e-4;trace=[];status='BUDGET_EXHAUSTED';tick=time.perf_counter();cpu=time.process_time();peak=memory_rss();rejects=0
    def H(z):
        nonlocal calls,peak
        if calls>=budget:raise StopIteration
        calls+=1;peak=max(peak,memory_rss());return m.evaluate(z)[0]
    if (dest/'checkpoint.npz').exists():
        cp=np.load(dest/'checkpoint.npz');y=cp['y'];calls=int(cp['calls']);step=float(cp['step'])
        trace=read(dest/'trace_checkpoint.json')
    try:
        while calls<budget:
            h=H(y);nr=float(np.linalg.norm(y-m.project(y-1e-4*h)))
            if not trace or calls-trace[-1]['h_calls']>=100 or nr<1e-6:
                trace.append(dict(h_calls=calls,natural_residual=nr,step=step,wall_seconds=time.perf_counter()-tick))
                np.savez(dest/'checkpoint.npz',y=y,calls=calls,step=step);write(dest/'trace_checkpoint.json',trace)
                print(method,calls,nr,step,flush=True)
            if nr<1e-6:status='PASS_NATURAL_ONLY';break
            half=m.project(y-step*h)
            if method=='PG':y=half;continue
            hh=H(half)
            if method=='EG_ADAPT':
                while step*np.linalg.norm(hh-h)>.7*np.linalg.norm(half-y):
                    step*=.5;rejects+=1
                    if step<1e-14:status='FAILED_LINESEARCH';raise StopIteration
                    half=m.project(y-step*h);hh=H(half)
            y=m.project(y-step*hh)
    except StopIteration:pass
    except Exception as exc:status='FAILED_EXCEPTION';write(dest/'error.json',dict(error=repr(exc)))
    # Separately counted validation H: never included covertly in solver budget.
    h,r=m.evaluate(y);nr=float(np.linalg.norm(y-m.project(y-1e-4*h)))
    flows=m.last_flows;fixed=~m.congest
    caperr=float(np.maximum(flows[fixed]-m.cap[fixed],0).max());comp=float(np.max(abs((y[:m.nt][fixed]-m.t0[fixed])*(m.cap[fixed]-flows[fixed]))))
    if nr<1e-6 and comp<1e-3 and caperr<1e-4:status='PASS_VI_CANDIDATE'
    else:status='FAILED_VI' if status=='PASS_NATURAL_ONLY' else status
    np.save(dest/'state.npy',y)
    r.update(method=method,initial_factor=factor,status=status,natural_residual=nr,capacity_complementarity=comp,capacity_violation=caperr,h_evaluations=calls,validation_h_evaluations=1,pumcm_calls=calls*sum(len(g) for _,g in m.graphs),wall_seconds=time.perf_counter()-tick,cpu_seconds=time.process_time()-cpu,peak_rss_mb=peak/2**20,initial_step=1e-4,final_step=step,line_search_rejections=rejects,h_budget=budget,distance_to_root_reference=float(np.linalg.norm(y-reference)),config=m.config(),cpu=platform.processor(),threads=1,classification='DIAGNOSTIC_ONLY',full_economic_acceptance='NOT_TESTED' if status!='PASS_VI_CANDIDATE' else 'REQUIRES_DEVIATION_AUDIT')
    write(dest/'metrics.json',r);write(dest/'trace.json',trace)
    return r
if __name__=='__main__':
    assert read(V7/'phase1_status.json')['status']=='COMPLETE'
    rows=[]
    for method in ['PG','EG_FIXED','EG_ADAPT']:rows.append(benchmark(method))
    csvout('benchmark_pilot.csv',rows)
    write(V7/'M01_status.json',dict(status='PILOT_COMPLETE',scope='One common cold start, 6000 H evaluations each; no Sioux expansion or universal method ranking',passed=sum(r['status']=='PASS_VI_CANDIDATE' for r in rows)))
