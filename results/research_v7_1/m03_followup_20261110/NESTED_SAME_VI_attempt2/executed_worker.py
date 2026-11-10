def run_nested(method):
    dest=DEST;dest.mkdir(parents=True,exist_ok=True)
    if (dest/'metrics.json').exists():return
    old=read(folder('E03_coarse','mod_1.5_pt_1.5')/'metrics.json');m=Model(**old['config']);m.optimize_fares=False
    ref=np.load(folder('E03_coarse','mod_1.5_pt_1.5')/'state.npy');xc=np.load(folder('E03_coarse','mod_1.5_pt_1.5')/'coordinates.npy');mask=m.congest
    x0=np.r_[xc[:m.nt],ref[m.nt:]*1.03];lo=np.r_[np.where(mask,0,m.t0),np.zeros(len(x0)-m.nt)];calls=0;inners=0;inner_fail=0;peak=memory_rss();tick=time.perf_counter();cpu=time.process_time()
    write(dest/'configuration.json',dict(method=method,config=m.config(),start='original reference with all prices multiplied by 1.03',inner_max_nfev=100,outer_max_nfev=50,outer_diff_step=1e-4,numerical_protocol='identical to original nested_worker; output and progress instrumentation only',previous_attempt='m03_runs/NESTED_SAME_VI',joint_reused='m03_runs/JOINT_AUX',original_source_sha256=digest(ROOT/'research_v71_extra.py')))
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
        np.save(dest/'last_inner_coordinates.npy',xx)
        write(dest/'last_inner.json',dict(inner_solves=inners,inner_failures=inner_fail,h_calls=extra[0],pumcm_calls=graph_calls[0],seconds=time.perf_counter()-tick,prices=p.tolist(),checkpoint_scope='last completed inner solve; not a restartable scipy outer-optimizer state'))
        print('INNER',inners,'H',extra[0],'failures',inner_fail,flush=True)
        return xx
    # Count all evaluations, including boundary cleanup and final diagnostics.
    original=Model.evaluate;extra=[0]
    from src.model import Graph
    old_graph_solve=Graph.solve;graph_calls=[0]
    def count_graph(self,*args,**kwargs):
        graph_calls[0]+=1;return old_graph_solve(self,*args,**kwargs)
    Graph.solve=count_graph
    def count(self,y,details=False):
        extra[0]+=1
        if extra[0]%5000==0:
            write(dest/'progress.json',dict(status='RUNNING',h_calls=extra[0],inner_solves=inners,inner_failures=inner_fail,seconds=time.perf_counter()-tick,pid=os.getpid()))
            print('PROGRESS',extra[0],inners,flush=True)
        return original(self,y,details)
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
