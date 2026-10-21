"""Additional labelled starts; never overwrite rejected or incomplete runs."""
import run
from batch_v4 import pair
from src.model import Model
import numpy as np

if __name__=='__main__':
    for ps,total in [('node',False),('line_node',False),('node',True)]:
        cfg=dict(name='small',mod_access_scope='aggregate',pt_access_scope=ps,pt_capacity_total=total)
        m=Model(maas=False,**cfg); old=np.load('results/small_aggregate_theta1_without/state.npy')
        warm=m.initial(); warm[:m.accessP+1]=old[:m.accessP+1]; warm[-2:]=old[-2:]
        pair(cfg,f'v4/small_aggregate_{ps}_total{int(total)}_warm',warm)
    for scale in [.5,.2]:
        cfg=dict(name='sioux',mod_access_scope='aggregate',pt_access_scope='node',theta=scale)
        m=Model(maas=False,**cfg)
        warm=np.load('results/v4/sioux_aggregate_node_total0_without/state.npy')
        pair(cfg,f'v4/sioux_mixed_common_{scale:g}',warm)
