"""Saved-state cross-network comparisons, entry decomposition and review diagnostics."""
import run
import csv,json,time,platform
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from src.model import Model
from spec_audit_v5 import writecsv

OUT=Path('results/v6')

def read(tag):
    p=OUT/tag
    return json.loads((p/'metrics.json').read_text()),np.load(p/'state.npy')

def main():
    manifest=json.loads((OUT/'manifest.json').read_text()); comparisons=[]; od_rows=[]; benchmarks=[]
    for tag,entry in manifest.items():
        if entry['status']!='PASS': continue
        r,y=read(tag)
        if not r['maas']: continue
        baseline=('sioux_aggregate_without' if 'aggregate' in tag else tag.replace('_paper','_without') if 'initial1' in tag or 'transfer1' in tag else r['network']+'_node_without')
        b,z=read(baseline)
        assert manifest[baseline]['status']=='PASS'
        row=dict(run=tag,baseline=baseline,network=r['network'],wholesale_mod_price=r['wholesale'][0],wholesale_pt_price=r['wholesale'][1],profit_mod=r['profit_mod'],profit_pt=r['profit_pt'],profit_maas=r['profit_maas'],mod_gain=r['profit_mod']-b['profit_mod'],pt_gain=r['profit_pt']-b['profit_pt'],mod_gain_pct=100*(r['profit_mod']/b['profit_mod']-1),pt_gain_pct=100*(r['profit_pt']/b['profit_pt']-1),pt_retail_change=r['retail_pt']-b['retail_pt'],pt_wholesale=r['wholesale_pt'],mod_retail_change=r['retail_mod']-b['retail_mod'],mod_wholesale=r['wholesale_mod'],traveler_gain=r['traveler_welfare']-b['traveler_welfare'],social_gain=r['social_welfare']-b['social_welfare'],driving_change_pp=r['share_drive']-b['share_drive'],pt_first_before=b['share_non_pt'],pt_first_after=r['share_non_pt']+r['share_maas_pt'],maas_pt_first=r['share_maas_pt'],maas_mod_first=r['share_maas_mod'],transfers_before=b['transfer_flow'],transfers_after=r['transfer_flow'])
        row['pt_decomposition_error']=row['pt_gain']-row['pt_retail_change']-row['pt_wholesale']
        row['operator_and_aggregate_traveler_improvement']=bool(row['mod_gain']>0 and row['pt_gain']>0 and row['profit_maas']>0 and row['traveler_gain']>0)
        current=np.atleast_2d(np.loadtxt(OUT/tag/'od_results.csv',delimiter=',',skiprows=1)); prior=np.atleast_2d(np.loadtxt(OUT/baseline/'od_results.csv',delimiter=',',skiprows=1))
        assert np.array_equal(current[:,:3],prior[:,:3])
        gains=current[:,7]-prior[:,7]; row['min_od_utility_change']=float(gains.min()); row['max_od_utility_change']=float(gains.max()); row['harmed_od_count']=int((gains< -1e-8).sum()); row['harmed_demand_pct']=float(100*current[gains< -1e-8,2].sum()/current[:,2].sum())
        assert abs(current[:,2]@gains-row['traveler_gain'])<1e-6
        for a,delta in zip(current,gains): od_rows.append(dict(run=tag,origin=int(a[0]),destination=int(a[1]),demand=a[2],expected_utility_change=delta))
        comparisons.append(row)
    writecsv(OUT/'entry_comparison.csv',comparisons); writecsv(OUT/'od_benefits.csv',od_rows)
    # Representative price response: fixed times and competing decisions.
    representative=[]
    r,y=read('sioux_node_without'); m=Model(**r['config'])
    selected={(1,3),(1,13),(1,18),(4,5)}
    for price in [y[-1],3.65]:
        yp=y.copy(); yp[-1]=price
        for ids,group in m.graphs:
            if not any(tuple(m.ods[k,:2].astype(int)) in selected for k in ids): continue
            kinds=list(group); sol=[g.solve(yp[:m.nt],yp[-2:],m.wholesale,k) for k,g in group.items()]
            v=np.array([s[0]-(m.fixed if k=='drive' else 0) for s,k in zip(sol,kinds)]).T
            share=np.exp(v/m.mode_theta-logsumexp(v/m.mode_theta,axis=1)[:,None])
            gi=kinds.index('non'); g=group['non']; s=sol[gi]
            for local,idx in enumerate(ids):
                o,d,q=m.ods[idx]
                if (int(o),int(d)) not in selected: continue
                inj=np.zeros(len(ids)); inj[local]=1; flow=s[4](inj)
                representative.append(dict(origin=int(o),destination=int(d),price=price,demand=q,non_maas_share=share[local,gi],conditional_first_pt=flow[g.board_pt].sum(),conditional_paid_pt_links=flow@g.attr[:,3],expected_paid_pt_links=share[local,gi]*(flow@g.attr[:,3]),non_maas_value=s[0][local],non_value_price_derivative=s[2][local,1]))
    writecsv(OUT/'representative_price_response.csv',representative)
    for tag in ['small_node_paper','sioux_node_paper']:
        r,y=read(tag); m=Model(**r['config']); m.evaluate(y); times=[]
        for _ in range(3):
            start=time.perf_counter(); m.evaluate(y); times.append(time.perf_counter()-start)
        benchmarks.append(dict(run=tag,od_count=m.nod,destinations=len(m.graphs),graphs=sum(len(g) for _,g in m.graphs),graph_transient_states=sum(h.n for _,g in m.graphs for h in g.values()),graph_edges=sum(len(h.i) for _,g in m.graphs for h in g.values()),resources=m.nt,median_evaluation_seconds=float(np.median(times)),solver_seconds=r['seconds'],solver_calls=r['calls'],cpu_threads_requested=1))
    writecsv(OUT/'local_scaling.csv',benchmarks)
    definition=dict(date='2026-10-27',paper='https://doi.org/10.1016/j.trc.2026.105703',completed=len(manifest),passed=sum(v['status']=='PASS' for v in manifest.values()),comparisons=len(comparisons),python=platform.python_version(),interpretation='Tested wholesale points only, not an identified continuous regime. Expected OD utility, not observed individual benefits. Fixed-time VI deviation, not re-equilibrated Stackelberg response.')
    (OUT/'analysis_summary.json').write_text(json.dumps(definition,indent=2))
    print(json.dumps(definition,indent=2)); print([(r['run'],round(r['pt_gain_pct'],2),r['operator_and_aggregate_traveler_improvement']) for r in comparisons])

if __name__=='__main__': main()
