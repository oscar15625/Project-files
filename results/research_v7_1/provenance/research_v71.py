"""v7.1: source-first audit and read-only reanalysis of November source states."""
from research_v7 import *
import research_v7 as prior
O=ROOT/'results/research_v7_1';O.mkdir(parents=True,exist_ok=True)
def outcsv(name,rows):
    if not rows:return
    p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def csvread(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def seal71():
    p=O/'protected_hashes.json'
    if p.exists():
        d=read(p);assert all(digest(ROOT/k)==v for k,v in d.items());return d
    paths=[ROOT/'src/model.py']+list(ROOT.glob('research_*.py'))+list(ROOT.glob('verify_research_v*.py'))
    paths=[p for p in paths if 'v71' not in p.name]
    paths += [p for s in ['results/v4','results/v5','results/research_v6','results/research_v7'] for p in (ROOT/s).rglob('*') if p.is_file()]
    d={str(p.relative_to(ROOT)):digest(p) for p in paths};write(O/'protected_hashes.json',d);return d
def r00():
    definitions=[
      ('C01','OD product','4','3','AUTHOR_EXPLANATION','OD-based pricing affords route and mode flexibility following Yao and Zhang 2024.','Conceptual product definition; no subscription/PAYG estimation.','Test product representativeness rather than claiming absent justification.'),
      ('C02','Availability','3,4','2-3','ORIGINAL_PAPER','Driving is available to all; travelers freely choose the three service subnetworks.','Availability is assumed; adoption and vehicle eligibility are not identified.','Separate modeled availability from observed market participation.'),
      ('C03','Service differentiation','3,4','2-3','AUTHOR_EXPLANATION','Both MaaS and non-MaaS permit self-designed single- or multi-modal trips, with shared supply and different fares/transfer costs.','Static duplication tests only the implemented upper Shannon specialization.','Non-MaaS is not restricted to unimodal travel.'),
      ('C04','Exclusivity','3','2','ORIGINAL_PAPER','No transfer links connect MaaS, non-MaaS and driving within a trip.','Payment-state mixing is excluded by construction.','Test a separate expanded payment-state model for mixed purchases.'),
      ('C05','MoD definition','9,10','5.1.1','ORIGINAL_PAPER','One MoD operator serves every road link and transfers at all PT stops; access uses total MoD demand.','Fleet operations, rebalancing and empirical service correspondence are not recovered.','MoD is explicitly defined; its real-market correspondence is a different question.'),
      ('C06','MoD market share','12,17','Tables 2-3','ORIGINAL_PAPER','Before-MaaS MoD shares are 50.8% and 40.9%.','These are model outputs, not observed Swiss modal shares.','Test explicit hypothetical lower-MoD baseline markets.'),
      ('C07','Transfer benefit','11,19','5.1.3; Appendix A','AUTHOR_EXPLANATION','Integrated planning and lower transfer inconvenience motivate reduced penalties; small 10 to 1 or 3, Sioux 8 to 0.5.','The magnitudes are settings; RP/SP calibration is not demonstrated in these sections.','Acknowledge the qualitative rationale and test its magnitude.'),
      ('C08','PUMCM','5,6','3.1 Eqs.1-11','AUTHOR_EXPLANATION','General smooth convex perturbations support values, probabilities, flows and sensitivities.','This code is a Shannon specialization, not the entire PUMCM class.','Upper Shannon duplication is not a theorem about every PUMCM.'),
      ('C09','PT pricing','9,10','5.1.1 Eq.27','ORIGINAL_PAPER','Two PT lines share one operator and a per-PT-link retail price; MoD is distance-priced.','Integrated ticket systems require different fare states.','Link pricing is explicit; examine external applicability separately.'),
      ('C10','Government','2','1','AUTHOR_EXPLANATION','The introduction notes incentive withdrawal and real implementation difficulties.','Government strategy and budgets are outside the modeled game.','Do not say government support was never discussed.'),
      ('C11','Wholesale symmetry','13,19','5.1.4; Appendix A','ORIGINAL_PAPER','Small sensitivity uses a common 0-3.5 price; Sioux uses MoD 1.5 and PT 1.0.','A full two-dimensional contractual landscape is not the common-price experiment.','Distinguish common-price simplification from the asymmetric Sioux case.'),
      ('C12','Revenue objectives','7','3.3-3.4 Eqs.17,19','AUTHOR_EXPLANATION','Fixed exogenous capacities motivate operator retail-plus-wholesale revenue maximization.','Additional platform costs are not empirically estimated.','Positive modeled residual is not demonstrated commercial sustainability.'),
      ('C13','Negotiation','4,13,18','3;5.1.4;6','AUTHOR_ACKNOWLEDGED_LIMITATION','Wholesale negotiation is prior/exogenous; bargaining feasibility and revenue sharing are discussed as future work.','An improving set does not determine which contract is negotiated.','Credit the authors discussion; test asymmetric participation sets.'),
      ('C14','Traveler objective','4,12,13','3;5.1.3-4','ORIGINAL_PAPER','Travelers maximize their own expected utilities; Pareto-improving language concerns reported comparisons.','Aggregate welfare does not identify every OD or person improvement.','Do not attribute cooperative Pareto objectives to travelers.'),
      ('C15','Virtual operator','2,6,9','1;3.2;4.2','AUTHOR_EXPLANATION','Dual traffic formulation avoids repeated lower-level equilibrium and equilibrium-sensitivity solves.','No controlled same-game nested timing comparison is demonstrated here.','Separate a sound computational motivation from measured comparative speed.'),
      ('C16','EG and initialization','8,10,11,19','4.2;5.1.2;Appendix A','ORIGINAL_PAPER','EG equations and nonmonotone limitations are stated; 150 initial perturbation runs and convergence figures are reported.','No matched PG/adaptive-EG cost table in the reviewed experiment sections.','Do not call it untested; reproduce the stated baseline and then compare.'),
      ('C17','Demand heterogeneity','14,15,18','5.1.5;6','AUTHOR_ACKNOWLEDGED_LIMITATION','OD-specific VOT is varied experimentally; elastic and heterogeneous demand extensions are acknowledged.','Within-OD distributions at common population means are different experiments.','OD VOT sensitivity already exists; target richer distributional robustness.'),
      ('C18','Geographic scope','9,16,17,18','5-6','ORIGINAL_PAPER','Experiments use a toy network and extended Sioux Falls; Swiss funding/affiliation is not Swiss market data.','Swiss fare systems would be external scenarios.','Do not judge numerical reproduction as a Lausanne empirical model.'),
      ('C19','Access aggregation','10','5.1.1','UNRESOLVED_SPECIFICATION','The paper explicitly makes MoD access homogeneous and dependent on total MoD demand.','November node/node baseline differs from that stated aggregation.','Node/node outcomes are independent counterfactuals, not recovered author settings.'),
      ('C20','Stopping criterion','10,19','5.1.2;Appendix A','UNRESOLVED_SPECIFICATION','Section 5.1.2 describes consecutive-iterate norm; Appendix A specifies natural projected residual with gamma 1e-4.','For EG these two residuals are not generally identical.','Report both; do not infer certified accuracy solely from iterate change.'),
      ('C21','VI versus global optimum','7,8','3.3 Eq.18;4.1','AUTHOR_ACKNOWLEDGED_LIMITATION','The text explicitly says nonconvex platform optimization and its VI condition are not equivalent; optima satisfy the VI.','Stationarity and finite deviations do not prove global profit maximization.','Credit the stated qualification and retain independent deviation diagnostics.')]
    text=(ROOT.parents[1]/'sources/maas.txt').read_text(encoding='utf-8');pages={int(k):v for k,v in re.findall(r'=== PAGE (\d+) ===\s*(.*?)(?==== PAGE|\Z)',text,re.S)}
    rows=[]
    for cid,issue,ps,section,ec,explanation,limit,safe in definitions:
        nums=[int(p) for p in ps.split(',')];assert all(n in pages for n in nums)
        rows.append(dict(claim_id=cid,issue=issue,pages=ps,section=section,evidence_class=ec,author_explanation=explanation,remaining_validation=limit,presentation_safe_claim=safe,source_text_sha256=digest(ROOT.parents[1]/'sources/maas.txt'),review_scope='pp.2-19 incl. conclusion and Appendix A',empirical_validation='NOT_ESTABLISHED_BY_THIS_AUDIT'))
    outcsv('paper_defense_ledger.csv',rows)
    (O/'R00_author_defense.md').write_text('# R00: what the authors explain, and what remains to test\n\nThe main contribution is a computationally motivated single-level VI with differentiable follower responses. Non-MaaS multimodal access, MoD service coverage, transfer convenience, asymmetric Sioux wholesale prices, and future demand/contract/platform extensions are explicitly discussed. These are not missing definitions.\n\nThe appropriate review asks how those definitions map to an external market and how counterfactual outcomes respond to changed conditions. No empirical calibration is established by merely reading a conceptual justification. OD VOT sensitivity and the 150 local initialization experiments deserve explicit credit.\n\nTwo additional source-to-code qualifications matter: page 10 prescribes total-demand homogeneous MoD access, while our November baseline uses node aggregation; page 10 and page 19 describe different residual functions for EG. We retain the independent baseline without quietly claiming either discrepancy is an author error. Page 7 also explicitly qualifies VI stationarity versus nonconvex global profit maximization.\n\nFor each of the 21 issues, paper_defense_ledger.csv records pages, section, evidence class, author explanation, remaining test and a presentation-safe claim. No claim of Lausanne calibration is made.\n',encoding='utf-8')
    print('R00: 21 source-checked issues',flush=True)
def metrics(m,y,x=None):
    h,r=m.evaluate(y);f=m.last_flows.copy();mask=m.congest;direct=float(np.linalg.norm(y-m.project(y-1e-4*h)));hc=h.copy()
    if x is not None:hc[:m.nt][mask]=m.cap[mask]*np.maximum(x[:m.nt][mask],0)-f[mask]
    scaled=np.r_[hc[:m.nt],hc[-2:]].copy()
    scaled[:m.nt][mask]=(np.maximum(x[:m.nt][mask],0)-f[mask]/m.cap[mask]) if x is not None else ((np.maximum(y[:m.nt][mask]/m.t0[mask]-1,0)/.15)**.25-f[mask]/m.cap[mask])
    scaled[:m.nt][~mask]=(y[:m.nt]-np.maximum(m.t0,y[:m.nt]-h[:m.nt]/m.cap))[~mask]
    scaled[-2:]/=np.maximum(m.retail_volume,1e-8);scaled[-2:]=y[-2:]-np.maximum(0,y[-2:]-scaled[-2:])
    d=dict(natural_direct=direct,natural_aux=float(np.linalg.norm(y-m.project(y-1e-4*hc))),scaled=float(np.linalg.norm(scaled)),capacity_violation=float(np.maximum(f[~mask]-m.cap[~mask],0).max()),complementarity=float(np.max(abs((y[:m.nt][~mask]-m.t0[~mask])*(m.cap[~mask]-f[~mask])))),conservation=r['flow_conservation_error'],accounting=abs(r['accounting_error']))
    return r,d
def gates():
    protected=seal71()
    for name in ['final_verification.json']:
        for p,h in read(OUT/name)['evidence_sha256'].items():assert digest(ROOT/p)==h,p
    rows=[];configs=[]
    for key,rec in read(OUT/'manifest.json').items():
        p=ROOT/rec['path'];old=read(p/'metrics.json');m=Model(**old['config']);y=np.load(p/'state.npy');x=np.load(p/'coordinates.npy');now,d=metrics(m,y,x)
        diff=max(abs(now[k]-old[k]) for k in now);assert diff<1e-6
        validation=read(p/'validation.json');d['fixed_time_deviation']=validation['deviation_gain_fixed_t'];d['fare_gain']=validation['maas_exact_fare_gain']
        if rec['status']=='PASS':assert d['natural_aux']<1e-6 and d['scaled']<1e-6 and d['complementarity']<1e-3
        row=dict(run=key,status=rec['status'],evidence_class='REPRODUCED_MECHANISM' if rec['status']=='PASS' else 'FAILED_NUMERICAL_CHECK',max_economic_difference=diff,**d);rows.append(row)
        configs.append(dict(run=key,source=rec['path'],config=m.config(),state_hash=digest(p/'state.npy'),coordinate_hash=digest(p/'coordinates.npy'),modified_assumptions=[],source_class='November research_v6 node/node Shannon reconstruction'))
    outcsv('g00_recomputed_states.csv',rows)
    stats=[]
    for key in ['natural_direct','natural_aux','scaled','capacity_violation','complementarity','conservation','accounting','fixed_time_deviation','fare_gain']:
        v=np.array([r[key] for r in rows if r['status']=='PASS']);stats.append(dict(metric=key,median=float(np.median(v)),p95=float(np.percentile(v,95)),maximum=float(v.max()),sample='75 original PASS only',evidence_class='DIAGNOSTIC_ONLY'))
    outcsv('g02_pass_statistics.csv',stats)
    write(O/'experiment_manifest.json',dict(source_tag='research-handoff-20261108',protected_files=len(protected),original_cases=configs,tolerances=dict(natural_aux=1e-6,scaled=1e-6,conservation=1e-6,accounting=1e-6,capacity_violation=1e-4,complementarity=1e-3,fixed_time_deviation=1e-4,aggregate_gain=1e-3,od_nonworse=1e-8),residual_contract='Retain inherited auxiliary-coordinate criterion; separately report direct-time residual; no silent reclassification',boundary_grid=dict(mod=[1.4,1.5,1.6],pt=[.7,.8,.9],purpose='new local tests, never replace original grid'),m01=dict(cases=['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage'],initial_factors=[.95,1.,1.05],methods=['PG','EG_FIXED','EG_ADAPT'],h_budget=20000,initial_step=1e-4,natural_gamma=1e-4,adaptive_eta=.7,adaptive_contraction=.5,process_isolation=True,sioux_gate='All small configurations must pass; otherwise NOT_RUN'),e01=dict(route_scale=1,mode_scale=1,frozen_crosses='A/B times and retail prices x no-MaaS or actual B product with B fare; no equilibrium solve'),cost_hypotheses=dict(fixed=[0,25,50,100],per_trip=[.1,.25,.5,1],revenue_fraction=[.05,.1,.25,.5])))
    write(O/'gates.json',dict(status='PASS_WITH_DISCLOSED_RESIDUAL_CONVENTION',passes=75,original_failed=1,direct_residual_exceedances=sum(r['natural_direct']>=1e-6 for r in rows if r['status']=='PASS'),unexpected_economic_discrepancy=False))
    print('G00-G02 passed with disclosed coordinate qualification',flush=True)
def e01():
    mA,yA,rA=case('A_no_maas');mB,yB,rB=case('B_maas_no_transfer_advantage');result=[]
    for state,y in [('A',yA),('B',yB)]:
        na=np.r_[y[:mA.nt],y[-2:]];nb=np.r_[y[:mA.nt],yB[mB.nt:-2],y[-2:]]
        for label,m,z in [('no_maas',mA,na),('actual_B_product_B_fares',mB,nb)]:
            _,rr=m.evaluate(z,True)
            for od in m.last_od:
                o,d,q,f,pn,pd,pm,v,wm,wp=od
                result.append(dict(frozen_state=state,choice_set=label,origin=int(o),destination=int(d),demand=q,logsum=v,share_non=pn,share_drive=pd,share_maas=pm,weighted_utility=q*v,profit_mod=rr['profit_mod'],profit_pt=rr['profit_pt'],profit_maas=rr['profit_maas'],equilibrium_reference=(state=='A' and label=='no_maas') or (state=='B' and label=='actual_B_product_B_fares'),evidence_class='DIAGNOSTIC_ONLY',route_scale=m.theta,mode_scale=m.mode_theta))
            if label=='no_maas':
                for lab,w in [('independent_clone',2.),('split_corrected',1.)]:
                    for od in m.last_od:
                        o,d,q,f,pn,pd,pm,v,wm,wp=od;den=1+(w-1)*pn;val=v+m.mode_theta*np.log(den)
                        result.append(dict(frozen_state=state,choice_set=lab,origin=int(o),destination=int(d),demand=q,logsum=val,share_non=pn*w/(2*den),share_drive=pd/den,share_maas=pn*w/(2*den),weighted_utility=q*val,profit_mod=None,profit_pt=None,profit_maas=None,equilibrium_reference=False,evidence_class='DIAGNOSTIC_ONLY',route_scale=m.theta,mode_scale=m.mode_theta))
    outcsv('e01_placebo_static.csv',result)
    tests=[]
    for mu in [.2,1.,3.]:
        for u,v in [(-100,0),(0,-100),(1,1),(-20,-22)]:
            before=mu*logsumexp(np.array([u,v])/mu);after=mu*logsumexp(np.array([u-mu*np.log(2),u-mu*np.log(2),v])/mu)
            p=np.exp(u/mu-before/mu);pp=2*np.exp((u-mu*np.log(2))/mu-after/mu)
            assert abs(after-before)<1e-12 and abs(p-pp)<1e-12
            tests.append(dict(mu_mode=mu,u=u,v=v,logsum_error=float(abs(after-before)),probability_error=float(abs(p-pp)),status='PASS',evidence_class='DIAGNOSTIC_ONLY'))
    outcsv('e01_invariance_unit_tests.csv',tests)
def physical71():
    pp=[];oo=[];ee=[]
    source=[(key,ROOT/r['path']) for key,r in read(OUT/'manifest.json').items() if key.startswith(('E01/','E03_coarse/')) and r['status']=='PASS']
    source += [('V5/'+s,ROOT/'results/v4'/s) for s in ['sioux_node_node_total0_without','sioux_node_node_total0_with']]
    for key,p in source:
        old=read(p/'metrics.json');m=Model(**old['config']);y=np.load(p/'state.npy');phys,od,edge=physical(m,y,key)
        pp += [dict(**r,evidence_class='REPRODUCED_MECHANISM',source_state=str(p.relative_to(ROOT))) for r in phys]
        oo += [dict(**r,evidence_class='REPRODUCED_MECHANISM') for r in od]
        if key.startswith(('E01/','V5/')):ee += [dict(**r,evidence_class='REPRODUCED_MECHANISM') for r in edge]
    outcsv('pt_physical_flow_vs_sales_channel.csv',pp);outcsv('pt_od_event_probabilities.csv',oo);outcsv('pt_selected_edge_flows.csv',ee)
    return pp,oo
def e03(pp,oo):
    base=read(folder('E01','A_no_maas')/'metrics.json');b=np.loadtxt(folder('E01','A_no_maas')/'od_results.csv',delimiter=',',skiprows=1);records=[];odrows=[];costs=[]
    for key,rec in read(OUT/'manifest.json').items():
        if not key.startswith('E03_coarse/'):continue
        p=ROOT/rec['path'];r=read(p/'metrics.json');d=next(x for x in csvread(O/'g00_recomputed_states.csv') if x['run']==key)
        row=dict(run=key,c_mod=r['config']['wholesale'][0],c_pt=r['config']['wholesale'][1],status=rec['status'],evidence_class='REPRODUCED_MECHANISM' if rec['status']=='PASS' else 'FAILED_NUMERICAL_CHECK',L3='NOT_IDENTIFIED',**{k:r[k] for k in ['retail_mod','retail_pt','wholesale_mod','wholesale_pt','profit_mod','profit_pt','profit_maas','maas_receipts','share_non','share_maas','share_drive','price_mod','price_pt','traveler_welfare','social_welfare','transfer_flow']})
        row.update({k:float(d[k]) for k in ['natural_direct','natural_aux','scaled','complementarity','conservation','accounting','fixed_time_deviation']})
        for op in ['mod','pt']:
            row['delta_profit_'+op]=r['profit_'+op]-base['profit_'+op];row['delta_retail_'+op]=r['retail_'+op]-base['retail_'+op]
            assert abs(row['delta_profit_'+op]-row['delta_retail_'+op]-r['wholesale_'+op])<1e-6
        row['delta_welfare']=r['traveler_welfare']-base['traveler_welfare'];row['platform_wholesale_payment']=r['wholesale_mod']+r['wholesale_pt']
        if rec['status']=='PASS':
            od=np.loadtxt(p/'od_results.csv',delimiter=',',skiprows=1);assert np.array_equal(od[:,:3],b[:,:3]);delta=od[:,7]-b[:,7]
            gains=[row['delta_profit_mod'],row['delta_profit_pt'],r['profit_maas'],row['delta_welfare']]
            row['L1']='IMPROVING' if min(gains)>1e-3 else 'NOT_IMPROVING' if min(gains)<-1e-3 else 'ZERO_NEAR_ZERO'
            row['harmed_od_count']=int((delta<-1e-8).sum());row['harmed_demand_pct']=float(100*od[delta<-1e-8,2].sum()/od[:,2].sum());row['L2']='IMPROVING' if row['L1']=='IMPROVING' and min(delta)>=-1e-8 else 'NOT_IMPROVING'
            for o,du,originrow in zip(od,delta,b):odrows.append(dict(run=key,origin=int(o[0]),destination=int(o[1]),demand=o[2],delta_utility=du,maas_fare=o[3],maas_sales=o[2]*o[6]*o[3],maas_wholesale=o[2]*o[6]*(o[8]+o[9]),evidence_class='REPRODUCED_MECHANISM'))
            for metric in ['pt_vehicle_link_traversals','pt_paid_links','mod_vehicle_link_traversals','any_actual_pt_trips','actual_mod_and_pt_trips']:
                row[metric]=sum(float(a[metric]) for a in pp if a['run']==key)
            for costtype,values in [('fixed',[0,25,50,100]),('per_trip',[.1,.25,.5,1]),('revenue_fraction',[.05,.1,.25,.5])]:
                for v in values:
                    cost=v if costtype=='fixed' else v*r['share_maas']*10 if costtype=='per_trip' else v*r['maas_receipts']
                    net=r['profit_maas']-cost
                    costs.append(dict(run=key,cost_type=costtype,parameter=v,assumed_cost=cost,platform_residual=net,L1_after_cost=row['L1']=='IMPROVING' and net>1e-3,L2_after_cost=row['L2']=='IMPROVING' and net>1e-3,evidence_class='DIAGNOSTIC_ONLY',equilibrium_recomputed=False))
        else:row['L1']=row['L2']='FAILED_NUMERICAL_CHECK';write(O/'failed_runs/original_mod_3.5_pt_1.5.json',dict(source=str(p.relative_to(ROOT)),metrics=r,validation=read(p/'validation.json'),status='FAILED_NUMERICAL_CHECK'))
        records.append(row)
    outcsv('e03_all_results_reaudited.csv',records);outcsv('e03_revenue_decomposition.csv',records);outcsv('e03_welfare_levels.csv',[{k:r.get(k) for k in ['run','c_mod','c_pt','L1','L2','L3','harmed_od_count','harmed_demand_pct','evidence_class']} for r in records]);outcsv('e03_od_welfare.csv',odrows);outcsv('e03_cost_participation.csv',costs)
    assert sum(r['L1']=='IMPROVING' for r in records)==31 and sum(r['L2']=='IMPROVING' for r in records)==14
def main():
    import re
    r00();gates();e01();p,o=physical71();e03(p,o);seal71()
    write(O/'milestone_A.json',dict(status='PASS',economic_reanalysis='75 accepted attempts re-evaluated; one original failure preserved',level1=31,level2=14,static_only=True,evidence_class='REPRODUCED_MECHANISM'))
    print('Milestone A complete',flush=True)
if __name__=='__main__':
    import re
    main()
