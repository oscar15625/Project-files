"""Report original values, sequential contrasts, and discrete wholesale points."""
from research_experiments import *
def main():
    manifest=json.loads((OUT/'manifest.json').read_text()); rows=[]; comparisons=[]
    a=json.loads((folder('E01','A_no_maas')/'metrics.json').read_text())
    aod=np.loadtxt(folder('E01','A_no_maas')/'od_results.csv',delimiter=',',skiprows=1,ndmin=2)
    for key,record in manifest.items():
        path=ROOT/record['path']
        r=json.loads((path/'metrics.json').read_text()) if (path/'metrics.json').exists() else {}
        if 'experiment_id' not in r:
            rows.append(dict(run=key,phase=key.split('/')[0],status=record['status'],c_mod=record['config']['wholesale'][0],c_pt=record['config']['wholesale'][1],private_aggregate_status='FAILED')); continue
        row=dict(run=key,phase=r['experiment_id'],status=r['status'],**{k:r[k] for k in ['profit_mod','profit_pt','profit_maas','retail_mod','retail_pt','wholesale_mod','wholesale_pt','maas_receipts','traveler_welfare','social_welfare','share_drive','share_maas','share_non','share_maas_pt','share_maas_mod','transfer_flow','pt_pt_transfers','intermodal_transfers','vi_residual','scaled_residual','time_seconds','solver_seconds','h_evaluations','pumcm_evaluations','h_seconds','peak_memory_mb']})
        # Separate contract unit prices from cash-flow columns.
        row['c_mod']=r['model_config']['wholesale'][0]; row['c_pt']=r['model_config']['wholesale'][1]
        row['price_mod']=r['price_mod']; row['price_pt']=r['price_pt']
        for k in ['profit_mod','profit_pt','traveler_welfare','social_welfare','share_drive']: row['delta_'+k]=r[k]-a[k]
        row['pt_retail_change']=r['retail_pt']-a['retail_pt']; row['pt_decomposition_error']=row['delta_profit_pt']-row['pt_retail_change']-r['wholesale_pt']
        if r['status']=='PASS':
            gains=[row['delta_profit_mod'],row['delta_profit_pt'],r['profit_maas'],row['delta_traveler_welfare']]
            row['private_aggregate_status']='NOT_IMPROVING' if min(gains)<-1e-3 else 'IMPROVING' if min(gains)>1e-3 else 'INDETERMINATE'
            od=np.loadtxt(path/'od_results.csv',delimiter=',',skiprows=1,ndmin=2); assert np.array_equal(od[:,:3],aod[:,:3])
            delta=od[:,7]-aod[:,7]; row['min_od_utility_change']=float(delta.min()); row['harmed_od_count']=int((delta<-1e-8).sum()); row['harmed_demand_pct']=100*float(od[delta<-1e-8,2].sum()/od[:,2].sum())
            row['all_od_average_nonworse']=bool(np.min(delta)>=-1e-8)
        else: row['private_aggregate_status']='FAILED'
        row['public_pareto_status']='NOT_APPLICABLE'
        rows.append(row)
    for left,right,name in [('A_no_maas','B_maas_no_transfer_advantage','B_minus_A'),('B_maas_no_transfer_advantage','C_maas_paper_advantage','C_minus_B'),('A_no_maas','C_maas_paper_advantage','C_minus_A')]:
        l=json.loads((folder('E01',left)/'metrics.json').read_text()); r=json.loads((folder('E01',right)/'metrics.json').read_text())
        comparisons.append(dict(contrast=name,interpretation='sequential equilibrium difference, not causal contribution',**{k:r[k]-l[k] for k in ['profit_mod','profit_pt','profit_maas','traveler_welfare','social_welfare','share_drive','share_maas','transfer_flow']}))
    # Union schema preserves missing entries as blanks for failed solver records.
    def unioncsv(path,data):
        fields=list(dict.fromkeys(k for row in data for k in row))
        with path.open('w',newline='',encoding='utf-8-sig') as f: w=csv.DictWriter(f,fields); w.writeheader(); w.writerows(data)
    unioncsv(OUT/'all_results.csv',rows); unioncsv(OUT/'E01_contrasts.csv',comparisons)
    unchanged=all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in json.loads((OUT/'G00/protected_hashes.json').read_text()).items())
    assert unchanged
    summary=dict(date='2026-11-06',total=len(manifest),status_counts={s:sum(r['status']==s for r in manifest.values()) for s in set(r['status'] for r in manifest.values())},protected_unchanged=unchanged,coarse_executed=any(r.get('phase')=='E03_coarse' for r in rows),source_tag='maas-reproduction-v5',reequilibrated_deviations='NOT_PERFORMED',interpretation='Discrete tested points, not continuous region or negotiation prediction')
    write(OUT/'summary.json',summary); print(json.dumps(summary,indent=2)); print(comparisons)
if __name__=='__main__': main()
