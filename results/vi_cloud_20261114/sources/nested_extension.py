"""Experimental nested top-level mode choice. NEVER edits the archived Model.

Root: nest {non-MaaS, MaaS} and singleton {private driving};
mu is root scale, lambda*mu the within-nest scale; lambda=1 reproduces MNL.
Within each mode, unchanged recursive path-choice Graph.solve (Shannon PUMCM).
This is a *sensitivity specification*, not an estimated Swiss demand model.
"""
from __future__ import annotations
import numpy as np
from scipy.special import logsumexp
from src.model import Model


def nested_root(values, kinds, mu=1.0, lam=1.0):
    values = np.asarray(values, dtype=float)
    if not 0 < lam <= 1 or mu <= 0: raise ValueError('Require 0 < lambda <= 1 and mu > 0')
    kinds = list(kinds)
    nest = [i for i,k in enumerate(kinds) if k in ('non','maas')]
    drive = kinds.index('drive')
    n=values.shape[0]
    within_logits = values[:,nest]/(lam*mu)
    within_logsum = logsumexp(within_logits, axis=1)
    within = np.exp(within_logits - within_logsum[:,None])
    inclusive=lam*mu*within_logsum
    root = mu*logsumexp(np.c_[inclusive/mu,values[:,drive]/mu],axis=1)
    Pnest=np.exp(inclusive/mu-root/mu)
    Pdrive=np.exp(values[:,drive]/mu-root/mu)
    shares=np.zeros_like(values)
    shares[:,nest]=Pnest[:,None]*within
    shares[:,drive]=Pdrive
    # d share(j) / d V(non) for operator retail price sensitivity.
    nonpos=nest.index(kinds.index('non'))
    wn=within[:,nonpos]
    dnon=np.zeros_like(shares)
    for ii, j in enumerate(nest):
        dnon[:,j]=shares[:,j]*(Pdrive*wn/mu+((1.0 if j==kinds.index('non') else 0.0)-wn)/(lam*mu))
    dnon[:,drive]=-shares[:,drive]*Pnest*wn/mu
    # d share(maas)/d V(maas), needed for platform price gradient.
    dmaas=None
    if 'maas' in kinds:
        wi=within[:,nest.index(kinds.index('maas'))]
        p=shares[:,kinds.index('maas')]
        dmaas=p*(Pdrive*wi/mu+(1-wi)/(lam*mu))
    return shares,root,dnon,dmaas


class NestedModel(Model):
    """Same networks, traffic operator, wholesales, and VI map, nested *root* only."""
    def __init__(self, *args, nest_lambda=1.0, **kwargs):
        super().__init__(*args, **kwargs)
        if not 0 < nest_lambda <= 1: raise ValueError('nest_lambda must be in (0,1]')
        self.nest_lambda=float(nest_lambda)
    def config(self):
        return {**super().config(), 'nest_lambda':self.nest_lambda}
    def evaluate(self,y,details=False):
        self.last_od=[]; self.retail_volume=np.zeros(2)
        retail=np.zeros(2);wholesale_paid=np.zeros(2);maas_receipts=0.;boarding=np.zeros((2,2));pt_transfers=0.
        mt=self.mode_theta;t=y[:self.nt]; prices=y[-2:];fares=y[self.nt:-2] if self.maas else np.zeros(self.nod)
        flows=np.zeros(self.nt);profit=np.zeros(3);gradient=np.zeros(2);gp=np.zeros(self.nod);shares=np.zeros(3);welfare=0.;transfers=0.;conservation=0.; pt_ridelinks=0.
        if getattr(self,'optimize_fares',False):
            raise RuntimeError('MNL closed-form optimized fares not valid under nested root; optimize fares as variables')
        for ids,group in self.graphs:
            kinds=list(group);sol=[group[k].solve(t,prices,self.wholesale,k) for k in kinds]
            values=np.array([s[0]-(self.fixed if k=='drive' else fares[ids] if k=='maas' else 0) for k,s in zip(kinds,sol)]).T
            share,lv,dnon,dmaas = nested_root(values,kinds,mt,self.nest_lambda)
            q=self.ods[ids,2];welfare+=q @ lv
            if details:
                for row,idx in enumerate(ids):
                    conditional=sol[kinds.index('maas')][1][row] if self.maas else np.zeros(2)
                    self.last_od.append([*self.ods[idx],fares[idx] if self.maas else 0,*(share[row,kinds.index(k)] if k in kinds else 0 for k in ['non','drive','maas']),lv[row],*conditional])
            non=kinds.index('non'); dv=sol[non][2]
            ds=dnon[:,:,None]*dv[:,None,:]
            for b,(k,s) in enumerate(zip(kinds,sol)):
                V,R,dV,dR,load=s; demand=q*share[:,b]; flow=load(demand);g=group[k]
                if k=='non':self.retail_volume+=flow@g.attr[:,2:4]
                if k!='drive':
                    boarding[0 if k=='non' else 1]+=np.array([flow[g.board_mod].sum(),flow[g.board_pt].sum()])
                    pt_transfers+=flow[g.pt_transfer].sum()
                    pt_ridelinks+=np.sum(flow[(g.res>=len(self.rows))&(g.res<self.accessM)])
                if k=='non':retail+=demand@R
                if k=='maas':wholesale_paid+=demand@R;maas_receipts+=demand@fares[ids]
                mask=g.res>=0; np.add.at(flows,g.res[mask],flow[mask]);transfers+=flow@g.attr[:,6]
                shares[{'non':0,'drive':1,'maas':2}[k]]+=demand.sum()
                conservation=max(conservation,abs(flow[~g.internal].sum()-demand.sum()))
                if k!='drive':
                    profit[:2]+=demand@R
                    for op in range(2):gradient[op]+=np.sum(q*(ds[:,b,op]*R[:,op]+share[:,b]*dR[:,op,op]))
                if k=='maas':
                    margin=fares[ids]-R.sum(axis=1);profit[2]+=demand@margin
                    gp[ids]=q*(share[:,b]-margin*dmaas)
        supply=self.cap.copy();mask=self.congest
        supply[mask]=self.cap[mask]*(np.maximum(t[mask]/self.t0[mask]-1,0)/.15)**.25
        H=np.r_[supply-flows,-gp if self.maas else [],-gradient]
        self.last_flows=flows;self.retail_mass=shares[0]
        out=dict(profit_mod=profit[0],profit_pt=profit[1],profit_maas=profit[2],profit_total=profit.sum(),share_non=shares[0]/self.total*100,share_drive=shares[1]/self.total*100,share_maas=shares[2]/self.total*100,price_mod=prices[0],price_pt=prices[1],traveler_welfare=welfare,social_welfare=welfare+profit.sum(),transfer_flow=transfers,flow_conservation_error=conservation)
        out.update(retail_mod=retail[0],retail_pt=retail[1],wholesale_mod=wholesale_paid[0],wholesale_pt=wholesale_paid[1],maas_receipts=maas_receipts,accounting_error=float(profit.sum()-retail.sum()-maas_receipts),share_non_mod=boarding[0,0]/self.total*100,share_non_pt=boarding[0,1]/self.total*100,share_maas_mod=boarding[1,0]/self.total*100,share_maas_pt=boarding[1,1]/self.total*100,pt_pt_transfers=pt_transfers,intermodal_transfers=transfers-pt_transfers,pt_access_flow=float(flows[self.pt_resources].sum()),mod_access_flow=float(flows[self.mod_resources].sum()),pt_total_capacity=float(self.cap[self.pt_resources].sum()),nested_lambda=self.nest_lambda,pt_ride_link_flow=float(pt_ridelinks))
        return H,out
