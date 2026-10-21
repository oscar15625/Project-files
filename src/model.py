"""PUMCM Shannon specialization with exact implicit sensitivity and shared supply."""
import numpy as np
from scipy.sparse import csc_matrix, eye
from scipy.sparse.linalg import splu
from scipy.special import logsumexp, lambertw
import re
from pathlib import Path

def inputs(name):
    if name == 'small':
        rows=[(1,2,2,300,5),(2,3,1.6,200,4),(2,7,4,300,10),(3,4,2,300,5),(3,5,2,300,5),(3,6,3.2,200,8),(4,5,2.4,300,6),(4,7,2,300,5),(5,6,2,300,5),(6,4,2.4,400,6),(6,8,2,300,5),(7,8,2,300,5)]
        return rows, [[1,2,3,5,6],[3,4,7]], [(3,5,500),(1,5,300),(1,7,200)]
    rows=[]
    for line in Path('data/SiouxFalls_net.tntp').read_text().splitlines():
        v=line.split()
        if len(v)>9 and v[0].isdigit():
            i,j=int(v[0]),int(v[1]); t=float(v[4]); length=.8 if {i,j}=={14,15} else t*.2
            rows.append((i,j,length,float(v[2]),t))
    ods=[]
    for block in Path('data/SiouxFalls_trips.tntp').read_text().split('Origin')[1:]:
        o=int(block.split()[0])
        for d,q in re.findall(r'(\d+)\s*:\s*([\d.]+)',block):
            if int(d)!=o and float(q)>0: ods.append((o,int(d),1.2*float(q)))
    return rows, [[1,3,12,13],[2,6,8,16,17,19,20],[12,11,10,16,18]], ods

class Graph:
    def __init__(self, edges, gates, destination, theta):
        # Edge fields: source,target,resource,constant,retail-M,retail-P,wholesale-M,wholesale-P,transfer
        terminal=('end',destination)
        nodes=set(e[0] for e in edges)|set(e[1] for e in edges)
        reachable={terminal}
        while True:
            nxt=reachable|{e[0] for e in edges if e[1] in reachable}
            if nxt==reachable: break
            reachable=nxt
        nodes=sorted(reachable-{terminal},key=str); index={x:i for i,x in enumerate(nodes)}
        self.n=len(nodes); self.gates=np.array([index.get(g,-1) for g in gates]); self.theta=theta
        edges=[e for e in edges if e[0] in index and e[1] in reachable]
        self.i=np.array([index[e[0]] for e in edges]); self.j=np.array([index.get(e[1],self.n) for e in edges])
        self.attr=np.array([e[2:] for e in edges],float); self.res=self.attr[:,0].astype(int)
        self.internal=self.j<self.n
    def solve(self,t,prices,wholesale,kind):
        a=self.attr; cost=a[:,1].copy(); mask=self.res>=0; cost[mask]+=t[self.res[mask]]
        if kind=='non': cost+=a[:,2:4]@prices
        w=np.exp(-cost/self.theta); keep=self.internal; i,j=self.i,self.j
        W=csc_matrix((w[keep],(i[keep],j[keep])),shape=(self.n,self.n))
        lu=splu(eye(self.n,format='csc')-W)
        b=np.bincount(i[~keep],weights=w[~keep],minlength=self.n)
        z=lu.solve(b)
        if np.any(z<=0) or not np.all(np.isfinite(z)): raise ValueError('Improper/underflowing Bellman solution')
        zz=np.r_[z,1.]; gates=self.gates; valid=gates>=0
        V=np.full(len(gates),-np.inf); V[valid]=self.theta*np.log(z[gates[valid]])
        rewards=a[:,4:6]*wholesale if kind=='maas' else a[:,2:4]*prices if kind=='non' else np.zeros((len(i),2))
        B=np.zeros((self.n,2)); np.add.at(B,i,w[:,None]*zz[j,None]*rewards)
        U=lu.solve(B); R=np.zeros((len(gates),2)); R[valid]=U[gates[valid]]/z[gates[valid],None]
        dV=np.zeros((len(gates),2)); dR=np.zeros((len(gates),2,2))
        if kind=='non':
            for k in range(2):
                dw=-w*a[:,2+k]/self.theta
                rhs=np.bincount(i,weights=dw*zz[j],minlength=self.n); dz=lu.solve(rhs); dzz=np.r_[dz,0.]
                direct=np.zeros_like(rewards); direct[:,k]=a[:,2+k]
                rhsU=np.zeros_like(U)
                np.add.at(rhsU,i,(dw*zz[j])[:,None]*rewards+(w*dzz[j])[:,None]*rewards+(w*zz[j])[:,None]*direct)
                np.add.at(rhsU,i[keep],dw[keep,None]*U[j[keep]])
                dU=lu.solve(rhsU)
                dV[valid,k]=self.theta*dz[gates[valid]]/z[gates[valid]]
                dR[valid,:,k]=(dU[gates[valid]]-R[valid]*dz[gates[valid],None])/z[gates[valid],None]
        def load(q):
            injection=np.zeros(self.n); np.add.at(injection,gates[valid],q[valid]/z[gates[valid]])
            left=lu.solve(injection,trans='T'); flow=left[i]*w*zz[j]
            return flow
        return V,R,dV,dR,load

class Model:
    def __init__(self,name='small',maas=True,theta=1.,penalty=None,wholesale=None,access_scope='aggregate'):
        self.name=name; self.maas=maas; self.theta=theta; self.access_scope=access_scope
        rows,lines,ods=inputs(name); self.rows=rows; self.ods=np.array(ods); self.total=self.ods[:,2].sum()
        n=max(max(r[:2]) for r in rows); self.n=n
        self.wholesale=np.array(wholesale or ([1.3,1.3] if name=='small' else [1.5,1.]))
        self.penalty=(1. if name=='small' else .5) if penalty is None else penalty
        self.fixed=5 if name=='small' else 2; self.nonpen=10 if name=='small' else 8
        self.t0=[r[4] for r in rows]; self.cap=[r[3] for r in rows]; self.congest=[True]*len(rows)
        road={(r[0],r[1]):k for k,r in enumerate(rows)}
        pt=[]
        for l,line in enumerate(lines):
            for u,v in zip(line[:-1],line[1:]):
                for i,j in [(u,v),(v,u)]:
                    k=road.get((i,j),road.get((j,i))); tm=rows[k][4]*(1.5 if name=='small' else 1.2)
                    idx=len(self.t0); self.t0.append(tm); self.cap.append(1e6); self.congest.append(False); pt.append((l,i,j,idx))
        self.accessM=len(self.t0); self.t0.append(1); self.cap.append(100 if name=='small' else 60000); self.congest.append(True)
        self.accessP=len(self.t0); self.t0.append(2); self.cap.append(500 if name=='small' else 30000); self.congest.append(False)
        am={i:self.accessM for i in range(1,n+1)}; ap={i:self.accessP for i in range(1,n+1)}
        if access_scope=='node':
            for node in range(2,n+1):
                am[node]=len(self.t0); self.t0.append(1); self.cap.append(100 if name=='small' else 60000); self.congest.append(True)
                ap[node]=len(self.t0); self.t0.append(2); self.cap.append(500 if name=='small' else 30000); self.congest.append(False)
        self.t0=np.array(self.t0,float); self.cap=np.array(self.cap,float); self.congest=np.array(self.congest)
        self.nt=len(self.t0); self.nod=len(ods); self.graphs=[]
        for d in sorted(set(self.ods[:,1].astype(int))):
            ids=np.flatnonzero(self.ods[:,1]==d); origins=self.ods[ids,0].astype(int); group={}
            for kind in (['non','drive','maas'] if maas else ['non','drive']):
                edges=[]; gates=[('gate',int(o)) for o in origins]
                def add(s,j,r=-1,c=0,rm=0,rp=0,wm=0,wp=0,tr=0): edges.append((s,j,r,c,rm,rp,wm,wp,tr))
                for k,(i,j,length,cap,tm) in enumerate(rows):
                    add(('M',i),('M',j),k,.2*length if kind=='drive' else 0,length if kind=='non' else 0,0,1,0)
                if kind!='drive':
                    for l,i,j,r in pt: add((l,i),(l,j),r,0,0,1,0,1)
                    for node in range(1,n+1):
                        states=[('M',node)]+[(l,node) for l,line in enumerate(lines) if node in line]
                        for s in states:
                            for j in states:
                                if s!=j: add(s,j,am[node] if j[0]=='M' else ap[node],self.nonpen if kind=='non' else self.penalty,tr=1)
                for o,g in zip(origins,gates):
                    add(g,('M',int(o)),-1 if kind=='drive' else am[o])
                    if kind!='drive':
                        for l,line in enumerate(lines):
                            if o in line: add(g,(l,int(o)),ap[o])
                add(('M',d),('end',d))
                if kind!='drive':
                    for l,line in enumerate(lines):
                        if d in line: add((l,d),('end',d))
                # Arrival terminates immediately, avoiding artificial destination loops.
                edges=[e for e in edges if e[0][1]!=d or e[0][0]=='gate' or e[1]==('end',d)]
                group[kind]=Graph(edges,gates,d,theta)
            self.graphs.append((ids,group))
    def initial(self):
        return np.r_[self.t0+.05,np.full(self.nod,5.) if self.maas else [],[.65,1.4] if self.name=='small' else [.81,3.65]]
    def project(self,y): return np.clip(y,np.r_[self.t0,np.zeros(len(y)-self.nt)],200.)
    def evaluate(self,y,details=False):
        self.last_od=[]
        self.retail_volume=np.zeros(2)
        t=y[:self.nt]; prices=y[-2:]; fares=y[self.nt:-2] if self.maas else np.zeros(self.nod)
        flows=np.zeros(self.nt); profit=np.zeros(3); gradient=np.zeros(2); gp=np.zeros(self.nod); shares=np.zeros(3); welfare=0.; transfers=0.; conservation=0.
        for ids,group in self.graphs:
            kinds=list(group); sol=[group[k].solve(t,prices,self.wholesale,k) for k in kinds]
            if self.maas and getattr(self,'optimize_fares',False):
                vi=sol[kinds.index('maas')][0]; ci=sol[kinds.index('maas')][1].sum(axis=1)
                alt=self.theta*logsumexp(np.array([s[0]-(self.fixed if k=='drive' else 0) for k,s in zip(kinds,sol) if k!='maas'])/self.theta,axis=0)
                fares[ids]=ci+self.theta*(1+lambertw(np.exp(np.clip((vi-ci-alt)/self.theta-1,-700,700))).real)
            values=np.array([s[0]-(self.fixed if k=='drive' else fares[ids] if k=='maas' else 0) for k,s in zip(kinds,sol)]).T
            lv=logsumexp(values/self.theta,axis=1); share=np.exp(values/self.theta-lv[:,None]); q=self.ods[ids,2]; welfare+=q@ (self.theta*lv)
            if details:
                for row,idx in enumerate(ids):
                    self.last_od.append([*self.ods[idx],fares[idx] if self.maas else 0,*(share[row,kinds.index(k)] if k in kinds else 0 for k in ['non','drive','maas']),self.theta*lv[row]])
            non=kinds.index('non'); dv=sol[non][2]
            ds=-share[:,:,None]*share[:,non,None,None]*dv[:,None,:]/self.theta
            ds[:,non,:]+=share[:,non,None]*dv/self.theta
            for b,(k,s) in enumerate(zip(kinds,sol)):
                V,R,dV,dR,load=s; demand=q*share[:,b]; flow=load(demand); g=group[k]
                if k=='non': self.retail_volume+=flow@g.attr[:,2:4]
                mask=g.res>=0; np.add.at(flows,g.res[mask],flow[mask]); transfers+=flow@g.attr[:,6]
                shares[{'non':0,'drive':1,'maas':2}[k]]+=demand.sum()
                # Telescoping flow balance at terminal is an independent loading check.
                conservation=max(conservation,abs(flow[~g.internal].sum()-demand.sum()))
                if k!='drive':
                    profit[:2]+=demand@R
                    for op in range(2): gradient[op]+=np.sum(q*(ds[:,b,op]*R[:,op]+share[:,b]*dR[:,op,op]))
                if k=='maas':
                    margin=fares[ids]-R.sum(axis=1); profit[2]+=demand@margin
                    gp[ids]=demand*(1-margin*(1-share[:,b])/self.theta)
        supply=self.cap.copy(); mask=self.congest
        supply[mask]=self.cap[mask]*(np.maximum(t[mask]/self.t0[mask]-1,0)/.15)**.25
        H=np.r_[supply-flows,-gp if self.maas else [],-gradient]
        self.last_flows=flows
        self.retail_mass=shares[0]
        out=dict(profit_mod=profit[0],profit_pt=profit[1],profit_maas=profit[2],profit_total=profit.sum(),share_non=shares[0]/self.total*100,share_drive=shares[1]/self.total*100,share_maas=shares[2]/self.total*100,price_mod=prices[0],price_pt=prices[1],traveler_welfare=welfare,social_welfare=welfare+profit.sum(),transfer_flow=transfers,flow_conservation_error=conservation)
        return H,out
