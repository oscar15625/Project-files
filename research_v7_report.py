"""Bilingual reports and presentation figures, generated solely from saved evidence."""
from research_v7 import *
import platform,html
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def rows(name):return list(csv.DictReader((V7/name).open(encoding='utf-8-sig')))
def number(v):return f'{float(v):,.4f}' if abs(float(v))<.1 and float(v)!=0 else f'{float(v):,.2f}'
def table(headers,data):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in data])
def main():
    figdir=V7/'figures';figdir.mkdir(exist_ok=True)
    econ=rows('wholesale_decomposition.csv');physical=rows('physical_usage.csv');bench=rows('benchmark_pilot.csv');strategy=rows('strategic_counterfactual.csv');multi=rows('multistart.csv');recheck=rows('baseline_recheck.csv')
    contrasts=rows('../research_v6/E01_contrasts.csv');placebo=read(V7/'placebo_summary.json');gain=placebo['independent_duplicate']['welfare_gain']
    agg={}
    for r in physical:
        a=agg.setdefault(r['run'],{k:0. for k in ['initial_pt','pt_vehicle_link_traversals','pt_boarding_events','any_actual_pt_trips','actual_mod_and_pt_trips','pt_passenger_distance_model_units','initial_pt_but_no_pt_ride']})
        for k in a:a[k]+=float(r[k])
    csvout('physical_summary.csv',[dict(run=k,**v) for k,v in agg.items()])
    labels=['E01/A_no_maas','E01/B_maas_no_transfer_advantage','E01/C_maas_paper_advantage','V5/sioux_node_node_total0_without','V5/sioux_node_node_total0_with']
    short=['Small A','Small B','Small C','SF V5 before','SF V5 after']
    pt_table=table(['Case','PT first access','PT ride links','Any PT trips','Both MoD+PT','PT access, no ride'],[[s]+[number(agg[k][c]) for c in ['initial_pt','pt_vehicle_link_traversals','any_actual_pt_trips','actual_mod_and_pt_trips','initial_pt_but_no_pt_ride']] for s,k in zip(short,labels)])
    dist_table=table(['Case','PT boarding events','PT passenger-distance (model units)'],[[s,number(agg[k]['pt_boarding_events']),number(agg[k]['pt_passenger_distance_model_units'])] for s,k in zip(short,labels)])
    fig,axes=plt.subplots(1,2,figsize=(10,3.6));axes[0].bar(['B - A','C - B'],[float(contrasts[0]['traveler_welfare']),float(contrasts[1]['traveler_welfare'])],color=['#245d85','#2b8a6e']);axes[0].set_title('Re-equilibrated sequential contrasts');axes[1].bar(['Independent clone','Corrected split','Correlated clone'],[gain,0,0],color=['#bb6c40','#2b8a6e','#245d85']);axes[1].set_title('Fixed-state choice-set diagnostic');axes[1].tick_params(axis='x',labelsize=8)
    for ax in axes:ax.set_ylabel('Aggregate expected utility');ax.grid(axis='y',alpha=.2)
    fig.suptitle('Different experiments: do not subtract or interpret as causal shares',fontsize=11);fig.tight_layout();fig.savefig(figdir/'choice_diagnostic.png',dpi=180);plt.close(fig)
    from matplotlib.colors import ListedColormap
    fig,axes=plt.subplots(1,2,figsize=(9,4));
    for ax,level,title in zip(axes,['level_1','level_2'],['Level 1: aggregate improvement','Level 2: all OD means nonworse']):
        mat=np.zeros((8,8));
        for r in econ:mat[round(float(r['c_mod'])*2),round(float(r['c_pt'])*2)]=-1 if r['status']!='PASS' else 1 if r[level]=='IMPROVING' else 0
        ax.imshow(mat,origin='lower',cmap=ListedColormap(['#666666','#f0e2d1','#2b8a6e']),vmin=-1,vmax=1)
        ax.set_xticks(range(8),[f'{x/2:g}' for x in range(8)]);ax.set_yticks(range(8),[f'{x/2:g}' for x in range(8)]);ax.set_xlabel('PT wholesale price');ax.set_ylabel('MoD wholesale price');ax.set_title(title,fontsize=10)
    fig.suptitle('Green: accepted improvement | gray: original failure | no interpolation',fontsize=10);fig.tight_layout();fig.savefig(figdir/'improvement_levels.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,3.8))
    for r in bench:
        trace=read(V7/'M01'/f"{r['method']}_1"/'trace.json');ax.semilogy([t['h_calls'] for t in trace],[t['natural_residual'] for t in trace],label=r['method'])
    ax.axhline(1e-6,color='black',ls='--',label='VI threshold');ax.set_xlabel('Counted H evaluations');ax.set_ylabel('Natural residual, gamma=1e-4');ax.set_title('Cold-start pilot: all methods exhausted the common 6,000-H budget');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(figdir/'algorithm_pilot.png',dpi=180);plt.close(fig)
    btable=table(['Method','Status','Residual','H calls','PUMCM calls','Wall / CPU (s)','RSS MB'],[[r['method'],r['status'],f"{float(r['natural_residual']):.3g}",r['h_evaluations'],r['pumcm_calls'],f"{float(r['wall_seconds']):.2f} / {float(r['cpu_seconds']):.2f}",number(r['peak_rss_mb'])] for r in bench])
    st=table(['Wholesale (M,P)','Operator','Price','Fixed-time gain','Re-equilibrated gain'],[[r['scenario'].replace('mod_','').replace('_pt_',', '),r['operator'],'+5%',number(r['fixed_time_gain']),number(r['reequilibrated_gain'])] for r in strategy if float(r['price_factor'])==1.05])
    mt=table(['Scenario','Start factor / source','Status','MoD profit','PT profit','MaaS profit'],[[r['scenario'],r['start_factor']+' / '+r['start_source'],r['status'],number(r['profit_mod']),number(r['profit_pt']),number(r['profit_maas'])] for r in multi])
    hurdle=table(['Illustrative profit floor','Level 1 points','Level 2 points'],[[str(f),str(next(int(r['points']) for r in rows('platform_hurdle.csv') if float(r['hypothetical_minimum_profit'])==f and r['level']=='level_1')),str(next(int(r['points']) for r in rows('platform_hurdle.csv') if float(r['hypothetical_minimum_profit'])==f and r['level']=='level_2'))] for f in [0,10,25,50,100,150]])
    direct=[r for r in recheck if r.get('direct_threshold_pass')=='False'];maxdirect=max(float(r['natural_residual_direct']) for r in recheck if r.get('natural_residual_direct'))
    econ_sample=[r for r in econ if (float(r['c_mod']),float(r['c_pt'])) in [(0,1.5),(1.5,1.5),(3,3)]]
    et=table(['(M,P)','PT retail change','PT wholesale','PT total change','Platform profit','Harmed ODs'],[[f"({r['c_mod']},{r['c_pt']})",number(r['pt_retail_change']),number(r['wholesale_pt']),number(r['delta_profit_pt']),number(r['profit_maas']),r['harmed_od_count']] for r in econ_sample])
    claims=[
      dict(id='C01',classification='ORIGINAL_PAPER',claim='Tables 2 and 3 report aggregate benefits in the authors settings',evidence='Supplied article Tables 2-3; local maas.txt',limit='Not numerically replicated here',presentation='The published outcomes motivate sensitivity checks.'),
      dict(id='C02',classification='DIAGNOSTIC_ONLY',claim=f'Independent service duplication increases fixed-state welfare by {gain:.2f}',evidence='placebo_od.csv',limit='Different product and equilibrium; no subtraction from E01',presentation='Expected-utility gains are sensitive to alternative identity and correlation.'),
      dict(id='C03',classification='REPRODUCED_MECHANISM',claim='PT access, actual riders and link traversals respond differently',evidence='physical_summary.csv; selected_edge_flows.csv',limit='Sioux V5 topology and distances are reconstructed',presentation='We should specify the physical PT quantity before interpreting market share.'),
      dict(id='C04',classification='REPRODUCED_MECHANISM',claim='31 aggregate improving and 14 all-OD nonworse original grid points',evidence='wholesale_decomposition.csv',limit='Conditional on auxiliary-coordinate acceptance and Shannon specialization',presentation='Aggregate benefit does not imply OD-level or individual Pareto improvement.'),
      dict(id='C05',classification='NOT_IDENTIFIED',claim='Individual Pareto improvement',evidence='No individual welfare model',limit='OD averages do not identify individual outcomes',presentation='Individual Pareto improvement is not identified.'),
      dict(id='C06',classification='DIAGNOSTIC_ONLY',claim='Three projection algorithms fail the 6000-H cold-start pilot',evidence='benchmark_pilot.csv; M01 traces',limit='One start and one initial step; no convergence-performance ranking',presentation='Robust scaling and step-selection tests are needed before a large-network benchmark.'),
      dict(id='C07',classification='NEW_COUNTERFACTUAL',claim='Profitable +5% price changes appear when traffic is re-equilibrated',evidence='strategic_counterfactual.csv',limit='Different response timing, fixed rival prices and MaaS fares; not original Nash violation',presentation='Decision timing is consequential for strategic interpretation.'),
      dict(id='C08',classification='DIAGNOSTIC_ONLY',claim=f'{len(direct)} stored PASS attempts fail a naive direct-time residual threshold',evidence='baseline_recheck.csv',limit='Auxiliary residual and forward BPR pass; no economic mismatch',presentation='Residual definitions and near-free-flow numerical precision must be disclosed.'),
    ];csvout('claim_ledger.csv',claims)
    references='Sources: Yao, Ma and Zhang (2026), Transportation Research Part C 188, 105703, DOI 10.1016/j.trc.2026.105703, supplied article, Sections 3-5, Tables 2-3, Appendix A; supplied PUMCM/PUME follow-up as background; unchanged V5 source-to-code ledger; 2026-11-08 research_v6 report; user v7 brief. Source PDFs are not redistributed. The v7 brief is an experiment request, not evidence of an original-paper claim.'
    en=f'''# MaaS Research v7: Critical Review and Experimental Validation

Technical experiment report | 9 November 2026 | Local independent reconstruction

## 1. Scope and findings

This study audits the behavioral and numerical interpretation of the November research_v6 reconstruction. It does not recover the authors' precise experimental calibration, prove an error in their theorem, or fit results to published values. The November study starts from the V5 model; it is distinct from the October maas-reproduction-v6-final branch. Existing results and tags remain unchanged.

Three results are central. A purely independent duplicate of the non-MaaS alternative raises fixed-state aggregate expected utility by {gain:.2f}, despite no improvement in travel conditions. The original wholesale grid contains 31 aggregate improving points but only 14 points with nondecreasing utility for every OD mean. Finally, profitable finite price changes can emerge when physical traffic is allowed to re-equilibrate, although the same changes lose money at fixed travel times. These are conditional results, not individual Pareto or empirical market predictions.

Phase 1 is complete. Phase 2 contains an executed algorithm pilot, finite strategic counterfactuals and local multistart diagnostics. The full convergence benchmark and a complete nested solver are not complete. Phase 3 extensions are deferred because the choice-set and numerical issues require priority under the user-defined stopping rule.

## 2. Baseline integrity and a residual qualification

All 75 previously accepted attempts reproduce their stored economic metrics within 1e-6; the original failed attempt remains preserved. The prior evidence hashes and protected files were checked before analysis. The new baseline seal also covers the complete research_v6 folder. No original model code or old output was overwritten.

However, {len(direct)} of the 75 accepted attempts give a directly recomputed time-coordinate natural residual above 1e-6, with maximum {maxdirect:.4g}. Their auxiliary-coordinate residuals and forward BPR travel-time checks pass. Therefore the label PASS must be qualified by its actual numerical definition. This report retains the original 31/14 classifications under that acceptance rule; it does not silently replace the rule with a direct-time criterion.

The relevant transformation is t = t0[1 + 0.15 x^4], where x is flow/capacity. Inverting rounded times near t0 loses information about small positive x. The inverse derivative grows without bound near free flow. The refiner retained x and recovered supply from capacity*x, whereas Model.evaluate reconstructs supply from time alone. The first strict v7 check failed and its log was preserved; both residuals are now exported. This is evidence of a numerical representation issue, not evidence that the reported revenue identities fail. Future projection benchmarks must use a clearly specified, independently verified stopping criterion and test conditioning rather than copying an auxiliary residual into an original-variable algorithm.

## 3. Alternative-duplication placebo

Let p be an OD's baseline non-MaaS probability and mu the upper-choice scale (mu=1 here). Adding an independent identical copy changes the inclusive value by mu*log(1+p), and the combined service probability becomes 2p/(1+p). Each copy has probability p/(1+p). Prices, physical times, routes and systematic service utility remain fixed. There is no new operator equilibrium in this diagnostic.

Splitting the original alternative into two copies with an offset -mu*log(2) on each leaves the total probability and inclusive value unchanged. A perfectly correlated pair also leaves its class value unchanged; an equal label allocation is used only for reporting. This is an analytical extreme-correlation diagnostic, not an estimated nested-choice model. Baseline state A is the reference for all three tests.

{table(['Diagnostic','Aggregate utility gain','Clone label share (%)'],[[k,number(v['welfare_gain']),number(v['clone_share_pct'])] for k,v in placebo.items()])}

![Choice diagnostics](figures/choice_diagnostic.png)

The earlier B-A=103.29 and C-B=69.58 are re-equilibrated sequential differences for an actual separately priced MaaS product. A perfect free clone is a different experiment. Subtracting 575.18 from 103.29 or calling the ratio a causal artifact share would be invalid. What is established is the sensitivity of expected utility to alternative identity. To evaluate physical platform benefits, specify perceived differentiation, correlation and access eligibility, then solve and validate that new equilibrium; the split correction is not a calibrated policy recommendation.

## 4. Actual PT use versus payment and access labels

Edge labels distinguish initial PT gates, physical PT ride links, PT boarding/transfer events and paid links. Absorbing Markov-chain hitting probabilities identify whether a trip actually uses any PT ride link and whether it traverses both a MoD road link and a PT ride link. These are not inferred from transfer counts. For an event-edge set E, the probability of avoiding E solves a=(I-P_without_E)^(-1)b; inclusion-exclusion yields the probability of using both modes. Kernel probabilities are recovered from positive gate injections and normalized edge visits. We preserve per-edge and per-OD exports.

{pt_table}

{dist_table}

In the small network, A to C increases initial PT access by {agg[labels[2]]['initial_pt']-agg[labels[0]]['initial_pt']:.2f}, but PT ride-link traversals increase by only {agg[labels[2]]['pt_vehicle_link_traversals']-agg[labels[0]]['pt_vehicle_link_traversals']:.2f}. C has about {agg[labels[2]]['initial_pt_but_no_pt_ride']:.2f} initial-PT trips with no actual PT ride, and actual mixed MoD/PT use rises to {agg[labels[2]]['actual_mod_and_pt_trips']:.2f}. B to C even reduces ride-link traversals while increasing PT-using persons. Ride counts weight trip length; rider counts do not. These distinctions prevent treating every observed increase as pure payment relabeling or as proportionate growth in physical service use.

The Sioux comparison reuses the two validated V5 node/node states, not a new Sioux A/B/C experiment. Its actual PT riders and ride-link traversals both increase substantially. Passenger-distance uses reconstructed network lengths: small-network explicit lengths and Sioux proxy lengths derived in V5, including reverse-road fallback for PT. These totals are not externally validated passenger-kilometers.

The paper's Table 2 PT shares sum to 25.5% before and 25.5% after in either MaaS column; Table 3 increases from 10.6% to 28.6%. These rounded labels alone do not identify PT ride distances or mixed-mode trajectories. The mapping to first-access shares remains unconfirmed. The physical audit therefore clarifies the independent reconstruction, not an undocumented author reporting convention.

## 5. Wholesale payments, profits and distribution

For each operator, total modeled profit equals retail receipts plus wholesale receipts; operating costs are not separately estimated in this reconstruction. Platform profit equals OD fare receipts minus both wholesale payments. OD-level sales and conditional wholesale costs are exported. Internal transfers are not added again to social welfare.

Level 1 requires both operator gains, positive platform profit and aggregate traveler gain greater than 0.001. Level 2 additionally requires every OD mean to be nonworse within 1e-8. Level 3 (individual Pareto improvement) is NOT_IDENTIFIED. The original 64-point grid retains 63 accepted candidates and one failure; 31 points satisfy Level 1 and 14 satisfy Level 2. No intervening equilibrium is inferred by interpolation.

![Discrete improvement levels](figures/improvement_levels.png)

{et}

The retail-revenue change and wholesale contribution exactly reconcile the PT profit change. A growing wholesale component can coexist with shrinking retail receipts. Minimum platform profit requirements below are exogenous post-processing diagnostics, not measured operating costs or a re-equilibrated market-exit model.

{hurdle}

## 6. Executed projection-algorithm pilot

PG, fixed EG and adaptive EG use the same original Model.evaluate/project, the same C configuration, one common cold start Model.initial(), initial step 1e-4, natural residual gamma=1e-4 and tolerance 1e-6, and exactly 6,000 solver H evaluations each. Adaptive EG halves the step until step*norm(Hhalf-H) <= 0.7*norm(half-y). All rejected trials count against the budget. One final validation H call per method is counted separately. The auxiliary fare shortcut is disabled. PUMCM call counts equal H calls times six destination/service graph solves for this small model.

{btable}

![Algorithm pilot](figures/algorithm_pilot.png)

All three runs exhausted the budget without convergence. Their prices and profits are saved only as failed-iterate diagnostics and cannot be compared as equilibria. Hence no converged-solution performance ranking, success-rate population estimate, multiple-equilibrium claim or Sioux scaling conclusion is supported. The pilot is more than a smoke test, but does not satisfy the planned full multistart time-to-convergence benchmark. One initial step is not an optimized step selection for each method. The paper itself discusses selecting suitable steps; these failures do not refute its convergence claims under its assumptions.

Runs were sequential on the same Windows CPU, with BLAS/OMP/MKL thread environment set to one. Wall and process CPU include Python instrumentation; RSS is sampled at H entry and is not a guaranteed instantaneous maximum. GPU/PyTorch performance is not compared. The CPU description, per-call trace and environment are stored. Next priority is resource-specific residual diagnostics, step-size validation and a theoretically consistent scaled or flow-coordinate formulation, followed by multistart small-network tests before Sioux expansion.

The component audit confirms that the largest PG and fixed-EG residuals are traffic components. PG repeatedly reaches free-flow bounds even with positive flow; fixed EG retains excess time on nearly unused links. Adaptive EG shrinks to 7.8125e-7 and still has substantial traffic, fare and retail-price residuals. Thus the failed runs cannot be explained solely by the tiny rounding discrepancy found in accepted auxiliary solutions. The numerical failure mechanism and step/coordinate dependence require further work.

## 7. Strategic timing, local starts and nested comparison

For three representative points, each operator's retail price changes by -5%, 0% and +5%. Rival retail price and every MaaS fare remain fixed. We compare the original fixed-time demand response with a separately solved physical traffic equilibrium at the altered prices. All 18 inner traffic solves pass auxiliary natural/scaled and capacity-complementarity checks. Zero-price-change controls reproduce the starting profits within 1e-6. These finite probes are not exhaustive best responses.

{st}

At (1.5,1.5), +5% MoD and PT price changes lose money at fixed times but gain about 25.19 and 19.78 after traffic adjusts. This is a material decision-timing sensitivity. It is not automatically a Nash violation of the original single-level game: the unilateral feasible response and derivative convention have changed. A review should explicitly distinguish partial derivatives at fixed virtual-operator action from total derivatives through traffic equilibrium.

{mt}

Two local starts perturb the accepted (1.5,1.5) state by +/-5%; the third starts the original failed (3.5,1.5) point from its accepted neighbor (3,1.5). New attempts have their own raw solver, state and validation files. They never replace the original failure or update the original 63/64 region. Similar locally accepted profits do not prove global uniqueness; different nonconverged values do not prove multiplicity.

All three new attempts pass the full inherited validation, including fixed-time deviation checks. The two local starts return the representative profits to numerical precision. The neighbor-start success at the previously failed point shows that its original failure is not evidence of equilibrium nonexistence; it also demonstrates the practical importance of initialization. This successful diagnostic is not retrospectively counted as an original-grid success.

A fair nested numerical comparison has two variants. To solve the same single-level stationary system, eliminate traffic with an inner solver but retain the original fixed-time price components H_price(t*(p),p), and compare final full residuals and total inner calls. If instead each leader optimizes profit(t*(p),p), total derivatives enter and the game can change. A CPU ratio between those two formulations would confound numerical implementation and strategic semantics. Only the inner traffic prototype is implemented here; a complete nested outer solver and a controlled efficiency comparison remain unimplemented.

## 8. Claims, deferred extensions and reproducibility

claim_ledger.csv identifies ORIGINAL_PAPER, REPRODUCED_MECHANISM, NEW_COUNTERFACTUAL, DIAGNOSTIC_ONLY and NOT_IDENTIFIED statements. No claim of universal MaaS benefit, individual Pareto improvement, algorithmic superiority, unique equilibrium or author error follows from these experiments.

Behavioral heterogeneity is the next structural extension after interpretation and numerical controls are settled: preserve population-weighted mean preferences, compute class-specific probabilities and analytic sensitivities, load every class on shared physical capacities, and compare welfare in common monetary units. A lower MoD baseline preference must be declared as a new market scenario. Boarding/zone/transfer-integrated fares require an expanded paid-state or history representation and accounting tests; changing a single link coefficient is insufficient.

Deferred design notes: availability requires eligible/ineligible classes and conservation; subsidies require a government budget and transfers counted once; subscription requires a participation and repeated-trip stage; multiple platforms require platform-specific prices and substitution; within-trip MaaS/non-MaaS mixing requires a payment-state expansion and cycle controls. None is implemented in this release.

Replay: research_v7.py; research_v7_benchmark.py; research_v7_stability.py; verify_research_v7.py; research_v7_report.py. Use the bundled Python and original .vendor path. Benchmark and stability outputs skip completed cases; a benchmark checkpoint can resume, but resumed segment time is not an uninterrupted performance measure. Preserve logs and start a new directory for a changed configuration. Local branch codex/maas-research-v7-20261109 and Git bundles provide backups; no remote push or author contact occurred. See notes/RESUME_RESEARCH_V7.md for status and next gates.

{references}
'''
    ko=f'''# MaaS Research v7 상세 검토 보고서

2026년 11월 9일 | 논문 리뷰 및 방법론 검증용 독립 재구현

## 1. 이번 작업의 결론과 완료 범위

이번 결과의 핵심은 기존 수익 추세를 더 그럴듯하게 맞추는 것이 아니라, 그 결과가 의미하는 바를 더 정확하게 제한하는 데 있습니다. 대안의 독립성, 실제 PT 이용량의 정의, 가격결정 시점, 수치 잔차의 좌표계를 구분했을 때 이전 보고서만으로는 드러나지 않았던 차이가 확인됐습니다. 원 논문 수치의 완전 복원이나 수학적 정리의 반증을 주장하지 않습니다.

첫째, 통행조건을 전혀 개선하지 않아도 동일한 non-MaaS 대안을 독립적으로 복제하면 기대효용 합계가 {gain:.2f} 증가했습니다. 둘째, 기존 도매가격 격자의 총량 공동 개선점 31개 중 모든 OD 평균이 비악화인 점은 14개입니다. 셋째, 고정 교통상태에서는 이익이 감소하는 가격 인상이 교통을 재균형시키면 이익 증가로 바뀝니다. 넷째, 동일 호출 예산의 실제 알고리즘 시범 실행은 세 방법 모두 미수렴했습니다.

Phase 1의 세 진단을 완료했습니다. Phase 2는 실제 시범 벤치마크, 대표 가격변경 실험, 국소 다중 초기값 검사까지 수행했습니다. 수렴까지의 본격적인 알고리즘 비교와 완전한 nested 외부 최적화는 완료하지 못했습니다. 사용자가 제시한 중단 규칙에 따라 이 문제를 먼저 해결해야 하므로 Phase 3의 이질성·운임 확장은 구현하지 않았습니다. 10월의 최종 재현 v6와 11월 research_v6는 별개이며, 이번 작업은 후자를 출발점으로 삼았습니다.

## 2. 기존 결과 재검증과 잔차의 의미

기존 75개 PASS 사례의 경제적 지표는 저장값과 1e-6 이내로 일치했습니다. 기존 해시 목록을 확인하고 research_v6 전체까지 새로 봉인했습니다. 기존 실패점과 V5/V6 모델·결과·태그를 수정하지 않았습니다.

다만 {len(direct)}개 사례에서 시간변수만으로 직접 다시 계산한 자연 잔차가 1e-6 기준을 넘었습니다. 최대값은 {maxdirect:.4g}입니다. 같은 사례의 보조 유량좌표 잔차와 순방향 BPR 시간 조건은 통과했습니다. 따라서 이전 PASS는 보조 좌표를 사용하는 원래 검증 방식 아래의 판정으로 읽어야 합니다. 이 보고서의 31개/14개 역시 그 판정을 유지한 값이며, 직접 시간 잔차라는 다른 기준으로 몰래 재분류하지 않았습니다.

BPR 관계는 t=t0[1+0.15x^4]이며 x는 유량/용량입니다. 작은 유량에서는 증가시간이 너무 작아 부동소수점 시간에 충분히 보존되지 않습니다. 이 시간을 역변환해 공급유량을 복구하면 오차가 커집니다. 원래 refiner는 보조 좌표 x를 저장하여 공급을 capacity*x로 복구했습니다. 반면 Model.evaluate는 시간만으로 역함수를 계산합니다. 최초의 엄격한 재검증 실패 로그와 두 종류의 잔차를 모두 남겼습니다.

이는 수익 계산이 틀렸다는 뜻은 아닙니다. 그러나 알고리즘마다 서로 다른 잔차를 사용하면서 모두 같은 정밀도로 수렴했다고 말해서는 안 됩니다. 대규모 네트워크 적용 시에는 변수 척도, 자유류 부근의 수치 조건, 서로 다른 좌표계의 종료 기준 대응이 중요한 방법론적 질문입니다. 전체 유량좌표 변환을 도입하면 VI 연산자와 투영의 수학적 대응도 다시 확인해야 합니다.

## 3. 플랫폼 편익과 대안 복제 효과

실험의 기준은 A의 가격·시간·물리 네트워크입니다. 기준 non-MaaS 확률을 p, 상위 선택 척도를 mu=1로 두면 독립적인 동일 대안 추가에 따른 Logsum 증가는 mu*log(1+p)입니다. 두 서비스 대안을 합한 확률은 2p/(1+p)가 됩니다. 실제 서비스 개선이나 새 사업자의 이윤극대화를 전혀 계산하지 않는 순수 선택구조 진단입니다.

두 복제 대안의 체계적 효용에 각각 -mu*log(2)를 넣으면 합계 확률과 Logsum이 원래 값으로 돌아갑니다. 두 대안의 비관측 효용이 완전히 동일한 극단적 상관 사례도 서비스 범주의 기대효용을 바꾸지 않습니다. 이때 이름만 다른 두 항목에 절반씩 배분한 것은 보고용 규칙이지 관측된 선택행동이 아닙니다. 상관계수를 추정한 nested logit을 구현한 것은 아닙니다.

{table(['진단','총 기대효용 증가','복제 항목 점유율 (%)'],[[k,number(v['welfare_gain']),number(v['clone_share_pct'])] for k,v in placebo.items()])}

![선택구조 진단](figures/choice_diagnostic.png)

이전 A→B의 +103.29는 독립적으로 가격이 정해지는 MaaS 상품을 포함해 가격과 혼잡을 다시 푼 결과입니다. 이번 +575.18은 동일 상품을 복제한 고정 상태 실험입니다. 103.29에서 575.18을 차감하거나 비율로 표시해 ‘가짜 편익의 비중’이라고 해석할 수 없습니다. 확인된 것은 후생값이 대안의 정체성과 독립성 가정에 민감하다는 사실입니다.

발표에서는 ‘플랫폼의 순수 실물 편익을 분리했다’보다 ‘선택집합 확장의 기대효용 효과를 진단했고, 상관성과 상품 차별화 가정을 추가 검증해야 한다’가 타당한 표현입니다. 보정은 진단 장치이며 실제 MaaS 선호를 추정한 결과가 아닙니다. 이 보정을 실제 플랫폼에 적용하려면 가격·민감도·균형까지 함께 다시 정의해야 합니다.

## 4. 실제 PT 이용은 얼마나 달라졌는가

PT 최초 접근, PT 차량 운행 링크 통과, 승차·환승 사건, PT 유료 링크, 실제 PT를 한 번이라도 탄 통행, 실제 MoD와 PT를 모두 탄 통행을 별도로 계산했습니다. 이용경로의 전이확률로 사건 간선을 한 번도 통과하지 않을 흡수확률을 풀고 포함배제법을 적용했습니다. 따라서 PT 접근 링크나 환승 링크 하나만 보고 실제 탑승을 가정하지 않습니다.

{pt_table}

{dist_table}

작은 네트워크에서 A→C의 PT 최초 접근은 {agg[labels[2]]['initial_pt']-agg[labels[0]]['initial_pt']:.2f} 증가했지만 PT 차량 링크 통과량은 {agg[labels[2]]['pt_vehicle_link_traversals']-agg[labels[0]]['pt_vehicle_link_traversals']:.2f}만 증가했습니다. B→C에서는 실제 PT 이용자 수가 늘어도 운행 링크 통과량은 줄어듭니다. 짧게 이용하는 사람이 늘면 두 지표가 다르게 움직일 수 있습니다. C에서 PT로 최초 접근한 뒤 PT 차량 링크는 전혀 이용하지 않는 통행도 약 {agg[labels[2]]['initial_pt_but_no_pt_ride']:.2f}건입니다. 실제 MoD/PT 결합 통행은 {agg[labels[2]]['actual_mod_and_pt_trips']:.2f}건으로 확인됩니다.

Sioux Falls는 기존 V5의 node/node 미도입·도입 상태를 진단했습니다. 새 A/B/C 실험을 Sioux에서 푼 것이 아닙니다. 이 상태에서는 실제 PT 이용 통행과 PT 차량 링크 통과량 모두 증가합니다. 다만 V5의 Sioux 길이는 도로 자유류시간 등에서 구성한 대리 길이이며 PT 역방향 링크는 역방향 도로 길이를 대체 참조하기도 합니다. 표의 passenger-distance는 모형 길이 단위로 표시했고 검증된 실제 passenger-km로 부르지 않았습니다.

원 논문 Table 2의 PT 분담 합계는 25.5%로 전후 동일하고 Table 3은 10.6%에서 28.6%로 증가합니다. 반올림된 분담률만으로 PT 탑승 거리, 환승 이용 또는 최초 접근 여부를 판별할 수 없습니다. 원저자의 분담률 정의와 본 코드의 최초 접근 지표가 동일하다는 확인도 없습니다. 따라서 ‘논문은 결제방식 전환만 측정했다’고 단정하지 않고, 물리량별 재보고가 필요하다는 리뷰 질문으로 제시하는 것이 적절합니다.

## 5. 도매가격, 수익 분해와 상생의 범위

운영자 수익은 소매수입과 도매수입의 합이고, MaaS 순이익은 OD 판매수입에서 두 운영자 도매지급을 뺀 값입니다. 별도 운영비를 추정하지 않은 재구성 모형입니다. 도매이전은 사회후생에 다시 더하지 않습니다. OD별 매출과 조건부 도매비용, 실제 이용량, 수단·결제 점유율을 CSV로 남겼습니다.

Level 1은 두 운영자 수익 변화, 플랫폼 이익, 총 이용자 기대효용 변화가 모두 +0.001보다 큰 경우입니다. Level 2는 이에 더해 모든 OD 평균 효용이 1e-8 허용오차 내에서 감소하지 않는 경우입니다. Level 3 개인별 Pareto 개선은 NOT_IDENTIFIED입니다. 개인별 취향과 반사실 효용을 모형화하지 않았기 때문입니다.

기존 격자는 64개 시도 중 63개를 원래 검증 기준으로 수용했고, Level 1은 31개, Level 2는 14개입니다. 17개는 총량 공동 개선이지만 일부 OD 평균이 손해를 봅니다. 색칠한 칸 사이를 검증한 균형으로 보간하지 않았습니다.

![상생 판정 수준](figures/improvement_levels.png)

{et}

PT 소매수입 감소와 도매수입 증가가 동시에 일어날 수 있습니다. 위 분해는 총수익 변화가 어디에서 나오는지 보여 주며, 소매가격 하나만으로 운영자 수익 추세를 설명하면 놓치는 부분입니다.

{hurdle}

플랫폼 최소 요구수익 25, 50, 100 등은 임의의 외생 진단 기준입니다. 실제 운영비로 추정된 값도, 원 논문이 제시한 값도 아닙니다. 이 조건을 넣어 시장 이탈과 가격을 다시 푼 것도 아닙니다. 예를 들어 요구수익 50을 적용하면 기존 공동 개선점 중 Level 1은 16개, Level 2는 12개가 남습니다. 이는 ‘양의 플랫폼 이익’만으로 사업성을 보장할 수 없다는 추가 질문을 정량화합니다.

## 6. 실제 알고리즘 비교: 실행했지만 수렴 비교는 미완성

PG, EG_FIXED, EG_ADAPT를 같은 C 설정, 동일 cold start, 초기 step 1e-4, 동일 자연 잔차 gamma=1e-4 및 1e-6 종료기준으로 실행했습니다. 각 방법의 solver H 예산은 6,000회이며 적응형 선탐색의 거절 평가도 포함합니다. 마지막 검증 호출 1회는 별도로 기록했습니다. MaaS 요금의 조건부 최적화 지름길은 껐습니다. 작은 네트워크의 H 한 번은 6개의 목적지·서비스 그래프 풀이를 포함합니다.

{btable}

![실제 알고리즘 시범 실행](figures/algorithm_pilot.png)

세 방법 모두 예산을 소진했고 수렴하지 않았습니다. 따라서 실패한 최종 반복점의 수익을 서로 다른 균형으로 해석하거나, PG가 EG보다 우수하다고 결론 내리지 않습니다. 현재 결과는 2회 반복 동작검사를 넘어선 실험이지만 사용자가 요청한 다중 초기값·수렴까지의 본격 벤치마크는 아직 달성하지 못했습니다. 하나의 초기 step만 비교했으므로 방법별로 적절한 step을 탐색한 비교도 아닙니다.

모든 방법은 동일 Windows CPU에서 순차 실행했고 BLAS/OMP/MKL 스레드를 1로 지정했습니다. 시간에는 Python 계측 비용이 포함됩니다. 메모리는 H 진입 시 RSS를 관찰한 최댓값으로 순간 피크 전체를 보장하지 않습니다. 원 논문의 PyTorch/MPS/GPU 실행과 직접 속도를 비교하지 않습니다.

잔차 성분을 추가로 확인한 결과 PG와 고정 EG의 큰 오차는 교통 자원에서 발생했습니다. PG는 양의 유량이 있어도 자유류 경계에 닿는 성분이 있고, 고정 EG는 거의 사용하지 않는 링크에 잔여 지체를 남겼습니다. 적응형 EG는 step이 7.8125e-7까지 줄었지만 교통·MaaS 요금·소매가격 오차가 함께 남았습니다. 따라서 이 실패 전체를 앞서 발견한 아주 작은 반올림 차이만으로 설명하지 않습니다.

다음 단계는 단순히 반복 수를 크게 늘리는 것보다 어느 자원이 잔차를 지배하는지 확인하고, 자유류 부근의 역 BPR 수치 조건과 변수 척도를 다룬 뒤, 동일한 정당화된 종료기준으로 step 민감도와 초기값 검사를 수행하는 것입니다. 작은 네트워크에서 이 게이트를 통과하기 전에는 Sioux 성능 실험을 확장하지 않았습니다.

## 7. 가격변경 후 교통 재균형과 게임의 해석

대표 공동 개선점 (1.5,1.5), 비개선점 (0,1.5), 분배상 손해가 있는 공동 개선점 (3,3)에서 두 운영자 가격을 각각 -5%, 0%, +5% 변경했습니다. 경쟁 운영자의 가격과 MaaS OD 요금은 고정했습니다. 고정 시간의 수요 반응과 물리적 교통을 다시 푼 반응을 나누어 비교했습니다. 총 18회 교통 풀이가 보조 자연·척도 조정 잔차와 용량 상보성 검증을 통과했고, 0% 변경 대조군의 수익 차이는 1e-6 이내입니다.

{st}

(1.5,1.5)에서 5% 가격 인상은 고정 시간 기준으로 두 운영자 모두 손해지만, 교통 재균형 후에는 MoD 약 25.19, PT 약 19.78의 이익 증가가 나타납니다. 이는 의사결정 시점이 경제적 해석에 중요하다는 결과입니다. 원래 단일 수준 게임의 Nash 위반이나 논문의 오류라고 자동 해석하지 않습니다. 가상 교통운영자의 행동을 고정한 편미분과 가격변경 뒤 교통반응까지 포함한 전미분은 다른 조건입니다. 또한 5% 이탈은 완전한 최적반응 탐색이 아닙니다.

{mt}

수용된 (1.5,1.5) 해 주변 +/-5% 초기값과, 기존 실패점 (3.5,1.5)에 이웃점 (3,1.5)의 해를 주는 별도 진단을 수행했습니다. 원시 상태·검증 파일을 새 위치에 저장했으며 기존 실패 판정과 63/64 격자를 대체하지 않았습니다. 국소 초기값에서 비슷한 해를 얻었다고 전역 유일성을 주장할 수 없습니다.

새 시도 세 개는 고정 시간 가격 이탈 검사를 포함한 기존 검증 기준을 모두 통과했습니다. 대표점의 두 국소 초기값은 수익이 수치 정밀도 내에서 같은 해로 돌아왔습니다. 기존 실패점도 이웃 해로 시작하면 검증된 후보를 얻으므로, 이전 실패를 균형 부재로 해석할 수 없습니다. 이는 초기값과 계산 경로의 실질적인 중요성을 보여 주되 기존 63/64 판정을 소급 변경하지 않습니다.

가상 운영자의 계산적 기여를 공정하게 비교하려면 먼저 비교 대상 게임을 고정해야 합니다. 같은 VI의 교통변수를 내부 풀이로 제거하고 원래 가격 편미분 H를 유지하는 block/nested 계산은 같은 정상조건을 푸는 비교가 될 수 있습니다. 반면 교통반응을 포함한 이윤 자체를 외부에서 최적화하면 다른 전략적 문제일 수 있습니다. Root solver와 EG의 속도 차이만으로 가상 운영자의 효과를 검증할 수 없습니다. 이번에는 내부 교통 풀이를 구현했으며 외부 nested 가격 solver와 동일 조건 시간 비교는 미구현입니다.

## 8. 발표에서 사용할 주장과 후속 설계

Research Claim Ledger는 원 논문 주장, 재구현된 작동 원리, 새로운 반사실, 진단 전용 결과, 식별 불가를 구분합니다. 발표의 중심 질문은 ‘MaaS가 언제나 좋은가’가 아니라 ‘선택구조·보고 지표·의사결정 시점·수치 조건 중 어떤 가정에서 편익과 계산상의 장점이 유지되는가’가 적절합니다.

수요 전문가의 후속 기여로는 평균 선호가 같은 집단 이질성을 권합니다. 다만 집단별 계수만 바꾸는 수준을 넘어서 집단별 확률·민감도·흐름을 계산하고 모든 집단이 같은 물리적 용량과 혼잡을 공유해야 합니다. 효용척도가 다르면 공통 화폐단위로 환산하지 않고 합산해서는 안 됩니다. 이번에는 구현하지 않았습니다.

낮은 MoD 선호의 초기 시장은 명시적인 새 시나리오로 정의해야 합니다. PT 승차·구간·환승통합 운임은 이미 요금을 지불했는지와 이용 이력을 표현하는 상태공간이 필요할 수 있습니다. 원문 수치를 맞추려고 링크별 요금 계수를 조정하는 방식으로 대체해서는 안 됩니다.

가입·인지 가능성은 이용 가능 집단과 비가능 집단 및 수요 보존을, 공공보조는 정부 예산과 이전지출 중복 방지를, 구독은 가입과 반복 이용의 단계를 필요로 합니다. 복수 플랫폼은 플랫폼별 가격·대체관계를, 한 통행 내 결제방식 혼합은 결제 상태와 순환 방지를 요구합니다. 이 항목들은 설계 메모로 남기며 이번 릴리스에서 구현하지 않았습니다.

## 9. 재현·백업·남은 작업

실행 순서는 research_v7.py → research_v7_benchmark.py → research_v7_stability.py → verify_research_v7.py → research_v7_report.py입니다. 원시 결과·로그·설정·잔차·해시·그림을 results/research_v7에 저장했습니다. 기존 결과는 변경하지 않았고 codex/maas-research-v7-20261109 로컬 브랜치 및 Git bundle로 백업했습니다. 원격 Push나 저자 연락은 하지 않았습니다.

중단 후에는 notes/RESUME_RESEARCH_V7.md와 완료 파일을 확인합니다. 같은 실험의 완료 결과는 건너뛰며, 설정이 바뀌면 새 폴더를 사용해야 합니다. 체크포인트 재개 시 누적 호출 수와 새 실행 구간 시간을 구분해야 하므로 재개 구간 시간을 무중단 성능 지표로 제시하지 않습니다.

남은 우선순위는 (1) 알고리즘 수렴과 종료기준의 정합성, (2) 가격반응 시점의 게임적 정의, (3) 상관된 대안 구조의 재균형, (4) 평균 동일 이질성의 공동 혼잡 모형입니다. 첫 두 문제를 해결하지 않은 채 모든 구조 확장을 얹으면 새로운 결과의 원인을 분리하기 어렵습니다.

{references}
'''
    en=en.replace('RSS is sampled at H entry and is not a guaranteed instantaneous maximum.','RSS is sampled at H entry and is not a guaranteed instantaneous maximum. All three methods ran in one process, so allocator history affects RSS; these values are not isolated per-method memory comparisons.')
    ko=ko.replace('순간 피크 전체를 보장하지 않습니다.','순간 피크 전체를 보장하지 않습니다. 세 방법이 하나의 프로세스에서 실행되어 이전 메모리 할당 이력도 포함되므로 방법별 독립 메모리 비교로 해석하지 않습니다.')
    en=en.replace('BUDGET_EXHAUSTED','Budget reached');ko=ko.replace('BUDGET_EXHAUSTED','Budget reached')
    (ROOT/'RESEARCH_V7_EN.md').write_text(en,encoding='utf-8');(ROOT/'RESEARCH_V7_KO.md').write_text(ko,encoding='utf-8')
    # Render the same report text, tables and figures with embedded Korean font.
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'));pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='TextV7',fontName='Malgun',fontSize=9,leading=14,spaceAfter=7,wordWrap='CJK'));styles.add(ParagraphStyle(name='TitleV7',fontName='MalgunBold',fontSize=19,leading=25,spaceAfter=15));styles.add(ParagraphStyle(name='HeadV7',keepWithNext=True,fontName='MalgunBold',fontSize=12,leading=18,spaceBefore=12,spaceAfter=8));styles.add(ParagraphStyle(name='CellV7',fontName='Malgun',fontSize=7,leading=10,wordWrap='CJK'))
    out=ROOT/'output/pdf';out.mkdir(parents=True,exist_ok=True)
    def footer(c,d):
        c.setFont('Malgun',8);c.setFillColor(colors.HexColor('#566675'));c.drawString(42,25,'MaaS Research v7 | 2026-11-09 | Independent reconstruction');c.drawRightString(553,25,str(d.page))
    for language,body in [('EN',en),('KO',ko)]:
        story=[];lines=body.splitlines();i=0
        while i<len(lines):
            line=lines[i].strip();i+=1
            if not line:continue
            if line.startswith('|'):
                block=[line]
                while i<len(lines) and lines[i].strip().startswith('|'):block.append(lines[i].strip());i+=1
                data=[[Paragraph(html.escape(c.strip()),styles['CellV7']) for c in row.strip('|').split('|')] for row in block if not set(row.replace('|','').replace(' ',''))<=set('-:')]
                n=len(data[0]);t=Table(data,colWidths=[511/n]*n,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3edf4')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#bdcbd4')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.extend([KeepTogether([t]),Spacer(1,10)]);continue
            if line.startswith('!['):
                name=line.split('](')[1].rstrip(')');story.extend([Image(str(V7/name),width=511,height=220),Spacer(1,10)]);continue
            style='TitleV7' if line.startswith('# ') else 'HeadV7' if line.startswith('## ') else 'TextV7';text=line.lstrip('# ').strip()
            story.append(Paragraph(html.escape(text),styles[style]))
        SimpleDocTemplate(str(out/f'MaaS_Research_v7_{language}.pdf'),pagesize=(595,842),leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=42,title=f'MaaS Research v7 {language}',author='Independent reproduction study').build(story,onFirstPage=footer,onLaterPages=footer)
    write(V7/'report_summary.json',dict(date='2026-11-09',placebo_gain=gain,level1=31,level2=14,direct_residual_mismatches=len(direct),algorithm_converged=0,traffic_probes=18,full_benchmark='INCOMPLETE',nested_outer='NOT_IMPLEMENTED',phase3='DEFERRED'))
if __name__=='__main__':main()

