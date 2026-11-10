"""Analytic inverse-BPR boundary diagnostics; no equilibrium/model modification."""
from research_v71 import *
def main():
    data=[]
    for flow in [0.,.01,1.]:
        t0=5.;capacity=300.;gamma=1e-4;t=t0+.001
        def h(z):return capacity*(max(z/t0-1,0)/.15)**.25-flow
        for step in range(5):
            half=max(t0,t-gamma*h(t));new=max(t0,t-gamma*h(half));nr=abs(new-max(t0,new-gamma*h(new)))
            data.append(dict(fixed_flow=flow,iteration=step,time=t,predictor=half,corrector=new,iterate_change=abs(new-t),natural_residual=nr,evidence_class='DIAGNOSTIC_ONLY',scope='One isolated scalar inverse-BPR component, not a new network equilibrium'))
            if flow==0:assert new==t and nr>1e-6
            t=new
    outcsv('m01_boundary_microtest.csv',data)
    unused=[]
    for label in ['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage']:
        m,y,r=case(label);used=set(int(v) for _,group in m.graphs for g in group.values() for v in g.res if v>=0)
        for i in range(m.nt):
            if i not in used and m.congest[i]:unused.append(dict(case=label,resource=i,t0=m.t0[i],capacity=m.cap[i],reason='Resource is absent from all destination-pruned graphs; aggregate demand identically zero',evidence_class='DIAGNOSTIC_ONLY'))
    outcsv('m01_unused_congestible_resources.csv',unused)
    components=[]
    for p in (O/'m01_runs').glob('*/metrics.json'):
        r=read(p);m=Model(**r['config']);y=np.load(p.parent/'state.npy');h,_=m.evaluate(y);v=y-m.project(y-1e-4*h)
        used=set(int(q) for _,group in m.graphs for g in group.values() for q in g.res if q>=0)
        for i in np.argsort(abs(v))[-5:][::-1]:components.append(dict(run=p.parent.name,index=int(i),component='traffic' if i<m.nt else 'price',unused_resource=bool(i<m.nt and i not in used),residual_component=float(v[i]),value=float(y[i]),evidence_class='DIAGNOSTIC_ONLY'))
    outcsv('m01_final_residual_components.csv',components)
    (O/'m01_boundary_diagnosis.md').write_text('''# Inverse-BPR boundary micro-diagnostic

Evidence: DIAGNOSTIC_ONLY. The original network and all benchmark iterates are unmodified.

For a zero-flow scalar resource, H(t)=capacity*((t/t0-1)/0.15)^(1/4). With t0=5, capacity=300, t=5.001 and gamma=1e-4, the EG predictor projects to t0. H(t0)=0, so the corrector returns to t=5.001 unchanged. The iterate difference is exactly zero while the natural residual is 0.001. This persists for five explicit updates in the micro-test. Thus small iterate change is not sufficient evidence of VI accuracy for this boundary configuration.

The inverse BPR derivative is unbounded near free flow. This example is outside the usual globally Lipschitz fixed-step EG setting; it does not refute EG convergence theorems or establish an error in the paper. The reconstruction contains destination-pruned unused congestible resources, listed separately; their presence is verified from graph resource indices. Nonzero-flow cases and network price coupling need separate diagnosis. Adaptive EG can avoid this particular stall while still failing the total budget because its common step shrinks.

Possible next tests: mathematically eliminate identically unused resources at their exact lower bound, or introduce a justified scaling/coordinate reformulation. Any such variant must be separately labeled and satisfy the same physical and economic acceptance contract; it is not silently applied to the reported original-variable benchmark.
''',encoding='utf-8')
if __name__=='__main__':main()
