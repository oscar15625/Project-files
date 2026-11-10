import run
from src.model import Model
from refine import refine
import numpy as np
import argparse

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--network',default='small'); p.add_argument('--theta',type=float,default=1); p.add_argument('--access',default='node'); a=p.parse_args()
    prefix=f'{a.network}_{a.access}_theta{a.theta:g}'
    base=Model(a.network,False,a.theta,access_scope=a.access)
    y,r=refine(base,prefix+'_without',maxiter=120)
    m=Model(a.network,True,a.theta,access_scope=a.access)
    start=np.r_[y[:base.nt],np.full(m.nod,5.),y[-2:]]
    refine(m,prefix+'_with',start,maxiter=150)
