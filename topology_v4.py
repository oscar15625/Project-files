import run
from batch_v4 import pair
from src.model import Model
import numpy as np
for scope in ['node','aggregate']:
    old=np.load(f'results/small_{scope}_theta1_without/state.npy'); oldm=Model('small',False,access_scope=scope)
    for variant in ['figure_pt','figure_pt_reverse23']:
        cfg=dict(name='small',mod_access_scope=scope,pt_access_scope='node',small_network_variant=variant)
        m=Model(maas=False,**cfg); warm=m.initial(); warm[:12]=old[:12]; warm[m.accessM]=old[oldm.accessM]; warm[-2:]=old[-2:]
        pair(cfg,f'v4/small_{scope}_{variant}',warm)
