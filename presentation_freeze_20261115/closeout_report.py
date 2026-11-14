"""Generate closeout evidence tables and figures from audited saved outputs."""
from pathlib import Path
import json,csv,hashlib,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from verify_presentation_release import ROOT,read,rows,verify
D=ROOT
def text(n,s):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def dump(n,x):text(n,json.dumps(x,ensure_ascii=False,indent=2))
audit=verify(False);f=audit.pop('facts');dump('baseline_audit/replay.json',audit);dump('baseline_audit/facts.json',f)
def save(fig,name,caption):
 fig.text(.02,.015,caption,fontsize=8,wrap=True);fig.tight_layout(rect=(0,.1,1,1))
 for ext in ['png','svg']:fig.savefig(D/'figures'/f'{name}.{ext}',dpi=180)
 plt.close(fig)
(D/'figures').mkdir(exist_ok=True)
fig,ax=plt.subplots(1,2,figsize=(11,4))
ax[0].bar(['B - A','C - A'],[f['E01_AB'],f['E01_AC']],color=['steelblue','teal']);ax[0].set(title='Re-equilibrated E01',ylabel='Total expected utility change (model units)')
ax[1].bar(['Actual B\nstatic product','Independent\nclone','Split\ncorrected'],[f['placebo'][k] for k in ['actual_B_product_B_fares','independent_clone','split_corrected']],color=['gray','orange','gray']);ax[1].set(title='Static placebo at frozen A (not equilibrium)',ylabel='Logsum change (model units)')
save(fig,'FIG_E01_platform_vs_transfer','Sources: E01 saved metrics; e01_placebo_static.csv. A=no MaaS; B=entry; C=transfer advantage. No causal market benefit claim.')
fig,ax=plt.subplots(figsize=(10,5));es=[r for r in rows(D/'sources/e03_all_results_reaudited.csv') if r['run'].startswith('E03_coarse/')]
groups=collections.defaultdict(list)
for r in es:
 label='Failed VI (1)' if r['status']!='PASS' else 'All OD averages non-worse (14)' if r['L2']=='IMPROVING' else 'Aggregate gain, OD loss (17)' if r['L1']=='IMPROVING' else 'Valid, no joint gain (32)'
 groups[label].append(r)
for label,rr in groups.items():ax.scatter([float(r['c_mod']) for r in rr],[float(r['c_pt']) for r in rr],label=label,s=85,marker='x' if 'Failed' in label else 'o')
ax.set(xlabel='MoD wholesale price (model units)',ylabel='PT wholesale price (model units)',title='E03: 8 x 8 grid; original failed cell retained');ax.legend(fontsize=8,loc='center left',bbox_to_anchor=(1.01,.5))
save(fig,'FIG_E03_wholesale_levels','Source: e03_all_results_reaudited.csv. L1=aggregate joint improvement; L2=all OD means non-worse. Individual Pareto status not identified.')
fig,axs=plt.subplots(1,3,figsize=(12,4))
for s in 'BC':
 rr=sorted([r for r in f['cloud'] if r['case'].startswith(s)],key=lambda r:float(r['case'].split('lambda')[1]));xx=[float(r['case'].split('lambda')[1]) for r in rr]
 for ax,key,title in zip(axs,['profit_maas','welfare_gain','harmed_od'],['Platform profit (model units)','Utility gain vs A (model units)','Harmed OD averages (count)']):ax.plot(xx,[r[key] for r in rr],'o-',label=s);ax.set(xlabel='Nested choice lambda',title=title);ax.legend()
save(fig,'FIG_BEHAVIOR_nested_lambda','Source: 10 audited cloud_reference states. Lambda is assumed, not estimated. Nested Choice is not the M03 nested solution algorithm.')
fig,axs=plt.subplots(1,3,figsize=(12,4))
axs[0].bar(['M01','Root\noriginal SCORE'],[0,9],color=['orange','teal']);axs[0].set(title='Distinct campaigns: PASS counts',ylabel='Passed attempts');axs[0].text(0,.3,'0 / 27',ha='center');axs[0].text(1,8,'9 / 9',ha='center')
gg=f['Root_groups'];axs[1].bar(['Nested\ndefault','Nested\nrestart','DEMAND'],[gg[k]['PASS'] for k in ['nested_default','nested_restarts','DEMAND']]);axs[1].set(title='Root subgroups: 9/10, 2/2, 1/3',ylabel='Passed attempts')
axs[2].bar(['Joint','Nested'],[1490,12309],color=['teal','steelblue']);axs[2].set(title='M03: same VI, one warm start',ylabel='Total H calls including validation')
save(fig,'FIG_SOLVER_M01_ROOT_M03','Sources: M01 CSV, 24 Root metrics, M03 summary. Different budgets/sessions; no general speed ranking, global convergence or paper-EG claim.')
columns='claim_id,topic,paper_section,paper_claim,reimplementation_assumption,experiment_id,source_path,git_commit,input_sha256,parameters,observed_result,validation_status,evidence_class,allowed_presentation_wording,caveat'.split(',')
ledger=[]
def claim(cid,topic,source,obs,word,caveat,cls='REPRODUCED_MECHANISM',section='Sections 3-5; independent reconstruction'):
 ledger.append(dict(zip(columns,[cid,topic,section,'See original-paper distinction in paper_defense_ledger; reconstruction values are not author values','Shannon specialization; Small appendix network; node-specific MoD access',cid,source,'4d9bbc450cbfafe97744047dd943e6bd7ac65942 / local 8c3270c8a6841d41a947ecabb25afb9438e84a52',hashlib.sha256((D/source).read_bytes()).hexdigest(),'See source configs; price and utility in model units',json.dumps(obs,ensure_ascii=False),'SOURCE_VERIFIED',cls,word,caveat])))
claim('PAPER','Original framework','sources/paper_defense_ledger.csv','PUMCM / VI framework','원문은 다수 운영자의 전략적 상호작용과 교통균형을 결합한다.','저자 수치와 본 재구현 수치를 혼용하지 않음','ORIGINAL_PAPER')
claim('E01','Entry and transfer','baseline_audit/facts.json',{k:f[k] for k in ['E01_AB','E01_BC','E01_AC']},'플랫폼 진입과 환승 가정의 효과를 구분한 모형 내 반사실 비교이다.','실제 시장 순인과 편익이 아님')
claim('P0-1','Static duplication','sources/e01_placebo_static.csv',f['placebo'],'동일상품을 독립 대안으로 복제하면 Logsum이 증가한다.','Shannon/MNL 특수화 진단; 일반 PUMCM의 오류 증명 아님','DIAGNOSTIC_ONLY')
claim('P0-2','Physical PT metrics','sources/pt_channel_summary.csv',f['PT'],'실제 PT 이용통행과 PT 링크 이용량은 다른 지표이다.','원문 Table 2 지표와 직접 동등하지 않음')
claim('E03','Distribution of gains','sources/e03_all_results_reaudited.csv',{k:f[k] for k in ['E03_total','E03_PASS','E03_L1','E03_L2','E03_L1_with_OD_loss']},'집계 공동개선 31개 중 17개는 일부 OD 평균 후생이 감소한다.','개인별 Pareto 개선은 NOT_IDENTIFIED')
claim('v8','Choice correlation','baseline_audit/facts.json',f['cloud'],'상위 선택의 상관성 가정에 따라 플랫폼 이익과 후생이 민감하게 변한다.','lambda는 실험 가정이며 실제 추정값 아님','NEW_COUNTERFACTUAL')
claim('M01','Original solver attempts','sources/m01_convergence_runs.csv',dict(total=27,PASS=0,H_budget=20000),'현재 재구현 설정에서 PG/EG 27개 시도가 수치검사를 통과하지 못했다.','원 논문 EG의 일반 실패를 뜻하지 않음','DIAGNOSTIC_ONLY')
claim('Root','Auxiliary root method','baseline_audit/facts.json',f['Root_groups'],'동일 VI 조건을 검증하는 Flow-coordinate/SCORE 보조 root 해법에서 유효해를 확보했다.','EG 알고리즘 개선, 전역 Nash, 유일성, 전역수렴 주장 아님')
claim('M03','Joint versus nested same VI','sources/m03_summary.json',f['M03'],'하나의 Small warm-start 사례에서 Joint와 Nested가 근접한 경제결과를 얻었다.','8.26배의 보편적 속도 우위가 아님; Nested Choice와 구별','DIAGNOSTIC_ONLY')
claim('M02','Strategic timing','sources/m02_timing_comparison.csv',{'finite_probes':12},'고정 교통상태와 교통 재균형을 허용한 가격변경은 다른 게임 해석이다.','유한 가격변경만 조사; 전역 최적반응/Stackelberg 균형 증명 아님','NEW_COUNTERFACTUAL')
claim('PERSON','Individual gains','sources/e03_welfare_levels.csv','NOT_IDENTIFIED','OD 평균 결과만 관측했다.','개인별 Pareto 개선 및 실증적 정책효과는 측정하지 않음','NOT_IDENTIFIED')
with (D/'CLAIM_LEDGER.csv').open('w',encoding='utf-8',newline='') as h:w=csv.DictWriter(h,fieldnames=columns);w.writeheader();w.writerows(ledger)
text('ONE_PAGE_SLIDE_NUMBERS.md',f'''# 발표용 핵심 수치 — 독립 Small 재구현

| 근거 | 검증된 수치 | 단위·해석 |
|---|---|---|
| E01 | B−A {f['E01_AB']:.2f}; C−B {f['E01_BC']:.2f}; C−A {f['E01_AC']:.2f} | 총 기대효용, 모형 단위 |
| 정적 Placebo | 독립복제 +575.18; 분할보정 0; 실제 B상품 +113.56 | A 상태 고정; 재균형 아님 |
| E03 | 64 중 63 PASS; 공동개선31; OD 비악화14; 공동개선이나 OD손실17 | 3 OD 평균; 개인 Pareto 아님 |
| Nested Choice B | λ1→.55 이익123.40→44.40; 후생증가103.29→26.94; 손실OD0→1 | 새로운 행동 반사실; λ 미추정 |
| M01 | 27 중 0 PASS | 시도별 solver H=20,000 |
| Root | 원모형9/9; Nested기본9/10; 재시작2/2; DEMAND1/3 | 총24 중21 STRICT PASS; 3실패 보존 |
| M03 | Joint/Nested PASS; H1,490/12,309 | 단일 warm-start, 세션 다름 |

PT 실제 이용통행/링크이용량 A,B,C: {json.dumps(f['PT'],ensure_ascii=False)}

수치 출처와 SHA: CLAIM_LEDGER.csv 및 baseline_audit/facts.json. 원 논문 Table 2/3의 수치가 아니다.
''')
text('MODEL_SCOPE_AND_LIMITATIONS.md','''# 모형 범위 및 제한

원문: Yao, Ma & Zhang (2026), TRC 188,105703, DOI 10.1016/j.trc.2026.105703. 원문에 대한 기존 21개 검토 항목은 sources/paper_defense_ledger.csv에 보존했다. 원문 PDF와 비공개 프롬프트는 배포하지 않는다.

이 구현은 일반 PUMCM의 Shannon 특수화이며 상위 선택은 기본 MNL이다. Nested Choice는 별도 상관성 반사실 확장이다. 수요는 Small 3 OD, 총1,000이며 네트워크·물리 공급은 baseline/src/model.py inputs 및 config에 명시된다. 시간·비용의 효용환산 및 가격/선택척도는 모형 설정값이며 실증 추정치가 아니다.

원문은 MoD 접근용량 집계 제약을 설명하지만 본 재구현은 node별 MoD 접근용량을 사용한다. PT 용량의 의미, 접근/환승 구조, 경로선택 특수화, 효용/가격 단위의 차이가 있으므로 원문 수치의 정밀 복제라 주장하지 않는다. B는 A와 같은 환승 불편 설정, C는 환승 페널티를 낮춘 조건이다. 비MaaS에도 멀티모달 이동이 허용된다. 임의 보정은 하지 않았다.

총 Logsum은 대안집합과 오차 상관성에 민감하다. 가입비·인증비·플랫폼 운영비·현실적 운임/보조금을 포함한 순편익이 아니다. PT 최초 접근, 판매채널, 실제 탑승 통행, 링크 횟수는 구별한다. OD 평균과 개인별 후생은 다르다.

VI 가격 미분은 교통상태를 고정한 편미분이다. 교통 반응을 내재화한 최적반응 게임과 동일시하지 않는다. 비볼록 게임의 VI 필요조건 및 제한된 가격이탈 검증은 전역 Nash/유일성의 증명이 아니다. Root는 동등 조건을 찾는 보조 해법이며 원 논문 extragradient의 알고리즘 개선이 아니다.

이번 동결의 새 재검증 범위는 Small이다. Sioux Falls 전체·스위스/로잔 시장·실측 수단분담에 일반화하지 않는다. 실행 환경과 예산이 다른 M01/Root/M03를 공정한 성능순위로 비교하지 않는다.
''')
failrows=[(p.parent.name,read(p)['status']) for p in (D/'baseline/results/vi_cloud_20261114/runs').glob('*/metrics.json') if read(p)['status']!='PASS']
early=[(p.parent.name,read(p).get('status')) for p in (D/'baseline/results/research_v7_1/m01_improved_20261110').glob('*/metrics.json')]
text('OPEN_ISSUES_AND_FAILURES.md',f'''# 실패·미해결 사항

- E03 원래 실패점: {f['E03_failures']}. 이후 이웃 조건/재시작과 혼합하지 않음.
- M01 27회 모두 FAILED_NUMERICAL_CHECK. sources/m01_convergence_runs.csv와 states/의 최종 실패 상태 보존. 교통잔차 정체 및 역BPR 경계의 민감도는 보조 원인 진단이며 단일 원인 증명이 아니다.
- 최초 Root 12회 상태: {json.dumps(early)}. 낮은 잔차에도 가격이탈 이익이 큰 후보 및 원시간 잔차 실패를 보존했다.
- 최신 Root 실패3개: {json.dumps(failrows)}. Bλ=.65 기본 시작점의 실패는 .95와1.05 재시작 성공으로 삭제하지 않음.
- M03 기존 Nested 중단은 sources/m03_original_interruption.json에 보존. 후속 attempt2 PASS는 별도 결과이다.
- 가격이탈과 유한차분의 기존 상세 검증은 아카이브로 보존하며 본 closeout은 최적화기를 다시 돌리지 않았다. 저장 경제량·잔차 및 18개 커널 검사는 재실행했다.
- 원문/재구현 MoD 접근용량 차이, 일반 PUMCM 대 Shannon, 개별 후생 및 실증 가입선택은 미해결이다.
- E05는 신규 집단모형을 구현/검증하지 않았으므로 E05_NOT_RUN_DESIGN_ONLY. 실패한 계산이 있거나 검사를 통과했다는 뜻이 아니다.
''')
text('FINAL_EVIDENCE_SUMMARY_KR.md',f'''# MaaS 재현 최종 증거 정리

최종 상태: **FROZEN_BASELINE_ONLY**. 기준선 저장해와 출처를 검증하고 발표 근거를 동결했다. 추가 균형 탐색은 실행하지 않았다. E05는 선택적 설계 메모로 남겼다.

원문은 PUMCM을 활용해 다수 운영자의 가격경쟁과 멀티모달 교통균형을 연결하고 VI로 계산하는 유망한 방법을 제안한다. 경로/선택과 시장을 한 모형으로 분석하는 점이 기여이다. 독립 재구현으로 그 작동 원리와 조건부 민감도를 검증했으며 저자 실험의 모든 수치를 복제했다는 결론은 내리지 않는다.

모형적으로 Shannon 특수화와 MoD 접근용량 구현 차이를 남겼다. 행동적으로 독립대안 복제의 Logsum 효과와 Nested Choice 민감도를 확인했다. 시장적으로 총량 공동개선과 OD 평균 분배 결과가 달랐으며, 고정 교통상태 가격미분과 교통반응을 고려한 이탈은 다른 질문이다. 수치적으로 기존 PG/EG 정체에 대해 Flow-coordinate/SCORE root가 유효한 대안을 제공했으나 이는 전역수렴 보장이 아니다.

E01의 기대효용 증가는 B−A {f['E01_AB']:.5f}, C−B {f['E01_BC']:.5f}이다. 정적 독립복제 +575.18, 분할보정0은 균형 편익과 분리한다. E03 64개 중63 PASS, 집계 공동개선31, 모든 OD 평균 비악화14이며 나머지 공동개선17개는 일부 OD 손실을 동반한다. 개인별 Pareto 개선은 NOT_IDENTIFIED이다.

Nested Choice B에서 λ1→.55에 플랫폼 이익123.40→44.40, A 대비 후생증가103.29→26.94, 손실 OD0→1이다. C도 상관성 변화에 민감하나 이 격자에서는 OD 평균 손실이 없다. λ는 실측 추정값이 아니다.

M01 27회는 모두 실패 상태를 유지했다. 최신 Root 저장24개는21 STRICT PASS와3 FAILED_VALIDATION을 유지한다. 원모형 SCORE9/9, Nested 기본9/10, 실패조건 재시작2/2, DEMAND1/3이다. M03 Joint/Nested는 둘 다 통과하고 H 호출은1,490/12,309이다. 이 단일 warm-start 사례로 일반적인 속도 우위를 주장하지 않는다.

이번 감사는 추가 저장상태와 최신24개를 합해 {audit['replayed_states']}개 경제량/잔차 replay 및18개 Nested 커널·회귀·유한차분 검사를 수행했다. 원래 상태표시를 유지했고 신규 최적화는0회이다. 사용한 manifest, 숫자 대조 및 실패 원자료는 baseline_audit/와 baseline/에 있다.

후속 연구는 행동적 이질성, 외생적 MaaS 접근집합, 현실적 운임과 수요 추정, 동일 예산의 솔버 비교이다. 이번 발표 범위에서는 전역 Nash/유일성, 개인 Pareto, 실제 정책 순편익, Sioux Falls/스위스 시장 검증 및 원 논문 EG의 일반 실패를 제외한다. 4개 발표 그림과 CLAIM_LEDGER를 바탕으로 발표 단계로 전환한다.
''')
text('e05_lite/E05_METHOD_AND_DERIVATIVES.md','''# E05_NOT_RUN_DESIGN_ONLY

이번 선택 실험은 실행하지 않았다. 기존 근거 동결을 우선했으며 별도 subclass 구현과 100% eligibility 회귀검증(게이트2–4)은 NOT_ASSESSED이다. C0 PASS만으로 신규 집단모형 검증을 대체하지 않는다. 신규 solve/H 호출0; 새 STRICT_PASS0.

설계: OD 수요 q를 eq와 (1-e)q로 분할. 적격집합은 drive/non/MaaS, 비적격은 drive/non. 물리 시간 t, 소매가격, 링크용량은 공유하고 공급을 복제하지 않는다. 총유량 f=e f_E+(1-e)f_N이며 H_t=supply(t)-f이다. 이익/후생은 집단 수요 가중 합, 소매가격 H는 집단별 음의 편미분의 합이다. MaaS 요금 F의 λ=1 미분은 H_F=e q P_M[(F-c)(1-P_M)/mu-1]. e>0, P_M>0일 때 SCORE 정상화는 대괄호이다. e=0에는 정규화를 적용하지 않는다.

실행하려면 A의 e 불변, e=1 B/C의 H/확률/회계/후생 일치, e=.5 수요합/확률합/공급 공유, 모든 가격과 시간의 유한차분을 먼저 확인해야 한다. 가격 및 혼잡은 함께 재균형해야 하며 사후 확률만 절반으로 줄이는 방법은 허용하지 않는다. 이번 릴리스에는 검증된 집단모형 코드나 E05 균형값이 없다.

추후 별도 승인 범위: λ=1, e=.5 B/C만, cold start1; 실패 시 .95 또는1.05 하나. 시도별 H≤8,000(수치Jacobian 포함), 총4회/32,000 이하. 이 문서는 실행 예약이 아니며 동결 버전을 수정하지 않는다.
''')
dump('e05_lite/E05_TESTS.json',dict(status='NOT_RUN',reason='Optional design-only closeout; group-model implementation and regression gates not assessed',new_solver_runs=0,new_H_calls=0))
dump('e05_lite/E05_BASELINE_REGRESSION.json',dict(status='NOT_ASSESSED',C0='PASS',group_model_regression='NOT_RUN'))
text('e05_lite/E05_RESULTS.csv','experiment_id,eligible_share,scenario,lambda,start_factor,h_calls,strict_pass,natural_direct,full_scaled,capacity_violation,complementarity,price_deviation_gain,profit_mod,profit_pt,profit_maas,welfare_total,maas_share_total,maas_share_eligible,mod_physical_volume,pt_physical_volume,transfers,model_source,assumption_note\n')
text('e05_lite/E05_OD_GROUP_RESULTS.csv','experiment_id,od_id,group,group_demand,group_welfare_per_person,group_welfare_change_vs_A,group_harmed_flag\n')
text('e05_lite/E05_FAIL_AND_RETRY_LOG.csv','experiment_id,attempt,status,h_calls,reason\nE05_LITE,0,NOT_RUN,0,Optional design only; no solver attempts\n')
text('e05_lite/E05_INTERPRETATION_AND_LIMITS.md','No E05 numerical result exists. No eligibility effect, subsidy effect, subscription willingness or individual Pareto claim is supported. No E05 figure is produced.\n')
text('README_RELEASE_KR.md','''# 발표용 최종 동결 — FROZEN_BASELINE_ONLY

FINAL_EVIDENCE_SUMMARY_KR.md → ONE_PAGE_SLIDE_NUMBERS.md → CLAIM_LEDGER.csv → figures/ 순서로 확인하십시오. C1의 presentation_release snapshot은 이 릴리스 루트이며 중복 폴더 대신 단일 manifest로 잠근다.

검증: `python verify_presentation_release.py`. 의존성은 requirements.txt. 기본 작업은 저장해 검증이며 최적화하지 않는다. Windows에서 검증했고 Linux 호환 코드를 제공하지만 Linux 실제 실행을 주장하지 않는다.

baseline/에는 기존 공개 VI 전달 패키지를 그대로 보존했다. states/에는 E01/E03 및 v6 기타 결과, M01 실패, M03, 클라우드 상태를 추가 보존했다. 각 원출처/해시는 baseline_audit/에 있다. 최신 Root 24개 중21 STRICT PASS/3실패; E05 신규0회이다. 기존 결과 및 실패를 덮어쓰지 않았다.

원자료 PDF, 개인 프롬프트, 개인 절대경로, 불필요한 대형 파일은 배포하지 않는다. 기존 전체 연구 Git 이력은 공개하지 않고 이미 공개된 4d9bbc4 기반의 새 브랜치에 이 폴더만 추가한다. ZIP hash 및 최종 커밋은 릴리스 외부 DELIVERY.json에 기록한다(자기참조 해시 방지).
''')
text('REPLAY_AND_RESUME.md','''# Replay and handoff

Extract the ZIP into a short folder. Use Python 3.11+ and install requirements.txt into an isolated environment. Run `python verify_presentation_release.py > replay_output.json` with the output redirected OUTSIDE the extracted release (the manifest disallows unexpected files). The command runs saved-state evaluations and kernel/derivative checks, never an equilibrium optimizer. Bytecode caches are excluded from inventory checks.

Read baseline_audit/replay.json for the original build audit. verify_presentation_release.py checks whole-release hashes, schemas, source-derived figures' numbers, status preservation, economics and natural residuals, and 18 nested checks. Archived price-deviation optimizer searches are not rerun. The source-derived facts must match the frozen facts exactly on the source read; floating-point replays allow documented tolerances.

baseline/replay_vi_results_20261114.py can independently replay just the original24. Old source runners are historical evidence, not the default entry point. Never rerun them into protected results directories. To extend after the freeze, create a new branch/output directory and record input hashes first. No pending solver or scheduled continuation remains in this release. E05 is design-only and requires fresh implementation/gates, not continuation from a hidden checkpoint.

SHA256SUMS covers all payloads plus RELEASE_MANIFEST; the manifest hashes all payloads excluding itself and SHA256SUMS to avoid circular hashes. DELIVERY.json lives beside the ZIP and identifies the public commit and ZIP hash. Windows replay is verified; cloud Linux execution remains a user-side portability test.
''')
dump('RELEASE_MANIFEST.json',dict(status='FROZEN_BASELINE_ONLY',baseline_audit='PASS',E05='E05_NOT_RUN_DESIGN_ONLY',root_strict_pass=21,root_total=24,new_equilibrium_runs=0,source_zip='MaaS_VI_Cloud_20261114.zip',source_git_commit='4d9bbc450cbfafe97744047dd943e6bd7ac65942',publication_branch='codex/maas-v71-presentation-freeze-20261115',omissions=['Copyright PDFs and source text','Private instructions and local absolute paths','Full historical Git history','Other research outputs not needed for frozen claims; hashes retained in protected_source_hashes.json'],files={p.relative_to(D).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ['RELEASE_MANIFEST.json','SHA256SUMS.txt']}))
text('SHA256SUMS.txt',''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(D).as_posix()}\n' for p in sorted(D.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS.txt'))
print(json.dumps(dict(status='FROZEN_BASELINE_ONLY',replayed=audit['replayed_states'],strict_root_pass=21,figures=4),indent=2))
