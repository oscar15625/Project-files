"""Registered local wholesale cases and same-VI nested numerical prototype."""
from research_v71 import *
from scipy.optimize import least_squares
def edges():
    base=read(folder('E01','A_no_maas')/'metrics.json');baseod=np.loadtxt(folder('E01','A_no_maas')/'od_results.csv',delimiter=',',skiprows=1)
    records=[]
    for cm in [1.4,1.5,1.6]:
        for cp in [.7,.8,.9]:
            dest=O/'e03_edge_cases'/f'mod_{cm:g}_pt_{cp:g}';dest.mkdir(parents=True,exist_ok=True)
            if (dest/'validation.json').exists():r=read(dest/'metrics.json');v=read(dest/'validation.json')
            else:
                m=Model(**config(wholesale=(cm,cp)));start=np.load(folder('E03_coarse','mod_1.5_pt_1')/'state.npy')
                write(dest/'configuration.json',dict(config=m.config(),start_source='research_v6/E03_coarse/mod_1.5_pt_1',evidence_class='NEW_COUNTERFACTUAL',registered_grid=[1.4,1.5,1.6,.7,.8,.9]))
                y,r=refine(m,str(dest.relative_to(ROOT/'results')),start,maxiter=100)
                raw=dest/'raw_solver';raw.mkdir(exist_ok=True)
                for name in ['metrics.json','state.npy','coordinates.npy']:shutil.copy2(dest/name,raw/name)
                x=np.load(dest/'coordinates.npy');y,x,c=polish(m,y,x);r.update(c);write(dest/'metrics.json',r);np.save(dest/'state.npy',y);np.save(dest/'coordinates.npy',x)
                v=validate(dest,r,y,x);r.update(v);write(dest/'metrics.json',r)
            row=dict(c_mod=cm,c_pt=cp,status=v['status'],delta_mod=r['profit_mod']-base['profit_mod'],delta_pt=r['profit_pt']-base['profit_pt'],platform_profit=r['profit_maas'],delta_welfare=r['traveler_welfare']-base['traveler_welfare'],natural_aux=r['natural_residual'],scaled=r['scaled_residual'],evidence_class='NEW_COUNTERFACTUAL' if v['status']=='PASS' else 'FAILED_NUMERICAL_CHECK')
            od=np.loadtxt(dest/'od_results.csv',delimiter=',',skiprows=1);harm=int(((od[:,7]-baseod[:,7])<-1e-8).sum());row['harmed_od_count']=harm
            row['L1']=v['status']=='PASS' and min(row[k] for k in ['delta_mod','delta_pt','platform_profit','delta_welfare'])>1e-3;row['L2']=row['L1'] and harm==0;records.append(row);outcsv('e03_local_boundary.csv',records)
    # Revalidate the separate v7 neighbor-start diagnostic without touching it.
    p=V7/'multistart/mod_3.5_pt_1.5_1';old=read(p/'metrics.json');m=Model(**old['config']);r,d=metrics(m,np.load(p/'state.npy'),np.load(p/'coordinates.npy'))
    write(O/'e03_failed_point_diagnosis.json',dict(original_status='FAILED_VI',diagnostic_source=str(p.relative_to(ROOT)),diagnostic_status=old['status'],recomputed=d,evidence_class='DIAGNOSTIC_ONLY',original_grid_replaced=False))
def nested_worker(method):
    dest=O/'m03_runs'/method;dest.mkdir(parents=True,exist_ok=True)
    if (dest/'metrics.json').exists():return
    old=read(folder('E03_coarse','mod_1.5_pt_1.5')/'metrics.json');m=Model(**old['config']);m.optimize_fares=False
    ref=np.load(folder('E03_coarse','mod_1.5_pt_1.5')/'state.npy');xc=np.load(folder('E03_coarse','mod_1.5_pt_1.5')/'coordinates.npy');mask=m.congest
    x0=np.r_[xc[:m.nt],ref[m.nt:]*1.03];lo=np.r_[np.where(mask,0,m.t0),np.zeros(len(x0)-m.nt)];calls=0;inners=0;inner_fail=0;peak=memory_rss();tick=time.perf_counter();cpu=time.process_time()
    def decode(x):
        y=x.copy();y[:m.nt][mask]=m.t0[mask]*(1+.15*np.maximum(x[:m.nt][mask],0)**4);return y
    def residual(x):
        nonlocal calls,peak
        calls+=1;peak=max(peak,memory_rss());y=decode(x);h,r=m.evaluate(y);f=m.last_flows.copy();v=h.copy()
        v[:m.nt][mask]=x[:m.nt][mask]-f[mask]/m.cap[mask]
        v[:m.nt][~mask]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~mask]
        if m.maas:v[m.nt:-2]=y[m.nt:-2]-np.maximum(0,y[m.nt:-2]-h[m.nt:-2]/m.ods[:,2])
        v[-2:]=y[-2:]-np.maximum(0,y[-2:]-h[-2:]/np.maximum(m.retail_volume,1e-8));return v
    def inner(p):
        nonlocal inners,inner_fail
        inners+=1
        def fun(t):return residual(np.r_[t,p])[:m.nt]
        opt=least_squares(fun,np.maximum(x0[:m.nt],lo[:m.nt]+1e-8),bounds=(lo[:m.nt],np.full(m.nt,200.)),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=100)
        xx=np.r_[opt.x,p];y=decode(xx);m.evaluate(y);f=m.last_flows
        sel=(~mask)&(xx[:m.nt]-m.t0<1e-6)&(m.cap-f>1e-3);xx[:m.nt][sel]=m.t0[sel]
        if np.linalg.norm(residual(xx)[:m.nt])>=1e-6:inner_fail+=1
        return xx
    # Count all evaluations, including boundary cleanup and final diagnostics.
    original=Model.evaluate;extra=[0]
    from src.model import Graph
    old_graph_solve=Graph.solve;graph_calls=[0]
    def count_graph(self,*args,**kwargs):
        graph_calls[0]+=1;return old_graph_solve(self,*args,**kwargs)
    Graph.solve=count_graph
    def count(self,y,details=False):extra[0]+=1;return original(self,y,details)
    Model.evaluate=count
    if method=='JOINT_AUX':
        opt=least_squares(residual,np.maximum(x0,lo+1e-8),bounds=(lo,np.full(len(x0),200.)),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=100);x=opt.x
    else:
        def outer(p):return residual(inner(p))[m.nt:]
        opt=least_squares(outer,x0[m.nt:],bounds=(np.zeros(len(x0)-m.nt),np.full(len(x0)-m.nt,200.)),diff_step=1e-4,xtol=1e-10,ftol=1e-10,gtol=1e-10,max_nfev=50);x=inner(opt.x)
    y=decode(x);m.evaluate(y);f=m.last_flows.copy();sel=(~mask)&(y[:m.nt]-m.t0<1e-6)&(m.cap-f>1e-3);x[:m.nt][sel]=m.t0[sel];y=decode(x)
    r,d=metrics(m,y,x);fullscaled=float(np.linalg.norm(residual(x)))
    np.save(dest/'state.npy',y);np.save(dest/'coordinates.npy',x)
    r.update(config=m.config(),natural_residual=d['natural_aux'],scaled_residual=fullscaled);write(dest/'metrics.json',r)
    validation=validate(dest,r,y,x)
    r.update(validation,method=method,full_scaled=fullscaled,total_h_calls=extra[0],residual_calls=calls,inner_solves=inners,inner_failures=inner_fail,seconds=time.perf_counter()-tick,cpu_seconds=time.process_time()-cpu,peak_rss_mb=peak/2**20,source_start='same reference state with every fare and retail price increased 3%',evidence_class='DIAGNOSTIC_ONLY',same_game='Original fixed-time partial price residual; inner root sensitivity is a numerical derivative, not profit total derivative',status=validation['status'] if fullscaled<1e-6 and inner_fail==0 else 'FAILED_NUMERICAL_CHECK')
    # validate() uses other Model instances; all calls are counted by the class wrapper.
    r['total_h_calls']=extra[0];r['total_pumcm_calls']=graph_calls[0];write(dest/'metrics.json',r)
def main():
    edges()
    from research_v7_stability import traffic
    probes=[]
    for tag in ['mod_1.5_pt_1.5','mod_3_pt_3']:
        p=folder('E03_coarse',tag);old=read(p/'metrics.json');m=Model(**old['config']);base=np.load(p/'state.npy');x=np.load(p/'coordinates.npy')[:m.nt]
        for op,idx in [('mod',-2),('pt',-1)]:
            for factor in [.95,1.,1.05]:
                dest=O/'m02_runs'/f'{tag}_{op}_{factor:g}';dest.mkdir(parents=True,exist_ok=True)
                y=base.copy();y[idx]*=factor;fixed=m.evaluate(y)[1]
                if (dest/'metrics.json').exists():r=read(dest/'metrics.json')
                else:
                    z,r=traffic(m,y,x);r.update(config=m.config(),source=str(p.relative_to(ROOT)),price_factor=factor,operator=op,evidence_class='NEW_COUNTERFACTUAL');np.save(dest/'state.npy',z);write(dest/'metrics.json',r)
                probes.append(dict(scenario=tag,operator=op,price_factor=factor,fixed_time_gain=fixed['profit_'+op]-old['profit_'+op],reequilibrated_gain=r['profit_'+op]-old['profit_'+op],traffic_status='PASS' if r['traffic_pass'] else 'FAILED_NUMERICAL_CHECK',natural_aux=r['traffic_natural_aux'],scaled=r['traffic_scaled'],evidence_class='NEW_COUNTERFACTUAL',scope='Finite price probe, not global best response; fixed rival retail and MaaS fares'))
    outcsv('m02_timing_comparison.csv',probes)
    for method in ['JOINT_AUX','NESTED_SAME_VI']:
        p=O/'m03_runs'/method;p.mkdir(parents=True,exist_ok=True)
        with (p/'execution.log').open('a',encoding='utf-8') as f:subprocess.run([sys.executable,__file__,method],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    outcsv('m03_same_vi_prototype.csv',[read(O/'m03_runs'/m/'metrics.json') for m in ['JOINT_AUX','NESTED_SAME_VI']])
if __name__=='__main__':
    if len(sys.argv)>1:nested_worker(sys.argv[1])
    else:main()
