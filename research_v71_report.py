"""Generate v7.1 bilingual Markdown reports, figures, dictionaries and claim ledger."""
from research_v71 import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
def tab(headers,data):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(x) for x in r)+' |' for r in data])
def num(x):return f'{float(x):,.3f}' if np.isfinite(float(x)) else 'not available'
def main():
    fig=O/'presentation_figures';fig.mkdir(exist_ok=True)
    static=csvread(O/'e01_placebo_static.csv');econ=csvread(O/'e03_all_results_reaudited.csv');phys=csvread(O/'pt_physical_flow_vs_sales_channel.csv');bench=csvread(O/'m01_convergence_runs.csv');edges=csvread(O/'e03_local_boundary.csv');nested=csvread(O/'m03_same_vi_prototype.csv');probes=csvread(O/'m02_timing_comparison.csv');cost=csvread(O/'e03_cost_participation.csv')
    combos={}
    for r in static:combos.setdefault((r['frozen_state'],r['choice_set']),0.);combos[(r['frozen_state'],r['choice_set'])]+=float(r['weighted_utility'])
    stattable=tab(['Frozen state','Choice set','Total expected utility'],[[a,b,num(v)] for (a,b),v in combos.items()])
    agg={}
    metrics_names=['initial_pt','pt_vehicle_link_traversals','pt_paid_links','any_actual_pt_trips','actual_mod_and_pt_trips','initial_pt_but_no_pt_ride','pt_passenger_distance_model_units','pt_boarding_events','pt_pt_transfers']
    for r in phys:
        a=agg.setdefault((r['run'],r['kind']),{k:0 for k in metrics_names})
        for k in a:a[k]+=float(r[k])
    outcsv('pt_channel_summary.csv',[dict(run=k[0],channel=k[1],**v,evidence_class='REPRODUCED_MECHANISM') for k,v in agg.items()])
    ptable=tab(['Case/channel','First PT','PT ride-links','PT-using trips','MoD+PT trips'],[[k[0].replace('E01/','').replace('V5/','')+' / '+k[1]]+[num(v[q]) for q in ['initial_pt','pt_vehicle_link_traversals','any_actual_pt_trips','actual_mod_and_pt_trips']] for k,v in agg.items() if not k[0].startswith('E03') and k[1]!='drive'])
    ptotals=[]
    for label in ['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage']:
        selected=[v for (run,channel),v in agg.items() if run=='E01/'+label]
        ptotals.append([label]+[num(sum(v[q] for v in selected)) for q in ['initial_pt','any_actual_pt_trips','pt_vehicle_link_traversals','actual_mod_and_pt_trips']])
    ptotal=tab(['Case total','First PT','PT-using trips','PT ride-links','MoD+PT trips'],ptotals)
    costsummary=[]
    for ct,v in sorted({(r['cost_type'],float(r['parameter'])) for r in cost}):
        chosen=[r for r in cost if r['cost_type']==ct and float(r['parameter'])==v]
        costsummary.append(dict(cost_type=ct,parameter=v,L1=sum(r['L1_after_cost']=='True' for r in chosen),L2=sum(r['L2_after_cost']=='True' for r in chosen),evidence_class='DIAGNOSTIC_ONLY'))
    outcsv('e03_cost_summary.csv',costsummary);ctable=tab(['Cost structure','Parameter','L1 points','L2 points'],[[r[k] for k in ['cost_type','parameter','L1','L2']] for r in costsummary])
    bt=tab(['Case','Method','Start','Status','Natural residual','H solver/total','Seconds'],[[r['case'],r['method'],r['initial_factor'],r['status'],f"{float(r['natural_direct']):.3g}",r['solver_h_calls']+'/'+r['total_h_calls'],num(r['solver_seconds'])] for r in bench])
    ntable=tab(['Method','Status','H calls','PUMCM','Inner solves','Full scaled','Wall (s)'],[[r['method'],r['status'],r['total_h_calls'],r.get('total_pumcm_calls',''),r['inner_solves'],f"{float(r['full_scaled']):.3g}" if r['status']=='PASS' else 'not available',num(r['seconds'])] for r in nested])
    et=tab(['MoD wholesale','PT wholesale','Status','PT revenue gain','L1','L2'],[[r[k] if k!='delta_pt' else num(r[k]) for k in ['c_mod','c_pt','status','delta_pt','L1','L2']] for r in edges])
    st=tab(['Contract','Operator','Price factor','Fixed-time gain','Traffic-response gain'],[[r['scenario'],r['operator'],r['price_factor'],num(r['fixed_time_gain']),num(r['reequilibrated_gain'])] for r in probes if float(r['price_factor'])!=1])
    stats=csvread(O/'g02_pass_statistics.csv');gt=tab(['Check (75 original PASS)','Median','95th percentile','Max'],[[r['metric']]+[f"{float(r[k]):.3g}" for k in ['median','p95','maximum']] for r in stats])
    # Figures are discrete diagnostics, no interpolated equilibria.
    f,ax=plt.subplots(figsize=(9,4));labs=['A: actual B product','A: independent clone','A: corrected clone','B: actual B product']
    values=[combos[('A','actual_B_product_B_fares')]-combos[('A','no_maas')],combos[('A','independent_clone')]-combos[('A','no_maas')],0,combos[('B','actual_B_product_B_fares')]-combos[('B','no_maas')]]
    ax.bar(labs,values,color=['#21618c','#bb7346','#418a64','#21618c']);ax.set_ylabel('Expected utility sum; fixed scale = 1');ax.set_title('DIAGNOSTIC_ONLY: frozen-state comparisons, not additive causal effects');ax.tick_params(axis='x',labelsize=8);f.tight_layout();f.savefig(fig/'e01_actual_vs_placebo.png',dpi=180);plt.close(f)
    f,axes=plt.subplots(1,2,figsize=(9,4))
    for ax,level in zip(axes,['L1','L2']):
        mat=np.zeros((8,8))
        for r in econ:mat[round(float(r['c_mod'])*2),round(float(r['c_pt'])*2)]=-1 if r['status']!='PASS' else int(r[level]=='IMPROVING')
        ax.imshow(mat,origin='lower',vmin=-1,vmax=1,cmap=ListedColormap(['#666666','#ecdcc8','#2b8965']));ax.set_xticks(range(8),[x/2 for x in range(8)]);ax.set_yticks(range(8),[x/2 for x in range(8)]);ax.set_xlabel('PT wholesale');ax.set_ylabel('MoD wholesale');ax.set_title(level+' | original discrete grid')
    f.suptitle('REPRODUCED_MECHANISM: green improvement; gray original failure',fontsize=10);f.tight_layout();f.savefig(fig/'e03_levels.png',dpi=180);plt.close(f)
    f,axes=plt.subplots(1,3,figsize=(13,4),sharey=True)
    for ax,c in zip(axes,['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage']):
        for r in bench:
            if r['case']!=c or float(r['initial_factor'])!=1:continue
            trace=read(O/'m01_runs'/f"{c}_{r['method']}_1"/'trace.json');ax.semilogy([v['wall_seconds'] for v in trace],[v['natural_residual'] for v in trace],label=r['method'])
        ax.axhline(1e-6,color='black',ls='--');ax.set_title(c.split('_')[0]);ax.set_xlabel('Wall seconds');ax.grid(alpha=.2)
    axes[0].set_ylabel('Natural residual, gamma=1e-4');axes[0].legend(fontsize=8);f.suptitle('DIAGNOSTIC_ONLY: matched original-variable algorithms; start factor 1');f.tight_layout();f.savefig(fig/'m01_residual_vs_walltime.png',dpi=180);plt.close(f)
    # Two axes: physical ridership and sales-channel split, small A/B/C.
    f,axes=plt.subplots(1,2,figsize=(10,4));names=['A_no_maas','B_maas_no_transfer_advantage','C_maas_paper_advantage']
    for j,name in enumerate(names):
        k='E01/'+name;non=agg.get((k,'non'),{});maas=agg.get((k,'maas'),{})
        axes[0].bar(j,non.get('any_actual_pt_trips',0),color='#2471a3',label='non-MaaS' if j==0 else None);axes[0].bar(j,maas.get('any_actual_pt_trips',0),bottom=non.get('any_actual_pt_trips',0),color='#229954',label='MaaS' if j==0 else None)
        axes[1].bar(j,non.get('pt_vehicle_link_traversals',0)+maas.get('pt_vehicle_link_traversals',0),color='#a36e35')
    for ax in axes:ax.set_xticks(range(3),['A','B','C']);ax.set_xlabel('November small-network scenario')
    axes[0].set_ylabel('Trips with actual PT riding');axes[0].legend();axes[1].set_ylabel('Passenger PT-link traversals');f.suptitle('REPRODUCED_MECHANISM: physical use and sales channels are different metrics');f.tight_layout();f.savefig(fig/'pt_physical_vs_channel.png',dpi=180);plt.close(f)
    hits=[]
    for p in (O/'m01_runs').glob('*/metrics.json'):
        r=read(p);hit=r['first_iterate_tol_hit']
        if hit:hits.append(dict(case=r['case'],method=r['method'],factor=r['initial_factor'],**hit,evidence_class='DIAGNOSTIC_ONLY'))
    outcsv('m01_iterate_vs_natural.csv',hits)
    fails=sum(r['status']!='PASS' for r in bench);passes=len(bench)-fails
    ledger=[dict(claim_id='R00-'+r['claim_id'],evidence_class=r['evidence_class'],test_id='R00',result_ref='paper_defense_ledger.csv',limits=r['remaining_validation'],presentation_safe_claim=r['presentation_safe_claim']) for r in csvread(O/'paper_defense_ledger.csv')]
    for cid,ec,test,ref,limit,claim in [
      ('N01','DIAGNOSTIC_ONLY','E01-P','e01_placebo_static.csv','Static cross states are not new equilibria or causal decomposition.','The implemented upper Shannon choice is sensitive to independent service duplication.'),
      ('N02','REPRODUCED_MECHANISM','E02-PT','pt_physical_flow_vs_sales_channel.csv','Model distance units are not verified km; first access is not ridership.','Actual PT use and payment-channel labels must be reported separately.'),
      ('N03','REPRODUCED_MECHANISM','E03-D','e03_welfare_levels.csv','November node/node baseline and original auxiliary residual acceptance.','31 aggregate improving points contain only 14 all-OD-mean nonworse points.'),
      ('N04','NOT_IDENTIFIED','E03-D','e03_welfare_levels.csv','No individual utility distribution or panel outcomes.','Individual Pareto improvement is not identified.'),
      ('N05','DIAGNOSTIC_ONLY','E03-V','e03_cost_summary.csv','Illustrative costs; no measured commercial model or re-equilibrium.','Participation depends on the assumed additional cost structure.'),
      ('N06','FAILED_NUMERICAL_CHECK' if fails else 'DIAGNOSTIC_ONLY','M01','m01_convergence_runs.csv','Independent reconstruction differs from author settings; bounded budget, no theorem refutation.',f'{passes}/{len(bench)} tested projection runs passed the specified contract.'),
      ('N07','NEW_COUNTERFACTUAL','M02','m02_timing_comparison.csv','Different response timing, finite probes and fixed rival/platform prices.','Re-equilibrating traffic can reverse the gain from a price increase.'),
      ('N08','DIAGNOSTIC_ONLY','M03','m03_same_vi_prototype.csv','Warm-start small example; numerical elimination comparison, not total-derivative leader game.','Nested and joint methods must solve the same final residual before timing ratios are interpretable.')]:ledger.append(dict(claim_id=cid,evidence_class=ec,test_id=test,result_ref=ref,limits=limit,presentation_safe_claim=claim))
    outcsv('claim_evidence_ledger.csv',ledger)
    (O/'pt_metric_dictionary.md').write_text('''# PT metric dictionary

Evidence class: REPRODUCED_MECHANISM. November source states, V5 node/node Sioux states; no substitution of October v6 data.

| Field | Definition and unit | Limitation |
|---|---|---|
| initial_pt | Expected flow on gate-to-PT access links, by sales channel | Not proof of a PT vehicle ride |
| pt_vehicle_link_traversals | Flow summed over edges with same PT line at both ends | Passenger-link count, not unique persons |
| pt_paid_links | Non-MaaS retail/PT or MaaS wholesale/PT attributes times flow | Equals PT ride links only in this link-priced specialization |
| pt_boarding_events | Entries from gates or another service/line into PT state | Repeated entries count; a ride need not follow |
| pt_pt_transfers | Cross-line PT state transitions | Not PT-MoD transfer count |
| any_actual_pt_trips | Demand weighted probability of at least one PT ride edge | Absorbing-chain event probability, not access-flow proxy |
| actual_mod_and_pt_trips | Probability of both MoD road and PT ride edges, inclusion-exclusion | Expected mixed-mode trips, no realized individual trajectories |
| initial_pt_but_no_pt_ride | PT initial access followed by no PT ride edge | Quantifies access-only misclassification |
| pt_passenger_distance_model_units | Ride-link flow times reconstructed lengths | Not verified passenger-km; Sioux uses V5 proxy lengths |

The event calculation uses an absorbing Markov kernel recovered from positive gate injections. Removing event transitions gives avoidance probability via a linear system; inclusion-exclusion yields the both-mode event. Probability and accounting identities are independently checked. Non-MaaS supports multimodal travel; a change of channel is not automatically a physical-mode change.

Paper Table 2 PT-share sums remain 25.5% and Table 3 changes 10.6% to 28.6%. These rounded aggregate labels do not assert unchanged PT flow on every link or OD. Figure 6 / section 5.1.3 explicitly describes local OD(1,5) PT growth. Mapping those shares to this code's first-access metric remains unresolved.
''',encoding='utf-8')
    (O/'market_scenarios.md').write_text('''# Market scenarios: dependency-gated design

Status: NOT_RUN / DESIGN_ONLY. Evidence: UNRESOLVED_SPECIFICATION or EXTERNAL_CONTEXT when external data are later introduced. No Lausanne market calibration is claimed.

1. E10 lower MoD baseline: choose service constants or access assumptions before MaaS entry; calibrate only an explicit hypothetical pre-entry share. Freeze the same conditions for entry comparison. Do not tune to recover a desired platform profit. The original single road-wide MoD definition is acknowledged; no rebalancing or driver-cost model is claimed.
2. E11 fare integration: per-link baseline versus per-boarding or trip-valid PT ticket requires paid/unpaid state and transfer rules. Verify ticket-once accounting, graph cycles, sensitivities and state-space cost before equilibrium experiments. Lower non-MaaS PT-PT penalties must be distinguished from extra MaaS convenience.
3. E04-C: separate route and service-scale tests; keep monetary utility coefficient/normalization explicit. Correlated service-choice nests are design hypotheses, not an estimated truth. For equal-mean heterogeneity, class probabilities, gradients and flows must all feed shared physical congestion. OD VOT variation is already in the paper; within-OD distributions are a distinct extension.
4. E05: eligible/ineligible MaaS subpopulations and driving availability require consistent denominators. Eligibility is not paid subscription or observed adoption. Do not invent registration fees.
5. E06: hypothetical platform cost or public PT fare-cap post-processing is not a government game. A strategic government needs objective, budget and transfer accounting; policy re-equilibrium must be separately solved.
6. E07: participation/outside-option restrictions define a feasible bargaining set; they do not select a Nash bargaining solution. The authors already acknowledge negotiation and revenue-sharing questions.
7. E09: PAYG plus subscription and within-trip payment mixing need participation/repeated-trip and payment-history states. Multiple platforms, elastic demand and endogenous supply are further model changes, not omissions the authors failed to recognize.

Gate: establish a robust numerical contract and validated small-network computation before structural extensions. No Swiss fare facts are asserted without a future official-source check.
''',encoding='utf-8')
    (O/'m03_comparability.md').write_text('''# M03 comparability contract

Evidence class: DIAGNOSTIC_ONLY. Two prototypes solve the same original fixed-time partial-derivative price residual. JOINT_AUX solves the full traffic-ratio/fare/retail system; NESTED_SAME_VI solves physical traffic inside each outer residual evaluation. Both start from contract (1.5,1.5) reference times with all prices increased 3%. Neither is the original EG algorithm.

The outer numerical Jacobian may differentiate a composed residual to find its zero. This does not turn the leader objective into profit(t*(p),p). A leader optimizing that composed profit would use total strategic derivatives and can define a different game: NOT_COMPARABLE with the original VI without further argument. This is why M02 gains are not automatic Nash violations.

Acceptance requires full VI/physical residuals and inherited finite price-deviation audits, not least_squares.success alone. The complete prototype records inner failures, every H call (including numerical Jacobian and validation) and graph solves. Timings include instrumentation and validation. One warm-start small case cannot establish universal VTO superiority or large-network speedup. PG/EG comparisons remain M01 and are not substituted for this comparison.
''',encoding='utf-8')
    source='Source: supplied Yao, Ma & Zhang (2026), TRC 188, 105703, DOI 10.1016/j.trc.2026.105703; pp.2-19, especially Sections 2-6 and Appendix A. Page-specific paraphrases and source hash: paper_defense_ledger.csv. November source tag research-handoff-20261108; independent code rooted in maas-reproduction-v5. v7.1 request is a work specification, not original-paper evidence.'
    en=f'''# MaaS Research v7.1: technical review and experimental validation

2026-11-10 | Positive contribution, precise validation questions, bounded evidence

## Findings at a glance

This is a completed bounded validation study, not an exact reproduction of all paper results. The frozen actual-product increment is {values[0]:.3f}, whereas identical independent duplication gives {values[1]:.3f}; they are different experiments. Of 63 accepted contract points, 31 improve aggregate interests and only 14 avoid mean-utility losses in every OD. Actual projection convergence acceptance is {passes}/{len(bench)}. Joint/nested results below are a separate small warm-start prototype, not a repair of failed EG trajectories. Remaining differences in access-demand aggregation and stopping conventions prevent attribution of our numerical failures to the authors. Market extensions and large-network benchmark expansion remain gated.

## Contribution and source audit

The paper supplies a motivated dual traffic/virtual-operator formulation, differentiable PUMCM follower responses, VI conditions and existence analysis, numerical EG results and several sensitivity experiments. Our review begins by acknowledging these contributions. R00 checks 21 issues, including the 18 requested topics and three additional qualifications. Non-MaaS explicitly permits multimodal travel. A single road-wide MoD operator is defined. Transfer convenience has a qualitative rationale. Small wholesale sensitivity is symmetric but Sioux wholesale prices differ. Travelers maximize their own utilities; aggregate Pareto language is a comparison, not their collective objective. Section 6 recognizes negotiation, demand and platform extensions, while Section 5.1.5 already varies OD VOT.

Two source-to-code issues must not be hidden. Page 10 explicitly aggregates MoD access across the network, whereas our preserved November baseline uses node/node resources; these are conditional reconstruction outcomes. Also page 10 describes consecutive-iterate differences, while Appendix A specifies a projected natural residual. Both are recorded in M01. Page 7 explicitly distinguishes nonconvex optimization from its necessary VI condition; passing residuals is not a proof of global Nash optimality. Neither the paper nor this study is a Lausanne empirical calibration.

## G00-G02: integrity and numerical contract

All 76 November attempts were reevaluated, including the original failure. Economic metrics match within 1e-6. The 75 original PASS states pass their auxiliary-coordinate criteria; 15 exceed 1e-6 if rounded times are directly inverted. No threshold was relaxed or old failure relabeled. The inverse BPR map is ill-conditioned near free flow; direct and retained-coordinate residuals are therefore both exported. Fixed-time deviation statistics below reference the hash-verified original audits; economic, traffic and accounting values were freshly recomputed.

{gt}

## E01-P: static product versus duplication tests

Static tests freeze A or B times and retail prices. The actual-B-product cross uses B's OD MaaS fares and transfer penalty 10; the clone exactly copies the systematic non-MaaS value. Independent duplication gives mu*log(1+p_non); two copies each shifted by -mu*log(2) preserve inclusive value and combined probability. Twelve analytic unit tests cover three mode scales and extreme utility differences. These are diagnostics of the implemented upper Shannon layer, not all PUMCM perturbations.

{stattable}

![Frozen-state choice diagnostics](presentation_figures/e01_actual_vs_placebo.png)

The A-frozen actual-product increment is {values[0]:.3f}, versus {values[1]:.3f} for the independent identical clone; the B-frozen actual-product increment is {values[3]:.3f}. The original equilibrium B-A remains 103.287. Different conditioning paths do not identify causal shares, and no clone increment is subtracted from the equilibrium gain. A and B references reproduce their equilibria; crossed states are not equilibria. No new placebo re-equilibrium file is fabricated. Nested/correlated alternatives remain design hypotheses without calibration data.

## E02-PT: physical use and sales channels

The PT dictionary distinguishes first access, actual ride links, paid links, boarding events, distance proxies and probability of actual PT/MoD joint use. Event probabilities are obtained from absorbing Markov kernels, not inferred from access totals. Small A/B/C and 63 accepted November coarse cases are recomputed; V5 node/node Sioux states are separately identified. October v6 is not substituted.

{ptable}

{ptotal}

PT-using trips and ride-link traversals need not move in the same direction. These reconstructed totals also do not reproduce the paper's PT market-share level exactly; separating indicators diagnoses interpretation, rather than erasing that quantitative discrepancy.

![Physical use versus channels](presentation_figures/pt_physical_vs_channel.png)

Table 2's unchanged aggregate PT share is compatible with the paper's stated OD(1,5) increase; it does not imply identical PT flows everywhere. Table 3 has a different network/demand setting. Reconstructed distance is reported in model units, not validated passenger-km. The paper's exact market-share reporting convention is not assumed identical to this code's first-access shares.

## E03-D/V: distribution, local boundary and hypothetical costs

The original 63 accepted coarse cases retain 31 L1 aggregate improving and 14 L2 all-OD-mean nonworse cases. L3 individual Pareto remains NOT_IDENTIFIED. Strict aggregate tolerance is 0.001; OD nonworse tolerance is 1e-8. Revenue decomposition reconciles retail changes plus wholesale receipts with operator gains. OD fares, sales, wholesale payments, losses and demand shares are exported. The original (3.5,1.5) failure remains excluded; v7's separately accepted neighbor-start diagnosis is freshly reevaluated and labeled diagnostic.

![Discrete welfare levels](presentation_figures/e03_levels.png)

Nine predeclared local points, MoD={{1.4,1.5,1.6}} and PT={{0.7,0.8,0.9}}, test the coarse PT participation transition without interpolation or sign-target fitting:

{et}

Additional platform costs are deliberately hypothetical and applied after equilibrium. They represent fixed, per-MaaS-trip or revenue-proportional costs; they are not estimated operating costs or endogenous exit decisions.

{ctable}

The feasible participation set changes with cost structure. The two-dimensional grid is not a solved wholesale negotiation game. Revenue-dependent costs and fixed costs should not be conflated.

## M01: completed attempts, convergence outcome

Each method uses the same original H/project, initial step 1e-4, natural gamma 1e-4, 1e-6 target and 20,000 solver-H budget. A/B/C each have initial factors 0.95, 1, 1.05. Adaptive halving uses eta=0.7 and counts rejected evaluations. Every run is a separate sequential process, with BLAS/OMP/MKL threads set to one; validation calls are separate from the solver budget but included in total H/graph counts. The whole operator-event CSV is retained, not just iteration counts. Memory is sampled process RSS, not a guaranteed instantaneous peak. CPU/wall include instrumentation and normal local-machine activity.

{bt}

![Natural residual versus wall time](presentation_figures/m01_residual_vs_walltime.png)

Observed acceptance: {passes}/{len(bench)}. Failed iterate prices and revenues are diagnostic only. All performed attempts are recorded; the requested successful time-to-convergence comparison is not achieved if methods remain failed. No equivalence with the author's numerical settings, universal ranking, nonexistence or multiple-equilibrium claim follows. {len(hits)} runs have an observed iterate-change threshold crossing; m01_iterate_vs_natural.csv records their natural residual at that crossing, exposing why the two stopping descriptions need to be distinguished. Sioux and additional contract cases are NOT_RUN where the small-network convergence gate is not met.

## M02 and M03: strategic versus numerical nesting

Twelve new finite -5%, 0%, +5% retail-price probes at (1.5,1.5) and (3,3) keep rival retail and MaaS fares fixed. Re-equilibrated traffic is a different response-timing counterfactual; the original fixed-time deviation is not replaced.

{st}

The same-VI nested prototype retains original partial price derivatives while solving traffic internally. The joint auxiliary comparator uses explicit fares too; no exact-fare shortcut substitutes for a competing algorithm. These are numerical solution strategies for the same stationary conditions, not a full comparison against leaders optimizing total profit derivatives through traffic equilibrium.

{ntable}

Only if both final validations pass are their timings comparable within this warm-start toy example. If either fails, the performance comparison is NOT_COMPARABLE. Even success is not evidence of general large-network speedup. Full settings and caveats are in m03_comparability.md.

## Deferred market extensions and reproducibility

E10 lower MoD prevalence, E11 integrated tickets, E04-C correlation/heterogeneity, E05 availability, E06 public finance and E07/E09 negotiation/product extensions remain dependency-gated. The design notes specify shared congestion, monetary normalization, payment history and participation conditions. No market data, subscription fee or public objective is invented. The priority is a reliable numerical/behavioral comparison before adding structural assumptions.

Code, raw states, all operator events, CSVs, figures, input hashes, protocol and failure records are in the new local branch research-v7-1-critical-validation. Original V5/V6/research_v6/v7 outputs and tags are preserved. No remote push or author contact. See README_RESEARCH_V7_1.md for replay and recovery, and claim_evidence_ledger.csv for presentation-safe statements.

{source}
'''
    ko=f'''# MaaS Research v7.1 상세 검토 및 실험 보고서

2026년 11월 10일 | 저자의 설명을 먼저 확인한 조건부 재현·검증

**판정:** 이번 명세에 따른 제한된 검증 연구를 완료했으며, 논문 전체의 정밀 재현 성공을 뜻하지 않습니다. 고정 상태에서 실제 B 상품 추가 효과는 {values[0]:.3f}, 동일 독립 대안 복제는 {values[1]:.3f}로 서로 다른 실험입니다. 유효 계약 63점 중 총량 공동 개선은 31점이고 모든 OD 평균 비악화는 14점입니다. 실제 투영 반복의 기준 통과는 {passes}/{len(bench)}입니다. 아래 joint/nested 시범은 별도의 작은 warm-start 실험이며 실패한 EG 궤적을 수정한 결과가 아닙니다. 원문과 접근수요 집계·종료지표 차이가 남아 있으므로 이 실패를 저자의 알고리즘 실패로 귀속하지 않습니다. 시장모형 확장과 대규모 벤치마크는 게이트 이후 과제로 남겼습니다.

## 1. 이번 업데이트의 핵심

이번 작업에서는 원문이 실제로 정의하고 설명한 내용을 먼저 인정한 뒤, 아직 검증되지 않은 현실성 가정을 분리했습니다. 저자는 전 도로망을 운행하는 단일 MoD를 정의했고, non-MaaS 내부에서도 PT와 MoD의 결합을 허용합니다. MaaS의 계획·환승 불편 감소에는 정성적 근거를 제시하며, Small의 공통 도매가격 실험과 Sioux의 상이한 도매단가도 구분됩니다. 여행자의 목표는 자기 기대효용 극대화이고 공동 Pareto 개선은 사후 비교입니다. OD별 VOT 민감도와 150개 초기값 교란 실험, 탄력·이질 수요와 복수 플랫폼 등의 후속과제도 실제로 존재합니다.

따라서 검토 질문은 ‘이런 내용을 언급하지 않았다’가 아니라 ‘그 설명만으로 현실 시장의 정도·분포·의사결정 시점까지 검증되었는가’입니다. R00은 요청된 18개 쟁점에 접근 수요 집계, 종료 잔차, VI와 글로벌 최적성의 관계를 더해 21개 근거 원장을 작성했습니다. 원문의 이론·모형 정의, 수치실험, 경험적 검증은 서로 다른 근거입니다. 스위스나 로잔 통합운임은 향후 외부 적용 시나리오이며 원 논문의 실증 대상이 아닙니다.

## 2. 원문과 독립 재구현 사이의 차이

원문 p.10의 MoD 접근시간은 전체 MoD 수요에 따른 동질적 접근시간입니다. 그러나 보존한 11월 기준선은 node/node 집계를 사용합니다. 이는 저자의 미정의 항목이라고 돌릴 수 없는 독립 재구성의 차이입니다. 이번 결과를 저자 설정의 정확한 복원으로 부르지 않습니다.

또한 p.10은 연속 반복값 차이를 잔차로 설명하고 p.19 Appendix A는 자연 투영 잔차를 명시합니다. EG에서는 두 값이 일반적으로 같지 않습니다. 이번에는 실제 반복 변화량과 고정 gamma=1e-4의 자연 잔차를 모두 기록합니다. 이 두 설명의 차이를 저자의 이론 오류로 단정하지 않고, 정량적 수렴 비교에서 해결해야 할 명세 문제로 남깁니다.

p.7은 비볼록 플랫폼 최적화와 그 VI 조건이 동치가 아님을 직접 설명합니다. 최적해가 VI를 만족한다는 것과 VI 잔차가 작은 모든 후보가 전역 이윤최대라는 것은 다릅니다. 이를 원문이 인식하지 못했다고 비판하는 대신 독립적인 가격 이탈 검사를 유지하는 것이 타당합니다.

## 3. G00-G02: 원본 보존과 PASS 검증

11월 76개 시도 전체를 재평가했으며 경제적 지표는 저장값과 1e-6 이내로 일치했습니다. 기존 PASS 75개는 원래 보조 좌표 기준을 통과했고 실패 1개는 그대로 남겼습니다. 직접 시간 역변환 잔차가 기준을 넘는 15개는 v7에서 이미 발견한 수치 표현 문제이며 이번에도 구분해 기록했습니다. 고정시간 가격 이탈 통계는 해시 검증된 원래 감사 결과를 참조하고, 경제·교통·회계 값은 새로 계산했습니다.

{gt}

이 표의 분포는 실패를 섞은 최대값이 아니라 기존 PASS 집합의 중앙값·95분위수·최댓값입니다. BPR의 자유류 부근에서 시간을 유량으로 역변환하면 반올림 오차가 커질 수 있으므로 직접 잔차와 저장된 보조 유량좌표 잔차를 섞어 쓰지 않았습니다. 기준을 느슨하게 바꾸거나 기존 FAIL을 삭제하지 않았습니다.

## 4. E01-P: 실제 상품구조와 동일 대안 복제의 구분

A 또는 B의 시간·소매가격을 고정한 뒤 상위 선택집합을 비교했습니다. actual B product는 B의 MaaS OD 요금과 환승 페널티 10을 사용하는 실제 코드의 상품입니다. independent clone은 non-MaaS 체계적 효용을 정확히 복제한 가상 대안입니다. split corrected는 각 복제 대안의 효용에서 mu_mode*log(2)를 빼는 불변성 진단입니다. 루트 척도와 모드 척도는 현재 모두 1이며, 분석적 불변성 검사는 모드 척도 0.2/1/3과 극단 효용 조합을 포함한 12개 테스트를 통과했습니다.

{stattable}

![실제 상품과 정적 복제 비교](presentation_figures/e01_actual_vs_placebo.png)

A 상태를 고정하면 실제 B 상품 추가의 기대효용 증가는 {values[0]:.3f}, 독립 동일 복제는 {values[1]:.3f}입니다. B 상태에서 실제 상품 추가 효과는 {values[3]:.3f}입니다. 원래 재균형 A→B 차이는 여전히 103.287입니다. 고정 조건과 상품 정의가 다르므로 575.18을 103.29에서 차감하거나 ‘인공 편익 비중’을 계산하지 않습니다. A/B 기준 참조만 균형이고 교차 조합은 균형이 아닙니다. 수행하지 않은 placebo 재균형 파일도 만들지 않았습니다.

이 진단은 구현된 상위 Shannon 선택의 중복 민감도에 관한 것입니다. 일반 PUMCM 전체가 IIA를 강제한다는 주장을 하지 않습니다. Nested/cross-nested 구조는 자료가 없는 현 단계에서 설계 가설이며, 그 자체가 현실적 정답이나 교정된 수요모형은 아닙니다.

## 5. E02-PT: 접근·물리 이용·판매채널

첫 PT 접근과 실제 PT 차량 링크 통과, PT 유료 링크, 승차·환승 사건, 실제 PT 이용 통행과 MoD/PT 결합 통행을 나누었습니다. 결합 통행은 접근량을 합쳐서 구한 것이 아니라 흡수 Markov 과정의 사건 확률을 계산해 식별합니다. 확률과 회계 항등식 검증을 함께 수행합니다.

{ptable}

{ptotal}

실제 PT 이용 통행 수와 차량 링크 통과량은 같은 방향으로 움직이지 않을 수 있습니다. 이 재구현의 PT 수준은 원문 시장분담 수준과도 정확히 일치하지 않습니다. 지표 분리는 해석을 정교하게 만드는 것이며 수치 차이 자체를 해소한 것은 아닙니다.

![PT 물리 이용과 결제채널](presentation_figures/pt_physical_vs_channel.png)

Small의 A/B/C, 원래 유효 E03 격자, 별도 표시된 V5 Sioux before/after를 진단했습니다. 10월 최종 v6를 11월 원시 자료로 대체하지 않았습니다. 실제 거리단위가 외부적으로 검증되지 않았으므로 passenger-km 대신 모형 길이 단위의 누적 거리를 제공합니다.

원문 Table 2의 PT 분담 합계 25.5% 유지와 §5.1.3의 OD(1,5) 국소 PT 증가 설명은 양립할 수 있습니다. 전체 합계가 같다고 모든 PT 차량 링크 유량이 동일했다고 주장해서는 안 됩니다. Table 3의 10.6%→28.6% 역시 다른 네트워크·수요 아래의 결과입니다. 원문의 시장분담 지표가 본 코드의 첫 접근 지표와 정확히 같은지는 확정하지 않았습니다.

## 6. E03-D/V: 계약·수익·분배와 비용 형태

원래 63개 유효 격자에서 L1 총량 공동 개선은 31점, 모든 OD 평균이 비악화인 L2는 14점입니다. L3 개인별 Pareto 개선은 NOT_IDENTIFIED입니다. 총량 기준은 +0.001 초과, OD 비악화는 1e-8 오차를 적용합니다. 소매수입 변화와 도매수입을 합해 운영자 총수익 변화가 되는지 검증하고, MaaS OD 요금매출과 도매지급, OD 손실과 해당 수요 비중을 별도 CSV로 제공합니다.

![L1과 L2](presentation_figures/e03_levels.png)

기존 PT 참여조건 전환 구간에 MoD 1.4/1.5/1.6 × PT 0.7/0.8/0.9의 9개 점을 사전 등록해 추가 계산했습니다. 원하는 부호가 나올 때까지 탐색하지 않았고 격자 사이를 균형으로 보간하지 않았습니다.

{et}

기존 실패 (3.5,1.5)는 원래 격자에서 제외한 채 보존합니다. 이웃점 시작으로 통과했던 v7의 별도 해도 새로 재평가해 진단으로 연결했으며 원래 63/64 판정을 바꾸지 않았습니다.

{ctable}

플랫폼 추가비용은 고정비용, MaaS 통행당 비용, 매출비례 비용으로 나누었습니다. 실제 운영비 추정이나 시장 이탈을 포함한 재균형 결과가 아니라 사후 참여조건 진단입니다. 예를 들어 비용 형태가 달라지면 동일한 양의 잔여수익이라도 통과 여부가 달라집니다. 이는 상업적 지속가능성이 입증됐다는 뜻이 아닙니다. 2차원 개선영역도 내생 협상가격의 해가 아니며 저자가 이미 논의한 참여조건·협상 문제의 확장입니다.

## 7. M01: 동일 조건 실제 반복 비교

A/B/C 각각에 초기값 배율 0.95/1/1.05를 적용하고 PG·고정 EG·적응형 EG를 실행했습니다. 모든 방법은 같은 H와 제약, 초기 step 1e-4, 자연 잔차 gamma=1e-4, 기준 1e-6, solver H 예산 20,000회를 사용합니다. 적응형의 거절 평가도 포함하고 최종 검증 H는 solver 예산과 구분해 전체 호출수에 포함합니다. 원문의 EG를 보조 root 해로 대체하지 않습니다.

{bt}

![자연 잔차와 시간](presentation_figures/m01_residual_vs_walltime.png)

실제 통과는 {len(bench)}개 중 {passes}개입니다. 실패한 최종 가격·수익은 균형표에서 제외하고 원시 진단값으로만 보존합니다. 모든 시도를 수행했다고 해서 수렴까지의 성공적인 성능 비교가 달성된 것은 아닙니다. 유효한 서로 다른 해가 확인되지 않았으므로 복수 균형이라고 해석하지 않습니다. 독립 재구현 설정이 저자 설정과 다르므로 원문 EG의 실패나 이론 반증이라고도 말하지 않습니다.

연속 반복 변화가 먼저 1e-6 아래로 내려간 기록은 {len(hits)}개이며 해당 순간의 자연 잔차도 별도 파일에 기록합니다. 작은 step이나 정체로 반복 변화가 작아지는 것과 원래 VI 정확도를 달성하는 것은 구분해야 합니다.

각 조합은 새 프로세스에서 순차 실행했고 BLAS/OMP/MKL 스레드를 1로 지정했습니다. 따라서 v7처럼 이전 알고리즘의 할당 이력을 같은 프로세스 메모리로 측정하는 문제를 줄였습니다. RSS는 관측된 프로세스 메모리 최댓값이며 순간 피크 보장이 아닙니다. 시간은 계측 및 일반적인 로컬 환경 활동을 포함합니다. Small 통과 게이트를 충족하지 못한 경우 Sioux 및 추가 계약 사례 확대는 NOT_RUN입니다.

## 8. M02: 전략적 시점의 구분

(1.5,1.5)와 (3,3)에서 두 운영자별 -5%/0%/+5% 가격 변경 12개를 새로 계산했습니다. 경쟁 소매가격과 MaaS 요금은 고정하고 고정 시간 반응과 교통 재균형 반응을 비교했습니다.

{st}

이는 같은 Nash 이탈 지표가 아닙니다. 후자는 다른 반응 시점의 반사실이며 유한 가격 탐색입니다. 전역 최적반응 증명도 아니고 원래 단일 수준 게임의 Nash 위반이라고 자동 판단하지 않습니다.

## 9. M03: 같은 VI를 푸는 nested 시범

JOINT_AUX는 교통 유량좌표·플랫폼 요금·소매가격을 함께 풀고, NESTED_SAME_VI는 외부 가격 잔차 평가마다 내부 교통균형을 풉니다. 두 방법 모두 (1.5,1.5) 참조해의 모든 가격을 3% 높인 같은 시작점에서 출발하고 원래 고정 시간 가격 편미분 조건을 유지합니다. 원문의 EG와 이 두 보조 해법의 비교를 가상 운영자 자체의 비교로 대체하지 않습니다.

{ntable}

외부 수치 solver가 잔차의 합성함수를 미분하는 것과, 사업자가 교통반응까지 포함한 이윤 전미분을 목적함수에 사용하는 것은 다릅니다. 이번 시범은 전자입니다. 후자는 다른 게임이 될 수 있어 별도 정당화 없이 비교할 수 없습니다. 두 최종 검증이 모두 통과해야 이 작은 warm-start 예에서의 비용 비교가 가능하며 하나라도 실패하면 성능 비교는 NOT_COMPARABLE입니다. 성공해도 대규모 일반적 속도 우위를 입증하지 않습니다.

## 10. 후속 시장 시나리오와 재개

낮은 MoD 초기 비중은 명시적 가상 사전 시장 조건으로, PT 통합운임은 요금 지불 상태를 갖춘 별도 모형으로 접근합니다. 이질성은 집단별 확률·민감도·흐름과 공유 용량·혼잡을 함께 바꾸어야 하고 효용은 공통 화폐 척도를 명시해야 합니다. 가입 가능성과 실제 구독은 다르며 공공 PT·정부 예산은 별도 목적함수와 회계가 필요합니다. 협상·PAYG/구독·혼합결제 설계도 이런 종속관계를 따라야 합니다. 상세 설계와 NOT_RUN 범위는 market_scenarios.md에 남겼습니다.

원본과 태그는 보존했고 새 로컬 브랜치 research-v7-1-critical-validation 및 results/research_v7_1에서 작업했습니다. 원격 Push·저자 연락은 하지 않았습니다. 재실행·해시·중단 지침은 README_RESEARCH_V7_1.md, 주장별 발표 가능 문구는 claim_evidence_ledger.csv에 있습니다.

{source}
'''
    en += '''\n## Boundary micro-diagnostic\n\nA separate scalar inverse-BPR test with zero flow, t0=5, capacity=300, time=5.001 and step=1e-4 gives an EG iterate change of exactly zero while the natural residual remains 0.001 for five updates. The predictor lands on free flow where H=0, and the corrector returns to the previous point. This is an example of stopping-metric disagreement, not a network equilibrium or a refutation of EG convergence theory. The inverse-BPR derivative is unbounded near free flow. Actual graph-unused congestible resources and the five largest final network residual components are recorded separately. This mechanism alone does not explain all 27 outcomes; price coupling and adaptive step shrinkage also require diagnosis. No benchmark iterate was corrected or discarded. See m01_boundary_diagnosis.md, m01_boundary_microtest.csv and m01_final_residual_components.csv.\n'''
    ko += '''\n## 추가 수치 진단: 자유류 경계에서의 EG 정체\n\n유량이 0인 독립 역 BPR 성분에서 자유류 시간 5, 용량 300, 현재 시간 5.001, step 1e-4를 적용하면 EG의 반복 변화량은 정확히 0인데 자연 잔차는 0.001로 남습니다. 예측점이 자유류 하한에 도달해 H=0이 되면 교정점이 이전 값으로 돌아오기 때문이며, 5회 반복으로 확인했습니다. 이는 종료지표 차이에 대한 반례이지 네트워크 균형이나 EG 정리의 반증이 아닙니다. 역 BPR 미분은 자유류 부근에서 유계가 아닙니다. 실제 코드에서 목적지별 그래프에 전혀 등장하지 않는 혼잡 자원과 각 실험의 최종 잔차 상위 5개 성분도 별도 파일로 제공합니다. 이 원인 하나로 모든 실패를 설명하지 않으며 가격 결합과 적응형 step 축소는 별도 요인입니다. 원래 벤치마크 반복값을 수정하거나 숨기지 않았습니다. 자세한 식과 원시 값은 m01_boundary_diagnosis.md, m01_boundary_microtest.csv, m01_final_residual_components.csv에 있습니다.\n'''
    ledger.append(dict(claim_id='N09',evidence_class='DIAGNOSTIC_ONLY',test_id='M01-boundary',result_ref='m01_boundary_microtest.csv',limits='Scalar zero-flow example; not a network equilibrium or theorem refutation.',presentation_safe_claim='A zero iterate change can coexist with a nonzero natural residual at an inverse-BPR boundary.'))
    outcsv('claim_evidence_ledger.csv',ledger)
    en=en.replace('This is a completed bounded validation study','This is a recovered, partially completed validation study')
    ko=ko.replace('이번 명세에 따른 제한된 검증 연구를 완료했으며','기존 계산 결과를 복구하고 제한된 추가 검증을 완료했으며')
    note_en='Recovery status: M03 JOINT_AUX finished and passed; NESTED_SAME_VI was interrupted without final state or a usable numerical checkpoint. It was not resumed under the latest low-compute instruction. The comparison is NOT_COMPARABLE. Historical solver timings are from the earlier run, not newly executed here. GitHub publication is authorized by the latest request; earlier no-push notes describe the previous scope.'
    note_ko='복구 상태: M03 JOINT_AUX만 완료·통과했고 NESTED_SAME_VI는 최종 상태나 사용 가능한 수치 체크포인트 없이 중단되었습니다. 최신 저연산 작업 지시에 따라 재시작하지 않았으며 성능 비교는 NOT_COMPARABLE입니다. 계산 시간은 이전 실행 기록이며 이번 복구에서 다시 계산한 값이 아닙니다. 최신 요청에서 GitHub 게시가 승인되었고 이전 no-push 문구는 과거 범위입니다.'
    en=en.replace('## Contribution and source audit',note_en+'\n\n## Contribution and source audit')
    ko=ko.replace('## 1. 이번 업데이트의 핵심',note_ko+'\n\n## 1. 이번 업데이트의 핵심')
    (O/'Technical_Report_EN.md').write_text(en,encoding='utf-8');(O/'Detailed_Review_KR.md').write_text(ko,encoding='utf-8')
    (O/'m01_solver_agreement.md').write_text(f'# M01 agreement\n\n{passes}/{len(bench)} accepted. All cases share the natural/scaled/physical contract; economic comparisons exclude failed iterates. Local initialization perturbations are not a proof of uniqueness. See full per-run traces, operator events and iterate-vs-natural crossings. No Sioux timing ranking is inferred.\n',encoding='utf-8')
    write(O/'report_summary.json',dict(m01_runs=len(bench),m01_passes=passes,level1=31,level2=14,nested_status={r['method']:r['status'] for r in nested},static_actual_A_increment=values[0],static_clone_A_increment=values[1],static_actual_B_increment=values[3],evidence_class='DIAGNOSTIC_ONLY'))
if __name__=='__main__':main()
