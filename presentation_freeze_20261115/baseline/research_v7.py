"""Read-only v6 re-evaluation and v7 behavioral/physical diagnostics."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[key]='1'
from research_experiments import *
from scipy.sparse import csc_matrix,eye
from scipy.sparse.linalg import spsolve
V7=ROOT/'results/research_v7'; V7.mkdir(parents=True,exist_ok=True)
def csvout(name,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (V7/name).open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seal():
    dest=V7/'baseline_hashes.json'
    if dest.exists():
        hashes=read(dest); assert all(digest(ROOT/k)==v for k,v in hashes.items());return hashes
    paths=[ROOT/'src/model.py']+[p for d in ['results/v4','results/v5','results/research_v6'] for p in (ROOT/d).rglob('*') if p.is_file()]
    hashes={str(p.relative_to(ROOT)):digest(p) for p in paths};write(dest,hashes)
    return hashes
def baseline():
    hashes=seal(); prior=read(OUT/'final_verification.json')
    for k,v in prior['evidence_sha256'].items():assert digest(ROOT/k)==v,k
    for k,v in read(OUT/'G00/protected_hashes.json').items():assert digest(ROOT/k)==v,k
    rows=[]
    for key,rec in read(OUT/'manifest.json').items():
        p=ROOT/rec['path'];r=read(p/'metrics.json');meta=read(p/'configuration.json')
        assert sha(meta['model_config'])==meta['config_hash']
        if rec['status']!='PASS':rows.append(dict(run=key,status=rec['status'],rechecked=False));continue
        m=Model(**r['config']);y=np.load(p/'state.npy');h,new=m.evaluate(y)
        err=max(abs(new[k]-r[k]) for k in new);nr=float(np.linalg.norm(y-m.project(y-1e-4*h)))
        assert err<1e-6,(key,err,nr)
        x=np.load(p/'coordinates.npy');hc=h.copy()
        hc[:m.nt][m.congest]=m.cap[m.congest]*np.maximum(x[:m.nt][m.congest],0)-m.last_flows[m.congest]
        coordnr=float(np.linalg.norm(y-m.project(y-1e-4*hc)))
        time_roundtrip=float(np.max(abs(y[:m.nt][m.congest]-m.t0[m.congest]*(1+.15*np.maximum(x[:m.nt][m.congest],0)**4))))
        forward=float(np.max(abs(y[:m.nt][m.congest]-m.t0[m.congest]*(1+.15*(m.last_flows[m.congest]/m.cap[m.congest])**4))))
        assert coordnr<1e-6 and forward<1e-6
        v=read(p/'validation.json');assert v['capacity_complementarity']<1e-3
        rows.append(dict(run=key,status='PASS_AUX_COORDINATES',rechecked=True,max_metric_difference=err,natural_residual_direct=nr,natural_residual_aux=coordnr,direct_threshold_pass=nr<1e-6,forward_bpr_time_error=forward,coordinate_time_roundtrip=time_roundtrip))
    csvout('baseline_recheck.csv',rows);write(V7/'baseline_status.json',dict(protected_files=len(hashes),prior_evidence=len(prior['evidence_sha256']),passes=sum(r['rechecked'] for r in rows),failed_preserved=1))
def case(tag):
    p=folder('E01',tag);r=read(p/'metrics.json');return Model(**r['config']),np.load(p/'state.npy'),r
def placebo():
    m,y,r=case('A_no_maas');m.evaluate(y,True);od=np.array(m.last_od);rows=[]
    for o,d,q,f,pn,pd,pm,v,wm,wp in od:
        for label,w in [('independent_duplicate',2.),('split_corrected',1.),('perfectly_correlated_clone',1.)]:
            denom=1+(w-1)*pn;delta=m.mode_theta*np.log(denom)
            # Correlated clone uses an explicitly equal allocation of its unchanged class probability.
            pcopy=pn*w/(2*denom)
            rows.append(dict(origin=int(o),destination=int(d),demand=q,diagnostic=label,base_non=pn,base_drive=pd,non_copy=pcopy,clone_copy=pcopy,drive=pd/denom,combined_service=2*pcopy,delta_logsum=delta,weighted_delta=q*delta,utility_adjustment_each=-m.mode_theta*np.log(2) if label=='split_corrected' else 0,classification='DIAGNOSTIC_ONLY'))
            assert abs(2*pcopy+pd/denom-1)<1e-12
            if w==1:assert abs(delta)<1e-12 and abs(2*pcopy-pn)<1e-12
    csvout('placebo_od.csv',rows)
    write(V7/'placebo_summary.json',{lab:dict(welfare_gain=sum(a['weighted_delta'] for a in rows if a['diagnostic']==lab),clone_share_pct=100*sum(a['demand']*a['clone_copy'] for a in rows if a['diagnostic']==lab)/m.total) for lab in sorted({a['diagnostic'] for a in rows})})
def physical(m,y,label):
    records=[];odrecords=[];edges=[]
    roadlength={(i,j):length for i,j,length,cap,t in m.rows}
    for ids,group in m.graphs:
        sols=[g.solve(y[:m.nt],y[-2:],m.wholesale,k) for k,g in group.items()];kinds=list(group)
        values=np.array([s[0]-(m.fixed if k=='drive' else y[m.nt+ids] if k=='maas' else 0) for k,s in zip(kinds,sols)]).T
        shares=np.exp(values/m.mode_theta-logsumexp(values/m.mode_theta,axis=1)[:,None])
        for b,(kind,g) in enumerate(group.items()):
            load=sols[b][4];q=m.ods[ids,2]*shares[:,b];flow=load(q)
            ridept=np.array([isinstance(s[0],int) and s[0]==d[0] for s,d in g.edge_labels]);ridem=np.array([s[0]=='M' and d[0]=='M' for s,d in g.edge_labels])
            lengths=np.array([roadlength.get((s[1],d[1]),roadlength.get((d[1],s[1]),0)) if ridept[e] or ridem[e] else 0 for e,(s,d) in enumerate(g.edge_labels)])
            boardpt=np.array([isinstance(d[0],int) and s[0]!=d[0] for s,d in g.edge_labels])
            # Recover the Markov transition kernel; all origins receive positive injection.
            unit=load(np.ones(len(ids)));visits=np.bincount(g.i,weights=unit,minlength=g.n)
            prob=np.divide(unit,visits[g.i],out=np.zeros_like(unit),where=visits[g.i]>0)
            def avoid(mask):
                keep=g.internal & ~mask
                P=csc_matrix((prob[keep],(g.i[keep],g.j[keep])),shape=(g.n,g.n))
                term=~g.internal & ~mask
                rhs=np.bincount(g.i[term],weights=prob[term],minlength=g.n)
                return spsolve(eye(g.n,format='csc')-P,rhs)
            ap=avoid(ridept);am=avoid(ridem);ab=avoid(ridept|ridem)
            anypt=1-ap[g.gates];both=1-ap[g.gates]-am[g.gates]+ab[g.gates]
            no_ride_after_pt_gate=np.bincount(g.i[g.board_pt],weights=prob[g.board_pt]*ap[g.j[g.board_pt]],minlength=g.n)[g.gates]
            assert min(anypt.min(),both.min())>-1e-9 and max(anypt.max(),both.max())<1+1e-9
            rec=dict(run=label,network=m.name,kind=kind,demand=float(q.sum()),initial_pt=float(flow[g.board_pt].sum()),pt_vehicle_link_traversals=float(flow[ridept].sum()),pt_boarding_events=float(flow[boardpt].sum()),pt_pt_transfers=float(flow[g.pt_transfer].sum()),pt_paid_links=float(flow@g.attr[:,3]) if kind=='non' else float(flow@g.attr[:,5]) if kind=='maas' else 0,pt_passenger_distance_model_units=float(flow[ridept]@lengths[ridept]),mod_vehicle_link_traversals=float(flow[ridem].sum()) if kind!='drive' else 0,any_actual_pt_trips=float(q@anypt),actual_mod_and_pt_trips=float(q@both) if kind!='drive' else 0)
            assert abs(rec['pt_vehicle_link_traversals']-rec['pt_paid_links'])<1e-7
            rec['destination']=int(m.ods[ids[0],1]);rec['initial_pt_but_no_pt_ride']=float(q@no_ride_after_pt_gate)
            assert rec['any_actual_pt_trips']<=rec['pt_vehicle_link_traversals']+1e-7
            assert rec['actual_mod_and_pt_trips']<=rec['any_actual_pt_trips']+1e-7
            records.append(rec)
            for local,idx in enumerate(ids):
                o,d,dem=m.ods[idx];fare=y[m.nt+idx] if kind=='maas' else 0
                odrecords.append(dict(run=label,origin=int(o),destination=int(d),kind=kind,demand=dem,share=shares[local,b],actual_pt_probability=anypt[local],actual_mod_pt_probability=both[local] if kind!='drive' else 0,maas_sales=dem*shares[local,b]*fare,conditional_wholesale_mod=sols[b][1][local,0] if kind=='maas' else 0,conditional_wholesale_pt=sols[b][1][local,1] if kind=='maas' else 0))
            for e,(s,d) in enumerate(g.edge_labels):
                edges.append(dict(run=label,destination=int(m.ods[ids[0],1]),kind=kind,source=str(s),target=str(d),flow=flow[e],pt_ride=bool(ridept[e]),mod_ride=bool(ridem[e]),resource=int(g.res[e])))
    return records,odrecords,edges
def phase1():
    baseline();placebo();allphys=[];allod=[];alledges=[];econ=[]
    source=[(key,ROOT/rec['path']) for key,rec in read(OUT/'manifest.json').items() if key.startswith(('E01/','E03_coarse/')) and rec['status']=='PASS']
    source += [('V5/'+tag,ROOT/'results/v4'/tag) for tag in ['sioux_node_node_total0_without','sioux_node_node_total0_with']]
    for key,p in source:
        r=read(p/'metrics.json');m=Model(**r['config']);y=np.load(p/'state.npy');h,new=m.evaluate(y)
        phys,ods,edges=physical(m,y,key);allphys+=phys;allod+=ods
        if not key.startswith('E03'):alledges+=edges
        print('PHYSICAL',key,flush=True)
    csvout('physical_usage.csv',allphys);csvout('od_usage_and_sales.csv',allod);csvout('selected_edge_flows.csv',alledges)
    old=list(csv.DictReader((OUT/'all_results.csv').open(encoding='utf-8-sig')))
    for r in old:
        if r['phase']!='E03_coarse':continue
        r['level_3']='NOT_IDENTIFIED';r['level_1']=r['private_aggregate_status'];r['level_2']='FAILED' if r['status']!='PASS' else 'IMPROVING' if r['level_1']=='IMPROVING' and int(r['harmed_od_count'])==0 else 'NOT_IMPROVING'
        for metric in ['pt_vehicle_link_traversals','pt_passenger_distance_model_units','any_actual_pt_trips','actual_mod_and_pt_trips','mod_vehicle_link_traversals']:
            r[metric]=sum(x[metric] for x in allphys if x['run']==r['run']) if r['status']=='PASS' else ''
        r['platform_wholesale_payments']=float(r['wholesale_mod'])+float(r['wholesale_pt'])
        econ.append(r)
    csvout('wholesale_decomposition.csv',econ)
    sensitivity=[]
    for hurdle in [0,10,25,50,100,150]:
        for level in ['level_1','level_2']:
            eligible=[r for r in econ if r[level]=='IMPROVING' and float(r['profit_maas'])>hurdle+1e-3]
            sensitivity.append(dict(hypothetical_minimum_profit=hurdle,level=level,points=len(eligible),classification='DIAGNOSTIC_ONLY'))
    csvout('platform_hurdle.csv',sensitivity)
    write(V7/'phase1_status.json',dict(status='COMPLETE',level1=sum(r['level_1']=='IMPROVING' for r in econ),level2=sum(r['level_2']=='IMPROVING' for r in econ),failed=1,physical_cases=len(source),baseline_unchanged=all(digest(ROOT/k)==v for k,v in seal().items())))
if __name__=='__main__':phase1()
