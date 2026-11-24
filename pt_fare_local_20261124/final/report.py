"""Postprocess saved, audited full-network equilibria. No optimization."""
from extension import *
import csv,platform
import scipy,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
os.chdir(ROOT)
allrows=[]
for p in sorted((ROOT/'results').glob('*/metrics.json')):
 r=json.loads(p.read_text());r['case']=p.parent.name;allrows.append(r)
assert len(allrows)==12 and all(r['status']=='STRICT_PASS' for r in allrows)
primary={r['case']:r for r in allrows if r['start']=='primary'}
def csvwrite(path,rows):
 with (ROOT/path).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def text(path,s):
 p=ROOT/path;p.parent.mkdir(exist_ok=True,parents=True);p.write_text(s,encoding='utf-8')
keys=['case','tariff','maas','start','status','share_maas','share_non','share_drive','price_mod','price_pt','profit_mod','profit_pt','profit_maas','traveler_welfare','social_welfare','retail_pt','wholesale_pt','PT_paid_units','natural_direct','natural_aux','full_scaled','fare_score_max','capacity_violation','complementarity','markov_node_balance_error','PT_revenue_error','accounting_error','price_deviation_gain','finite_difference_error','solver_H_calls','solver_seconds','total_seconds']
csvwrite('summary.csv',[{k:r[k] for k in keys} for r in allrows])
paired=[];odrows=[];service=[];multistart=[]
for tariff in ['link','flat']:
 a=primary[tariff+'_A_primary'];c=primary[tariff+'_C_primary'];pair=dict(tariff=tariff,baseline='same tariff without MaaS',maas_share=c['share_maas'])
 for k in ['profit_pt','profit_mod','profit_maas','retail_pt','wholesale_pt','traveler_welfare','social_welfare']:pair['delta_'+k]=c[k]-a[k]
 assert abs(pair['delta_profit_pt']-pair['delta_retail_pt']-pair['delta_wholesale_pt'])<1e-6
 ado={(int(o[0]),int(o[1])):o for o in a['od']}
 for o in c['od']:
  b=ado[int(o[0]),int(o[1])];odrows.append(dict(tariff=tariff,origin=int(o[0]),destination=int(o[1]),demand=o[2],maas_share=o[6],utility_A=b[7],utility_C=o[7],utility_change=o[7]-b[7],harmed=o[7]-b[7]<-1e-8))
 pair['harmed_OD_count']=sum(r['harmed'] for r in odrows if r['tariff']==tariff);pair['harmed_demand']=sum(r['demand'] for r in odrows if r['tariff']==tariff and r['harmed']);paired.append(pair)
 for sc in ['A','C']:
  r=primary[f'{tariff}_{sc}_primary'];m=make('sioux',tariff,sc=='C');y=np.load(ROOT/'results'/r['case']/'state.npy');m.optimize_fares=False
  pt_links=0.;mod_links=0.
  for ids,gr in m.graphs:
   kinds=list(gr);sol={k:g.solve(y[:m.nt],y[-2:],m.wholesale,k) for k,g in gr.items()};vals=np.array([sol[k][0]-(m.fixed if k=='drive' else y[m.nt:-2][ids] if k=='maas' else 0) for k in kinds]).T
   from scipy.special import logsumexp
   probs=np.exp(vals-logsumexp(vals,axis=1)[:,None])
   for j,k in enumerate(kinds):
    g=gr[k];flow=sol[k][-1](m.ods[ids,2]*probs[:,j]);ptmask=np.array([isinstance(s[0],int) and isinstance(t[0],int) and s[0]==t[0] and s[1]!=t[1] for s,t in g.edge_labels]);pt_links+=float(flow[ptmask].sum())
    if k!='drive':mod_links+=float(flow[(g.res>=0)&(g.res<len(m.rows))].sum())
  service.append(dict(case=r['case'],PT_vehicle_link_traversals=pt_links,MOD_vehicle_link_traversals=mod_links,PT_nonmaas_paid_units=r['PT_paid_units'],PT_unit_price=r['price_pt'],PT_retail_revenue=r['retail_pt'],PT_wholesale_revenue=r['wholesale_pt']))
  for start in ['0.8','1.2']:
   s=next(v for v in allrows if v['case']==f'{tariff}_{sc}_{start}');base=np.load(ROOT/'results'/r['case']/'state.npy');other=np.load(ROOT/'results'/s['case']/'state.npy')
   multistart.append(dict(case=s['case'],status=s['status'],price_max_difference=float(np.max(abs(base[m.nt:]-other[m.nt:]))),time_max_difference=float(np.max(abs(base[:m.nt]-other[:m.nt]))),profit_max_difference=max(abs(r[k]-s[k]) for k in ['profit_mod','profit_pt','profit_maas']),welfare_difference=s['traveler_welfare']-r['traveler_welfare']))
csvwrite('paired_comparison.csv',paired);csvwrite('od_welfare.csv',odrows);csvwrite('physical_service.csv',service);csvwrite('multistart_comparison.csv',multistart)
(ROOT/'figures').mkdir(exist_ok=True)
def save(fig,name,caption):
 fig.text(.02,.015,caption,fontsize=8);fig.tight_layout(rect=(0,.09,1,1))
 for ext in ['png','svg']:fig.savefig(ROOT/'figures'/f'{name}.{ext}',dpi=180)
 plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10,4));axs[0].bar(['LINK','FLAT'],[p['maas_share'] for p in paired]);axs[0].set(ylabel='MaaS share (%)',title='Full Sioux Falls: with MaaS')
axs[1].bar(['LINK','FLAT'],[p['delta_profit_pt'] for p in paired],color=['steelblue','orange']);axs[1].axhline(0,color='black',lw=.7);axs[1].set(ylabel='PT profit change (model units)',title='C minus matched no-MaaS baseline')
save(fig,'market_and_PT','528 OD; demand 432,720. Aggregate MoD access / node-specific PT access. Independent VI, not a Table 3 replication.')
fig,ax=plt.subplots(figsize=(8,4));xx=np.arange(2);ret=[p['delta_retail_pt'] for p in paired];wh=[p['delta_wholesale_pt'] for p in paired];net=[p['delta_profit_pt'] for p in paired]
ax.bar(xx-.22,ret,.22,label='Retail change');ax.bar(xx,wh,.22,label='Wholesale change');ax.bar(xx+.22,net,.22,label='Net PT change');ax.set_xticks(xx,['LINK','FLAT']);ax.set(ylabel='Revenue / profit change (model units)',title='Wholesale receipts do not offset lost retail revenue');ax.legend();ax.axhline(0,color='black',lw=.6)
save(fig,'PT_revenue_decomposition','Profit accounting follows the source model; no additional operating costs or subsidy are introduced.')
fig,axs=plt.subplots(1,2,figsize=(11,4));axs[0].bar(['LINK','FLAT'],[p['delta_traveler_welfare']/1000 for p in paired]);axs[0].set(title='Utility gain vs matched A',ylabel='Thousand model units')
for i,t in enumerate(['link','flat']):axs[1].bar([i-.15,i+.15],[primary[t+'_A_primary']['traveler_welfare']/1e6,primary[t+'_C_primary']['traveler_welfare']/1e6],width=.3,label=t.upper())
axs[1].set_xticks([-.15,.15,.85,1.15],['LINK A','LINK C','FLAT A','FLAT C']);axs[1].set(title='Absolute utility levels',ylabel='Million model units')
save(fig,'welfare_baseline_and_levels','Different tariffs have different A baselines. Logsum is not an estimated causal or net subscription benefit.')
fig,axs=plt.subplots(1,2,figsize=(10,4));
for t in ['link','flat']:
 rr=[r['utility_change'] for r in odrows if r['tariff']==t];axs[0].plot(np.sort(rr),label=t.upper());axs[0].set(xlabel='OD rank (sorted separately)',ylabel='Mean utility change per traveler');axs[0].legend()
axs[0].axhline(0,color='black',lw=.6);axs[1].bar(['LINK','FLAT'],[p['harmed_OD_count'] for p in paired]);axs[1].set(ylabel='Harmed OD means (count)',title='Distributional diagnostic; not individual Pareto')
save(fig,'OD_distribution','All 528 OD included, including OD with endpoints outside PT stations. Threshold for harm: utility change < -1e-8.')
table='| 운임/조건 | MaaS % | PT 단가 | PT 이익 | MoD 이익 | MaaS 이익 | 이용자 기대효용 |\n|---|---:|---:|---:|---:|---:|---:|\n'
for t in ['link','flat']:
 for sc in ['A','C']:
  r=primary[f'{t}_{sc}_primary'];table+=f"| {t.upper()} {sc} | {r['share_maas']:.4f} | {r['price_pt']:.5f} | {r['profit_pt']:,.2f} | {r['profit_mod']:,.2f} | {r['profit_maas']:,.2f} | {r['traveler_welfare']:,.2f} |\n"
p0,p1=paired
pttable='| 운임 | PT 소매수입 변화 | PT 도매수입 변화 | PT 순이익 변화 | 이용자 효용 변화 | 손실 OD 수 |\n|---|---:|---:|---:|---:|---:|\n'
for p in paired:pttable+=f"| {p['tariff']} | {p['delta_retail_pt']:,.2f} | {p['delta_wholesale_pt']:,.2f} | {p['delta_profit_pt']:,.2f} | {p['delta_traveler_welfare']:,.2f} | {p['harmed_OD_count']} |\n"
valid=dict(status='PASS_FULL_NETWORK_COUNTERFACTUAL_CONDITIONAL',small_saved_replay=6,full_network_primary=4,multistart=8,strict_pass=12,failed=0,max_original_time_residual=max(r['natural_direct'] for r in allrows),max_scaled_residual=max(r['full_scaled'] for r in allrows),max_Markov_balance=max(r['markov_node_balance_error'] for r in allrows),max_PT_revenue_error=max(r['PT_revenue_error'] for r in allrows),max_price_deviation_gain=max(r['price_deviation_gain'] for r in allrows),max_FD_error=max(r['finite_difference_error'] for r in allrows),max_multistart_price_difference=max(r['price_max_difference'] for r in multistart),solver_H_calls=sum(r['solver_H_calls'] for r in allrows),solver_seconds_sum=sum(r['solver_seconds'] for r in allrows),zone='NOT_RUN_NO_ZONE_MAP')
write(ROOT/'VALIDATION_SUMMARY.json',valid)
text('REPORT_KR.md',f'''# PT 운임 구조의 Sioux Falls 전체 네트워크 확장 실험

실행일 2026-11-24. **528 OD·432,720 수요의 전체 네트워크에서 4개 주조건과 8개 추가 초기점, 총12회 STRICT_PASS.** 첨부 Small 저장해6개도 별도 replay했다. 기존 presentation_freeze_20261115는 변경하지 않았다.

## 1. 결론

링크당 운임에서 여정당 첫 PT 이용 1회 운임으로 바꾸면 MaaS 점유율은 {p0['maas_share']:.4f}%→{p1['maas_share']:.4f}%로 {p1['maas_share']-p0['maas_share']:.4f} percentage points 증가했다. 그러나 동일 운임 내 MaaS 도입에 따른 PT 이익 변화는 {p0['delta_profit_pt']:,.2f}→{p1['delta_profit_pt']:,.2f}이다. **이 공급·행동 설정에서는 두 운임 모두 PT 손실이며, 여정 운임에서 손실이 더 크다.** Small의 ‘링크에서는 PT 이익, 여정에서는 손실’이라는 부호 전환은 전체 네트워크에서 그대로 반복되지 않았다.

따라서 운임함수가 중요하다는 구조적 민감도는 확인되지만, 링크 운임이 항상 MaaS 이용률을 과대추정한다거나 flat이 항상 더 높은 후생을 만든다는 결론은 지지하지 않는다. 원 논문 Table3의 PT 공동개선은 이 독립 기준선에서 재현되지 않았다. 이를 저자 결과의 오류 증명으로 취급하지 않는다.

## 2. 입력 감사와 원 논문 대조

첨부 ZIP은 PROVENANCE.json에 SHA256로 고정했다. 보고서·코드·6개 .npy/JSON·표·audit.log를 검토했다. Small6개 저장 경제량 차이는1e-6 미만이며 원시간 잔차도1e-6 미만이다. 원 첨부의 natural_projected는 보조좌표 잔차이므로 이를 원시간 검증으로 오인하지 않았다. 기존 Small multistart는 로그로 보존했으며 이번에 새로 실행한 multistart는 Sioux Falls8개이다.

원천 Git 커밋 b682637921d843bc2edac8f154b5d03f21fa257a의 src/model.py, SiouxFalls_net.tntp, SiouxFalls_trips.tntp를 그대로 고정했다. 원 논문 Eq.(27)의 non-MaaS PT 링크당 단가와 MoD 거리당 단가는 edge coefficient로 점검했다. PT3노선,14정류장 노드,13무방향 PT구간,76방향 도로링크를 확인했다. PT정류장 양끝174OD/164,040수요의 최단PT홉1~8, 가중평균2.611558은 첨부와 일치한다. 이 수치는 실제 균형 경로 분포가 아니다.

모형은 Shannon PUMCM 특수화, MNL 상위선택, 원천의 Sioux 비용·용량·운임 설정이다. MoD 접근은 전체 집계형(60,000), PT 접근은 정류장 노드별30,000; PT ride capacity1,000,000, PT 자유시간1.2배, non-MaaS 환승8, MaaS환승0.5, 도매 MoD1.5/PT1.0이다. PT 접근용량의 노드별 해석은 **독립 구현 가정**으로 고정했다. Small의 node/node 설정과 동일한 용량 체계라는 뜻이 아니다. 전체 수요를 축소하거나 원문에 맞춰 상수/계수를 보정하지 않았다.

## 3. 통제된 운임 변경

LINK는 PT ride edge마다 소매단가를 부과한다. FLAT은 non-MaaS 그래프에 has_used_PT=0/1을 추가하여 최초 PT 진입에만 부과하고 이후 재진입/환승에는 부과하지 않는다. MoD→PT 전환과 출발지에서의 PT 진입을 모두 테스트했다. MaaS/Driving 대안, 물리 링크·용량·총수요·도매계약은 각 LINK/FLAT 비교에서 동일하다. PT소매가격0에서 Small과Sioux의 효용·물리유량 일치로 상태증설에 따른 대안 복제 효과를 점검했다.

실제 Sioux 존맵/요금표가 주어지지 않았으므로 존 실험은 NOT_RUN_NO_ZONE_MAP이다. Small의 가상4존 결과는 입력 감사 대상으로만 유지했다. 실제 스위스 요금·가입선택을 추정한 실험이 아니다.

## 4. 새 균형 결과

{table}

A는 MaaS 미도입, C는 MaaS 도입 및 원천 환승 우위 조건이다. 모든 값은 독립 모형 단위이며 PT 단가는 LINK에서는 링크당, FLAT에서는 여정당이므로 직접적인 가격상승률로 비교하지 않는다.

{pttable}

PT 이익은 소매수입과 도매수입의 합이다. 이번에는 도매수입 증가가 소매수입 감소를 상쇄하지 못했다. paid units, PT ride-link 통행량 및 판매채널 지표는 physical_service.csv에서 구분했다. 실물 링크 횟수는 실제 승객 수와 같지 않다.

FLAT−LINK의 C 절대효용 차이는 {primary['flat_C_primary']['traveler_welfare']-primary['link_C_primary']['traveler_welfare']:,.2f}이다. 각 운임 내 C−A와 운임 간 C 수준 차이를 구분해야 한다. LINK와 FLAT의 무MaaS 기준선부터 서로 다르다. OD 평균 손실은 od_welfare.csv에 모두 보존했다. 개별 사람별 Pareto 개선은 NOT_IDENTIFIED이다.

## 5. 계산·검증 방법

원천 Model.evaluate는 수정하지 않았다. 혼잡 링크를 유량/용량비 좌표로 표현하고, λ=1 MaaS OD가격을 조건부 정확 최적요금식으로 제거한 reduced root를 풀었다. 교통시간·소매가격·MaaS가격이 최종적으로 함께 재균형된다. 남은 운영자 가격 조건은 **교통상태 및 다른 가격을 고정한 원래 편미분**이며, 교통반응을 내재화한 Stackelberg 목적함수로 바꾸지 않았다. 수치 residual Jacobian에 체인룰이 들어가는 것과 경제적 게임 해석을 구별한다.

HYBR 우선, 필요 시 bounded TRF fallback; 시도별 H≤4,000/600초, 추가초기점은 H≤2,500/600초이다. 실제 사용량은 summary.csv와 trace.json에 있다. 기본 LINK는 cold start, FLAT은 대응하는 LINK 해에서 시작했다. 추가초기점은 각 해의 소매가격×0.8/1.2 및 혼잡 지연×0.99/1.01이다. 제거된 MaaS가격은 각 평가에서 정확식으로 재계산하므로 별도의 초기 MaaS가격 perturbation 효과를 주장하지 않는다.

원시간 natural residual, 보조좌표 residual, scaled residual 및 전체 OD fare score를 확인했다. 물리용량·상보성, Markov 각 내부노드 수지, 회계, PT paid units×가격의 매출 일치, 모든 OD 확률합을 검사했다. 소매가격별 grid 및 bounded 이탈탐색과 MaaS 정확 조건부 최적이탈, 소매가격5점 유한차분도 검증했다. 탐색영역 내 이탈검사는 전역 Nash 증명이 아니다.

검증 요약: 원시간 잔차 최대 {valid['max_original_time_residual']:.3e}, scaled 최대 {valid['max_scaled_residual']:.3e}, Markov 수지 최대 {valid['max_Markov_balance']:.3e}, PT 회계 최대 {valid['max_PT_revenue_error']:.3e}, 가격이탈이익 최대 {valid['max_price_deviation_gain']:.3e}, 가격유한차분 오차 최대 {valid['max_FD_error']:.3e}. 추가초기점 가격 최대 차이 {valid['max_multistart_price_difference']:.3e}. 총 solver H {valid['solver_H_calls']}; 이 수에는 수치Jacobian 호출을 포함하며 별도 검증 호출은 포함하지 않는다. 다중초기점의 일치는 전역수렴/유일성 보장이 아니다.

## 6. 원 논문과 다른 점 및 허용 표현

원 논문 Table3은 MaaS39.5%, PT이익337,286→375,636을 보고한다. 본 LINK 기준선은 위 표와 다르다. 독립 Shannon 특수화, 상태/접근용량 해석, 비MaaS의 멀티모달 접근 및 균형 선택 등이 동시에 원인 후보이므로 이 실험만으로 차이의 원인을 하나로 식별할 수 없다. 과거 v5의 한계가 사라졌다고 주장하지 않는다. 원문 텍스트는 로컬에서 대조했으며 PDF/원문 전체는 공개 패키지에서 제외했다.

권장 발표 문장: ‘동일한 독립 Sioux Falls 모형과 전체 OD 수요에서 PT 소매운임만 바꿔 재균형했을 때, MaaS 이용률·PT 수입 구성·분배 결과가 변했다. 다만 원 논문의 공동개선 기준선 자체와 차이가 있어, 이것은 저자 Table3의 정확 재현이 아니라 명시한 가정 아래의 운임 반사실 실험이다.’

## 7. 전달 및 재개

verify.py는 배포 manifest와 저장해를 검증하며 새 최적화를 실행하지 않는다. campaign.py는 COMPLETE가 있는 시도를 건너뛰며 완료된 실패도 임의로 다시 PASS로 바꾸지 않는다. 현재12개 시도는 모두 완료되어 이어서 실행할 미완료 계산은 없다. 새 실험은 별도 브랜치·출력경로로 분리한다. 중간 checkpoint02와 최종 ZIP, 원시 상태·coordinates·trace·protocol·실패/종료 메시지를 보존했다.
''')
text('REPORT_EN.md',f'''# Full-demand Sioux Falls PT tariff counterfactual

Four primary equilibria and eight perturbed-start solves passed strict validation. This is an independent Shannon/MNL VI counterfactual, not a numerical replication of the paper's Table 3.

{table}

The pinned source is b682637921d843bc2edac8f154b5d03f21fa257a. All528 OD and432,720 trips are retained. MoD access is aggregate; PT access capacity is node-specific. Only non-MaaS PT retail charging changes between link-based and first-PT-entry-per-journey charging. Wholesale, demand, supply and all other choice assumptions remain fixed between tariffs. No Sioux zone map was supplied; no zonal full-network experiment was invented.

MaaS share rises from {p0['maas_share']:.4f}% to {p1['maas_share']:.4f}%. The matched PT profit changes are {p0['delta_profit_pt']:.2f} and {p1['delta_profit_pt']:.2f}, respectively. Both are losses in this full-network configuration, unlike the positive LINK effect in the supplied Small study. Lost retail receipts exceed incremental wholesale receipts. See paired_comparison.csv, physical_service.csv and od_welfare.csv.

The solver uses flow coordinates and exact conditional MNL fare elimination, retaining the original fixed-traffic retail-price VI conditions. HYBR with bounded TRF fallback is a root method, not an extragradient improvement. All OD fares, traffic times and retail prices are jointly consistent at the final state. Two retail-price factors(.8/1.2) plus small traffic perturbations per condition are sensitivity checks, not global uniqueness proofs. See VALIDATION_SUMMARY.json for residual, Markov balance, accounting, deviation and finite-difference checks. Solver H counts include numerical Jacobian calls but exclude post-solve validation calls.

Windows Python {platform.python_version()}, NumPy {np.__version__}, SciPy {scipy.__version__}. Linux execution has not been performed locally. python verify.py replays archived states without optimization. Original source PDF and private paths are not distributed. The frozen20261115 release is untouched.
''')
text('README.md','''# PT tariff full-network local extension — 2026-11-24

Read REPORT_KR.md, REPORT_EN.md, summary.csv, paired_comparison.csv and VALIDATION_SUMMARY.json. Four primary cases + eight multistarts are complete. The original Small package is a separate input; six saved Small states were replayed.

Extract the ZIP to a short path, e.g. C:/maas/pt24 or ~/pt24. Use Python3.12 and requirements.txt. Run `python verify.py` for read-only saved-state/manifest verification. Redirect output outside the release folder. Linux-compatible code is supplied; this run was tested on Windows only.

`python campaign.py` is the bounded resume entry point, skips COMPLETE cases, and does no new solve when all12 are complete. Do not remove COMPLETE to force a restart. Use a fresh output branch/directory for new research. `python extension.py` and `python structure_audit.py` are audit builders; they write audit outputs, unlike verify.py.

src/model.py and data files are pinned to Git commit b682637921d843bc2edac8f154b5d03f21fa257a. Protocol: aggregate MoD access, node-specific PT access, full528OD, no demand scaling. Small's node/node settings are distinct. No full-network zones are simulated without an explicit zone map. All amounts are model units. The original paper's Table3 is not numerically reproduced here.

results/*/ contains state.npy, coordinates.npy, metrics.json, trace.json, protocol.json, COMPLETE.json and best checkpoints. COMPLETE means the attempt ended; consult its status rather than assuming PASS. The supplied Small logs are retained separately under input/. requirements.txt describes the tested environment, not empirical calibration.
''')
text('requirements.txt',f'numpy=={np.__version__}\nscipy=={scipy.__version__}\nmatplotlib=={matplotlib.__version__}\n')
text('ENVIRONMENT.txt',f'Windows; Python {platform.python_version()}; NumPy {np.__version__}; SciPy {scipy.__version__}; matplotlib {matplotlib.__version__}\nOPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1\n')
text('FAILURES_AND_LIMITS.md','''# Preserved outcomes and limitations

All12 full-network attempts passed. Raw solver termination messages and iteration traces are retained; success is decided by independent final validation, not optimizer status. No full-network zonal run was attempted because no zone map was supplied. This is an unimplemented scope, not a numerical failure.

The original supplied run.py treats missing LINK residuals as acceptable; this extension does not rely on that rule. Its six-state replay recomputes original-time residuals. The package's natural_projected was auxiliary-coordinate based. New full-network validation records both definitions.

The supplied model supports Small only. This extension imports the pinned full-network source and retains its unchanged Model.evaluate. Aggregate MoD versus node PT access is declared explicitly. It differs from the supplied Small node/node configuration and does not uniquely identify the cause of disagreement with Table3. General PUMCM, empirical tariffs, intrinsic subscription willingness, individual Pareto, global Nash and equilibrium uniqueness are not established.

The initial packaging checkpoint01 was not completed because the credential-pattern checker matched its own literal pattern; its matching expression was corrected and checkpoint02 is the valid committed archive. No equilibrium result was removed or recalibrated. Windows long paths require extracting the portable ZIP to a short directory. No Linux machine was used in this local run.
''')
print(json.dumps(valid,indent=2))
