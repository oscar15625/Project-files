import run
from pathlib import Path
import json,csv,hashlib
import numpy as np
from src.model import Model

FINAL=['small_aggregate_theta1_without','small_aggregate_theta1_with','small_node_theta1_without','small_node_theta1_with','sioux_aggregate_theta1_without','sioux_aggregate_theta1_with','sioux_node_theta1_without','sioux_node_theta1_with','sioux_wholesale_pt0.5','sioux_wholesale_pt1.5','sioux_wholesale_pt2','sioux_wholesale_pt3','small_node_moderate','small_node_theta2_warm_without','small_node_theta2_warm_with']
if __name__=='__main__':
    FINAL.append('sioux_aggregate_corrected')
    summary=[]
    for tag in FINAL:
        folder=Path('results')/tag
        if not (folder/'metrics.json').exists(): continue
        r=json.loads((folder/'metrics.json').read_text()); m=Model(r['network'],r['maas'],r['theta'],r['penalty'],r['wholesale'],r['access_scope']); y=np.load(folder/'state.npy'); m.evaluate(y,True)
        np.savetxt(folder/'od_results.csv',m.last_od,delimiter=',',header='origin,destination,demand,maas_fare,share_non,share_drive,share_maas,value',comments='')
        np.savetxt(folder/'resource_results.csv',np.c_[np.arange(m.nt),m.t0,m.cap,m.congest,y[:m.nt],m.last_flows],delimiter=',',header='resource,t0,capacity,congestible,time,flow',comments='')
        status='residual_only_not_strategically_audited'
        if (folder/'audit.json').exists():
            audit=json.loads((folder/'audit.json').read_text())
            status='passed_numerical_deviation_check' if audit['all_retail_deviation_gains_below_1e-4'] else 'REJECTED_profitable_unilateral_deviation'
        summary.append(dict(run=tag,interpretation_status=status,**r))
    Path('results/final_manifest.json').write_text(json.dumps(summary,indent=2))
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('data').glob('*.tntp')}
    Path('data/provenance.json').write_text(json.dumps({'source':'https://github.com/bstabler/TransportationNetworks/tree/master/SiouxFalls','retrieved':'2026-10-21','sha256':hashes,'network_blob':'66d0eca4ddcfb82f861bea040060deab7a741b2f','trips_blob':'db70eda57738877811e9ac07c25a567973d3b6a0'},indent=2))
