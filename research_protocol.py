from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parent
notes=ROOT/'notes'; notes.mkdir(exist_ok=True)
assumptions=[
('initial_pt_wait','2','paper_ambiguous','Appendix A; section 5.1.1','Initial wait not separately identified; unchanged V5'),
('transfer_pt_access','2','paper_explicit','Appendix A','Keep physical access time separate from penalty'),
('mod_access_scope','node','independent_extension','section 5.1.1 / V5 ledger','Literal text favors total aggregation; node is reconstruction baseline, not author setting'),
('pt_access_scope','node','paper_ambiguous','Appendix A','Sharing across nodes/lines not recovered'),
('perturbation','Shannon theta=1, mode_theta=1','paper_ambiguous','section 3.1; follow-up','A specialization, not recovered empirical scale'),
('small_network','appendix lines; road PT capacity 1e6','paper_ambiguous','Appendix A vs figure','Prior topology/physical PT capacity assumptions retained'),
('fixed_OD','1000 total, three OD pairs','paper_explicit','Table 1','No induced total demand'),
('wholesale_E01','MoD=1.3 PT=1.3','paper_explicit','section 5.1.3','Exogenous utilized-link price'),
('transfer_penalty_C','1 vs non-MaaS 10','paper_explicit','Table 2','Physical wait unchanged'),
('transfer_penalty_B','10 for both','independent_extension','E01 handoff','Remove transfer advantage; still a separate priced choice alternative'),
('wholesale_grid','pilot {0,1.5,3} squared; coarse {0,.5,...,3.5} squared','independent_extension','E03 handoff','Illustrative; not empirically calibrated; no bargaining outcome'),
('mode_share','first access edge','paper_ambiguous','Tables 2-3','Not necessarily any paid PT travel'),
('solver','V5 ROOT_AUX plus common active-set cleanup','independent_extension','refine.py','Same algorithm for A/B/C; not original Algorithm 1'),
('equilibrium_deviation','fixed times and other fares','paper_explicit','VI equations 19-22','No traffic-re-equilibrated best response performed'),
('benefit_tolerance','absolute 1e-3 monetary; 1e-8 OD utility','independent_extension','predeclared acceptance','Near-zero aggregate signs marked indeterminate'),
]
with (notes/'assumptions_registry.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['parameter','value','status','source','interpretation']); w.writerows(assumptions)
(notes/'EXPERIMENT_ASSUMPTIONS_V6.md').write_text("""# Frozen research protocol, 2026-11-06

Base: maas-reproduction-v5 ac330d4. Local independent clone. src/model.py and results/v4, results/v5 remain byte-identical. Existing V6 final reproduction is background only; no claim that this handoff starts from that different tag.

G00: six baseline re-evaluations and three legacy verification scripts in a temporary clone. R01: source/implementation/hypothesis registry, no fit to published targets.

E01: small network, A no MaaS, B MaaS penalty 10, C MaaS penalty 1; wholesale (1.3,1.3); all other settings fixed, same ROOT_AUX 100-iteration limit and 3% retail start perturbation. Report B-A, C-B, C-A as sequential equilibrium differences. Telescoping arithmetic is not causal identification.

E03: predeclared pilot {0,1.5,3} x {0,1.5,3}, same C configuration except wholesale prices. Full {0,.5,1,1.5,2,2.5,3,3.5} squared grid is permitted only if all nine pilot runs pass. A pilot failure stops expansion; preserve it rather than tuning to find positive effects. No fine boundary search in this first session. Comparing each to the same A baseline is valid because wholesale prices are unused without MaaS.

Common numerical cleanup: preserve raw solver state; for noncongestible resources with excess delay below 1e-6 and capacity slack above 1e-3 set delay exactly to its lower bound, update conditional MaaS fares, and recompute residuals. This is a boundary numerical operation used for every scenario, not a behavioral calibration. Preserve raw failures. Pass thresholds: natural/scaled VI <1e-6; capacity violation <1e-4, complementarity <1e-3; fixed-time deviation and fare gains <1e-4; conservation/accounting/cost identities <1e-6; normalized FD error <1e-4. Bound 200 must not be active.

Private aggregate benefit: both existing operator profit differences, platform profit, and total traveler utility change exceed +1e-3 => improvement; any below -1e-3 => not improvement; otherwise indeterminate. Also report OD-average utility losses with threshold 1e-8. No government exists, so public Pareto is NOT_APPLICABLE, not a zero-cost government benefit.

Recorded performance includes solver/validation wall-time separately, H/PUMCM calls during solver, evaluation time, process CPU time and sampled RSS. These are local workload observations, not a full M01 benchmark. M01 only supplies a shared original-variable residual and PG/EG/adaptive-EG interface plus smoke checks; no convergence ranking or 18-run benchmark is claimed.

No class heterogeneity, adoption, subsidy, subscription, elastic demand, or network topology changes. No author contact or public upload. Local commits and bundles are the authorized backups for this handoff.
""",encoding='utf-8')
rows=[
('G00','done before E01','legacy scripts + isolated sandbox','hash/check gate','read/CPU low'),
('R01','audit only','V5 ledger + supplied paper','assumptions registry','identifiability'),
('E01','execute','Model penalty + refiner','A/B/C comparisons','nonmonotone solve'),
('E02','backlog','components/Graph attrs','separate friction hypothesis','cost double-counting'),
('E03','execute pilot; gated coarse','wholesale vector + same model','2D points and failure map','zero-price degeneracy'),
('E04','backlog','Graph and shared resource loading','class-specific gradients/weights','factorization expansion'),
('M01','minimal interface only','evaluate/project','PG/EG/shared residual','nonmonotonicity; fair budgets'),
('M02','backlog','solver state and deviation audit','multistart clustering/traffic re-equilibrium','expensive nested responses'),
('E05','backlog','root choice split','availability subgroups','OD conservation'),
('E06','backlog','profit/constraints/ledger','government and fiscal accounts','new game; transfer double-counting'),
('E07','backlog','capacity arrays','one-resource counterfactual','unidentified capacity sharing'),
('M03','backlog','sparse Graph systems','dimension-specific scaling','LU fill-in and memory'),
('E08','backlog','expanded states','transition policy','invalid loops/double fares'),
('E09','backlog','OD fare replaced only after derivation','subscription stage model','new dynamic game'),
('E10','backlog','operator/platform indexing','multiple platforms','new VI and accounting'),
('E11','backlog','fixed q logic','outside option and welfare','baseline comparability')]
(ROOT/'EXPERIMENT_BACKLOG.md').write_text('# Research backlog\n\n| ID | Scope | Dependency | Needed work | Risk |\n|---|---|---|---|---|\n'+'\n'.join('| '+' | '.join(r)+' |' for r in rows),encoding='utf-8')
print('Protocol and assumption registry written')
