"""Build the v5 audit report from saved results; performs no new experiments."""
from pathlib import Path
import csv, json, html
import run  # local numerical dependencies
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)
checks = json.loads((ROOT/'results/v5/independent_checks.json').read_text())
cases = sorted((ROOT/'results/v5').glob('*/summary.json'))
rows = sum(sum(1 for _ in csv.DictReader(p.with_name('od_costs.csv').open(encoding='utf-8'))) for p in cases)
profile = list(csv.DictReader((ROOT/'results/v5/sioux_node_node_total0_without/price_profile.csv').open(encoding='utf-8-sig')))
fig, ax = plt.subplots(figsize=(7, 2.8))
ax.plot([float(r['price']) for r in profile], [float(r['revenue'])/1000 for r in profile])
ax.axvline(2.601456, color='green', linestyle='--', label='v4 price 2.6015')
ax.axvline(3.65, color='red', linestyle=':', label='Paper price 3.65')
ax.set(xlabel='PT price per link', ylabel='PT revenue (thousands)', title='Fixed times and other leader decisions; no MaaS, node access')
ax.legend(); ax.grid(alpha=.2); fig.tight_layout()
fig.savefig(OUT/'v5_pt_price_profile.png', dpi=180); plt.close(fig)

ledger = '''# V5 source-to-code specification ledger

Scope: audits the selected v4 specialization, not recovery of the authors' full settings.

| Specification | Source | Implementation / evidence | Conclusion |
|---|---|---|---|
| OD dummy root and service-mode gates | Main paper Section 2 | Model.evaluate, group graphs; 18 explicit flattened graph comparisons | Equivalent for tested common scale 1; not all possible scales |
| Exclusive service copies within trip | Section 2 | Separate non-MaaS/MaaS/driving graphs | Structurally represented |
| Destination terminal treatment | Section 3.1 | Graph destination absorption and pruning | Zero terminal cost specialization; complete original terminal specification not recovered |
| PT fare per traversed link | Eq. 27 | PT edge price attribute; link-volume revenue | Represented; do not replace with fare per first boarding |
| PT ride time in Sioux Falls | Appendix A | 1.2 times road free-flow time | Source consistent |
| Initial PT waiting time 2 | Appendix A and Section 5.1.1 | Initial gate uses 2 | Unresolved: Appendix explicitly describes PT transfers; separate initial boarding value not identified |
| Transfer access and penalty | Section 5.1.3, Appendix A | Access time plus non-MaaS penalty 8 / MaaS 0.5 | Explicitly decomposed; units remain part of specialization |
| PT capacity | Appendix A, Table A2 | Access resources and physical links | Sharing of access capacity remains uncertain; Sioux physical limit 1e6, small-network application is assumption |
| MoD access demand aggregation | Section 5.1.1 | node and aggregate variants retained | Literal source favors aggregate; proximity of node results is not validation |
| PT operator revenue | Eqs. 19-20 | Retail plus wholesale, gradient decomposition | Included; 12 finite-difference checks |
| MaaS operator revenue | Eqs. 17-18 | OD receipts minus wholesale payments | v4 accounting retained; no behavioral change |
| Perturbation function and scale | Section 3.1; supplied PUME follow-up | Shannon specialization with common scale 1 | Supported mathematical specialization; original experimental scale not recovered |
| Reported mode share and transfers | Tables 2-3 | First boarding and link counts exported separately | Paper reporting definitions not fully identified |
| Solution algorithm | Eqs. 24-25 | v4 auxiliary VI refinement retained | Not replication of original iteration trajectory or proof of global Nash equilibrium |

Sources: supplied MaaS TRC article and PUME follow-up; local extracted text in sources/. These PDFs are not redistributed. Feedback is advisory, not experimental evidence.
'''
(ROOT/'notes/V5_SPECIFICATION_LEDGER.md').write_text(ledger, encoding='utf-8')
pages = [
('MaaS 재현 V5: 구조·비용 감사 결과', [
'작성일: 2026-10-23 (Asia/Seoul) | 브랜치: codex/maas-v5-spec-audit',
'결론: 계산과 검증은 완료했지만, 논문 Tables 2-3의 정량 재현은 아직 미완료입니다. 이번 버전은 기존 결과를 개선했다고 주장하지 않습니다. 재최적화에 앞서 불일치의 원인을 좁히는 구조·비용 감사를 수행했습니다.',
f'완료 범위: Sioux Falls 및 소규모 네트워크의 기존 기준선 6개, OD-모드 비용 행 {rows:,}개, 명시적 루트 그래프 비교 18개, 가격 미분 검증 12개입니다. 6개 기준선의 집계 지표 회귀 오차는 모두 0입니다.',
'모델의 수치 동작과 파라미터는 바꾸지 않았습니다. 간선 이름 추적, OD별 비용 분해, 자원 사용률, 대표 PT 경로, 고정 조건 가격 반응과 독립 검증을 추가했습니다.',
'핵심 성과: 더미 모드 노드의 압축 구현, 비용 합산, PT 수익 미분을 검증했습니다. 이 검증 범위에서 새로운 확정적 구현 오류는 발견하지 못했습니다. 남은 핵심 불확실성은 초기 PT 대기, 접근 수요/용량 집계, 섭동함수·척도 및 표의 지표 정의입니다.',
'자료의 역할을 구분했습니다. 원 논문은 재현 대상, 후속 PUME 논문은 수학적 참고, V4 피드백은 작업 우선순위 참고입니다. 후속 논문이나 피드백으로 원 실험의 미공개 설정을 확정하지 않았습니다.',
'본 보고서와 전체 CSV, 재실행 스크립트, 가정 원장을 함께 보존합니다. 사용자 제공 원문 PDF는 GitHub에 올리지 않습니다.'
]),
('1. 독립 검증과 아직 식별되지 않은 설정', [
f'명시적 루트 그래프 18개: 가치 최대 오차 {checks["max_root_value_error"]:.3g}, 흐름 최대 오차 {checks["max_root_flow_error"]:.3g}. 공통 척도 1에서 압축 구현과 일치했습니다. 다른 척도 조합까지 검증했다는 뜻은 아닙니다.',
f'PT 수익 기울기 12개: 분석 미분과 수치 분해의 최대 절대 차이 {checks["max_price_gradient_error"]:.3g}. 이는 10만 수준의 항을 합산하는 검증이며, 원 논문의 최적해를 찾았다는 뜻은 아닙니다.',
'PT 요금은 첫 탑승 횟수가 아니라 유료 PT 간선 통과량에 곱해집니다. MaaS 여행자의 소매 비용에 도매 지급액을 다시 넣지 않으며, PT 사업자 수익에는 도매 수익을 포함합니다.',
'초기 PT 대기 2는 미확정입니다. 부록의 PT 환승 시간 2와 초기 탑승 대기를 동일하게 두는 현재 가정이 원 실험과 같은지는 식별되지 않았습니다. 근거 없이 값을 조정하지 않았습니다.',
'MoD 접근 수요는 본문 5.1.1의 문자적 해석상 전체 집계가 우선입니다. 노드별 모델이 일부 지표에 가까워도 정답 설정으로 인정할 수 없습니다. 두 변형의 결과를 모두 보존합니다.',
'PT 접근 용량의 공유 범위와 초기 대기, Shannon 섭동 척도 1, 목적지 처리 및 지표 정의를 가정 원장에 분리했습니다. 전체 원장: notes/V5_SPECIFICATION_LEDGER.md.',
'수치 잔차가 작거나 비용 항등식이 맞는 것은 선택한 모델의 내부 일관성 증거입니다. 비선형 게임의 전역 균형 또는 원 실험의 복원 증거로 확대하지 않습니다.'
]),
('2. PT 경로 비용과 가격 불일치의 구체적 원인', [
'아래는 Sioux Falls, node/node, MaaS 없음, PT 가격 2.601456의 순수 PT 최소비용 경로입니다. 전체 확률적 배정 결과를 단일 경로로 대체한 것이 아닙니다.',
'1→3: 초기 접근 2 + 주행 4.8 + 요금 2.601456 = 9.401456.',
'1→13: 초기 접근 2 + 주행 13.2 + PT 3개 간선 요금 7.804369 = 23.004369.',
'1→18: 초기 접근 2 + 주행 31.2 + 환승 접근 2 + 환승 페널티 8 + PT 6개 간선 요금 15.608737 = 58.808737. 4→5는 순수 PT 경로가 없지만 다른 수단의 OD 연결은 가능합니다.',
'이 기준선에서 PT 접근 용량 최대 이용률은 약 53.65%이고, PT 용량 그림자 비용은 0입니다. 따라서 추가 대기가 0인 이유를 용량 계산 누락으로 해석할 수 없습니다.',
'기준 가격 2.601456에서 PT 수익은 292,166.70입니다. 다른 사업자 결정과 이동시간을 고정하고 가격만 논문 값 3.65로 바꾸면 수익은 282,901.34로 약 3.17% 감소합니다. 이는 교통 상태를 다시 푼 균형 결과가 아닙니다.',
'가격 3.65의 수익 미분: 직접 가격 효과 +77,507.22, 수요 감소 효과 -97,725.97, 도매 효과 0 → 합계 -20,218.76. 현재 모델에서는 논문 가격을 그대로 넣어도 최적반응 조건이 맞지 않습니다.',
'이때 첫 PT 탑승은 47,276.79, PT 간선량은 77,507.22입니다. 논문 수익 337,286과 가격 3.65가 같은 간선 과금 정의라면 요구 간선량은 92,407.12입니다. 이 비교는 보고 정의가 같다는 조건부 진단입니다.'
]),
('3. 결과 해석, 다음 실험 및 재개 방법', [
'아래 곡선은 고정된 시간·다른 사업자 결정에서의 가격 반응입니다. 교통 재균형이나 전체 다중 리더 재최적화 곡선으로 읽으면 안 됩니다.',
'가장 큰 미해결 문제는 수치 정밀도보다 원 실험 설정의 식별입니다. 이번 감사에서 확인한 음의 가격 기울기는 현재 비용·선택 구조가 논문과 다른 가격 반응을 만든다는 구체적 증거입니다.',
'다음 순서: (1) 공개 자료에서 초기 PT 대기, 접근 용량 공유, 섭동함수·척도, 표의 탑승/환승 정의에 대한 근거를 보강합니다. (2) 근거가 있는 설정 후보만 분리하고 작은 네트워크에서 비용 및 방향미분을 먼저 검증합니다. (3) 통과한 후보만 6개 기준선과 비교하며 재최적화합니다.',
'평가 기준은 PT 가격 한 개의 일치가 아닙니다. 가격·수익·첫 탑승·유료 간선량·수단 분담·전략적 이탈 및 수치 잔차를 함께 봅니다. 미확정 설정을 적합하면 복원이 아닌 보정 실험으로 명시합니다.',
'재개 자료: results/v5/의 case별 COMPLETE, summary.json, od_costs.csv, pure_pt_paths.csv, path_edges.csv, resources.csv, price_profile.csv 및 최상위 독립 검증 파일. 실행: python spec_audit_v5.py, python verify_spec_v5.py. 보고서만 재생성: python report_v5.py.',
'현재 감사 작업은 완료 상태입니다. 연결 중단 시 자동 재접속을 예약하지 않습니다. 사용자가 연결을 복구하고 지시하면 notes/RESUME.md와 Git 태그에서 이어갑니다.'
])]
md = '# MaaS 재현 V5 감사 보고서\n\n' + '\n\n'.join('## '+title+'\n\n'+'\n\n'.join(paras) for title,paras in pages)
(ROOT/'REPRODUCTION_V5.md').write_text(md, encoding='utf-8')
pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
c = canvas.Canvas(str(OUT/'MaaS_reproduction_v5_ko.pdf'), pagesize=(595.28,841.89))
c.setTitle('MaaS reproduction V5 specification audit')
for i,(title,paras) in enumerate(pages,1):
    c.setFont('MalgunBold',16); c.drawString(42,794,title)
    y=758
    for para in paras:
        c.setFont('Malgun',10)
        for line in simpleSplit(para,'Malgun',10,511):
            c.drawString(42,y,line); y-=16
        y-=13
    if i==4:
        c.drawImage(str(OUT/'v5_pt_price_profile.png'),42,65,width=511,height=204,preserveAspectRatio=True)
        assert y>280, y
    assert y>45, (i,y)
    c.setFont('Malgun',8); c.drawString(42,28,f'V5 | 2026-10-23 | {i}/4 | 정량 재현 미완료 · 감사 완료')
    c.showPage()
c.save()
print(json.dumps({'cases':len(cases),'od_mode_rows':rows,'pdf':str(OUT/'MaaS_reproduction_v5_ko.pdf')}, ensure_ascii=False))

