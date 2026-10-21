import run
import numpy as np
from src.model import Model
from refine import refine

if __name__=='__main__':
    start=np.load('results/sioux_node_theta1_with/state.npy')
    for cp in [.5,1.5,2.,3.]:
        m=Model('sioux',True,wholesale=[1.5,cp],access_scope='node')
        y,r=refine(m,f'sioux_wholesale_pt{cp:g}',start,maxiter=80)
    m=Model('small',True,penalty=3,access_scope='node')
    refine(m,'small_node_moderate',np.load('results/small_node_theta1_with/state.npy'),maxiter=100)
