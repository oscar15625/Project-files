"""Independent controlled tariff structures on the existing SMALL network.
Original link: PT fare per physical PT segment (source model).
Flat journey: PT fare assessed exactly once on first PT boarding, including a MoD->PT transfer.
Toy zones: PT fare once per distinct node-zone used by PT, no double charge on reentry.
The network's actual mode choices, traffic resources, MaaS fares, retail MoD fare,
wholesale c, capacity, OD, PUMCM specifications remain unchanged.
NOT the paper's full Sioux Falls reproduction and NOT actual Swiss Mobilis fares.
"""
from pathlib import Path
import sys, numpy as np
sys.path.insert(0,str(Path(__file__).parent/'maas_cloud_study'))
from src.model import Model,Graph
from maas_cloud_study.solver import solve

ZONES_SMALL={1:0,2:0,3:1,4:1,5:2,6:2,7:3,8:3}

def wrap_state(s,flag):
    return s if s[0]=='end' else (*s,flag)

def change_non_maas_tariff(m,tariff,zone_map=None):
    if tariff=='link':return m
    assert tariff in ('flat','zones')
    if zone_map is None:zone_map=ZONES_SMALL
    for ids,grp in m.graphs:
        g=grp['non'];d=int(m.ods[ids[0],1]);flags=range(2 if tariff=='flat' else 2**len(set(zone_map.values())))
        gate_nodes=[('gate',int(m.ods[idx,0]),0) for idx in ids]
        edges=[]
        for (s,j),at in zip(g.edge_labels,g.attr):
            for flag in flags:
                newflag=flag
                if isinstance(j[0],int):
                    bit=1 if tariff=='flat' else (1<<zone_map[j[1]])
                    newflag=flag|bit
                    charge=1 if (not flag&bit) else 0
                else:charge=0
                b=at.copy()
                b[3]=charge # PT retail coefficient only. PT link fare 0 in flat/zones.
                edges.append((wrap_state(s,flag),wrap_state(j,newflag),*b))
        grp['non']=Graph(edges,gate_nodes,d,g.theta)
    m.fare_structure=tariff
    return m

def model(tariff,maas,penalty=1.,zone_map=None):
    m=Model('small',maas=maas,access_scope='node',penalty=penalty)
    return change_non_maas_tariff(m,tariff,zone_map)
