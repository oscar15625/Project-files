"""Build a Korean handoff research report from saved, explicitly gated results."""
from research_experiments import *
import html
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
PDF=ROOT/'output/pdf'; PDF.mkdir(exist_ok=True)
FIG=OUT/'figures'; FIG.mkdir(exist_ok=True)
rows=list(csv.DictReader((OUT/'all_results.csv').open(encoding='utf-8-sig')))
summary=json.loads((OUT/'summary.json').read_text())
contrasts=list(csv.DictReader((OUT/'E01_contrasts.csv').open(encoding='utf-8-sig')))
e01={k:json.loads((folder('E01',k)/'metrics.json').read_text()) for k,_ in cases('E01')}
A=e01['A_no_maas']; B=e01['B_maas_no_transfer_advantage']; C=e01['C_maas_paper_advantage']
phase='E03_coarse' if summary['coarse_executed'] else 'E03_pilot'
grid=[r for r in rows if r['phase']==phase]; values=sorted({float(r['c_mod']) for r in grid})
size=len(values)
if phase=='E03_coarse': assert len(grid)==64, 'Report only after full planned grid finishes'
else: assert len(grid)==9
def f(v,d=2): return f'{float(v):,.{d}f}'
def arr(key):
    z=np.full((size,size),np.nan)
    for r in grid:
        if r['status']=='PASS' and r.get(key) not in ['',None]: z[values.index(float(r['c_mod'])),values.index(float(r['c_pt']))]=float(r[key])
    return z
region=np.full((size,size),3.)
for r in grid: region[values.index(float(r['c_mod'])),values.index(float(r['c_pt']))]={'IMPROVING':1,'NOT_IMPROVING':0,'INDETERMINATE':2,'FAILED':3}[r['private_aggregate_status']]
fig,ax=plt.subplots(figsize=(6.6,4.4)); im=ax.imshow(region,origin='lower',cmap=ListedColormap(['#e1b3a6','#67a69c','#ead294','#777777']),vmin=-.5,vmax=3.5)
ax.plot(np.arange(size),np.arange(size),'k--',lw=1,label='Equal wholesale price')
for r in grid:
    if r.get('harmed_od_count') and int(r['harmed_od_count'])>0: ax.text(values.index(float(r['c_pt'])),values.index(float(r['c_mod'])),'x',ha='center',va='center',fontsize=13)
ax.set_xticks(range(size),[f'{v:g}' for v in values]); ax.set_yticks(range(size),[f'{v:g}' for v in values])
ax.set(xlabel='PT wholesale price per utilized link',ylabel='MoD wholesale price per utilized link',title='Tested grid points; x = some OD-average utility declines')
cbar=fig.colorbar(im,ax=ax,ticks=[0,1,2,3]); cbar.ax.set_yticklabels(['Not improving','Aggregate improvement','Indeterminate','Failed'])
ax.legend(fontsize=8,loc='upper left'); fig.tight_layout(); fig.savefig(FIG/'wholesale_region.png',dpi=180); plt.close(fig)
def panels(keys,titles,name):
    fig,axs=plt.subplots(2,2,figsize=(8,5.8))
    for ax,key,title in zip(axs.flat,keys,titles):
        z=arr(key); image=ax.imshow(z,origin='lower',cmap='viridis')
        if np.isfinite(z).any() and np.nanmin(z)<0<np.nanmax(z): ax.contour(z,levels=[0],colors='white',linewidths=.8)
        ax.plot(np.arange(size),np.arange(size),'w--',lw=.6)
        ax.set_xticks(range(size),[f'{v:g}' for v in values],fontsize=7); ax.set_yticks(range(size),[f'{v:g}' for v in values],fontsize=7)
        ax.set(xlabel='PT wholesale',ylabel='MoD wholesale',title=title); fig.colorbar(image,ax=ax,shrink=.8)
    fig.tight_layout(); fig.savefig(FIG/name,dpi=170); plt.close(fig)
panels(['delta_profit_mod','delta_profit_pt','profit_maas','delta_traveler_welfare'],['MoD profit change','PT profit change','Platform profit','Traveler utility change'],'economic_surfaces.png')
panels(['price_mod','price_pt','share_maas','share_drive'],['MoD retail price','PT retail price','MaaS share (%)','Driving share (%)'],'price_share_surfaces.png')
good=[r for r in grid if r['status']=='PASS']; improving=[r for r in good if r['private_aggregate_status']=='IMPROVING']; harms=[r for r in improving if int(r['harmed_od_count'])>0]
pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf')); pdfmetrics.registerFont(TTFont('MalgunB','C:/Windows/Fonts/malgunbd.ttf'))
body=ParagraphStyle('body',fontName='Malgun',fontSize=9.3,leading=14.5,spaceAfter=8,wordWrap='CJK')
title=ParagraphStyle('title',parent=body,fontName='MalgunB',fontSize=16,leading=22,spaceAfter=13,textColor=colors.HexColor('#163c4a'))
cell=ParagraphStyle('cell',parent=body,fontSize=8,leading=11,spaceAfter=0)
story=[]; md=[]
def p(s): story.append(Paragraph(html.escape(s),body)); md.append(s+'\n')
def page(s):
    if story: story.append(PageBreak())
    story.append(Paragraph(html.escape(s),title)); md.append('## '+s+'\n')
def table(h,data,widths):
    t=Table([[Paragraph(html.escape(str(v)),cell) for v in row] for row in [h]+data],colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebef')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f7')]),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([t,Spacer(1,10)])
    md.append('| '+' | '.join(h)+' |\n| '+' | '.join(['---']*len(h))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in data)+'\n')
def figure(name,w,h):
    story.extend([Image(str(FIG/name),width=w,height=h),Spacer(1,8)]); md.append(f'![{name}](results/research_v6/figures/{name})\n')

page('MaaS 연구 실험 보고서 | 2026-11-08')
p('실험 시작: 2026-11-06 · 중단 후 체크포인트 재개 및 최종 정리: 2026-11-08')
p('이번 작업은 과거 최종 재현 V6와 구분되는 새 연구 실험입니다. 사용자 지시서에 따라 V5 태그(ac330d4)에서 별도 로컬 브랜치를 만들고 G00 → R01 → E01 → E03을 수행했습니다. 원 논문 수치를 맞추는 보정 실험이 아닙니다.')
table(['구분','수행 내용','판정'],[
['G00','6개 기준선 재평가, 기존 검증 3종, 파일 해시 봉인','PASS / 원본 변경 없음'],
['R01','초기 대기·집계·척도·지표 정의의 출처 원장','미확정 항목 유지'],
['E01','작은 네트워크 A/B/C 동일 해법 대조','3개 PASS'],
['E03',f'3×3 시범 + {size}×{size} 도매가격 격자',f'최종 격자 {len(good)}/{len(grid)} PASS'],
['M01','PG / EG_FIXED / EG_ADAPT 공통 인터페이스','18개 최소 동작 검사; 성능 비교 아님']],[67,295,135])
p(f'주요 결과 1: 환승 혜택이 없는 플랫폼 진입(A→B)도 이용자 후생을 {f(B["traveler_welfare"]-A["traveler_welfare"])} 높였습니다. 추가 환승 페널티 감소(B→C)는 {f(C["traveler_welfare"]-B["traveler_welfare"])}의 개선을 더했습니다. 따라서 이 설정에서 모든 MaaS 편익이 환승 혜택만으로 생긴 것은 아닙니다.')
p(f'주요 결과 2: 최종 격자 {len(grid)}점 중 운영자·플랫폼·총 이용자 후생의 공동 개선점은 {len(improving)}개입니다. 그중 {len(harms)}개는 적어도 한 OD의 평균 기대효용이 감소했습니다. 총량 기준 상생과 모든 OD의 개선을 구분해야 합니다.')
p('범위: 고정 OD 수요, node/node 접근 집계, Shannon 척도 1, 작은 네트워크의 기존 구성에 조건부인 반사실 분석입니다. 원문과 동일한 수치 균형 복원, 실제 가입·협상 예측, 모든 개인의 Pareto 개선 또는 전역 Nash 균형 증명을 주장하지 않습니다.')
p('제공 지시서의 공개 업로드 금지에 따라 새 결과는 로컬 브랜치와 복구 번들에 저장했습니다. 기존 V5/V6 태그 및 결과는 덮어쓰지 않았습니다.')

page('1. E01: 플랫폼 도입과 환승 혜택의 분리')
p('A: MaaS 미도입. B: MaaS 도입, 양쪽 환승 페널티 10. C: MaaS 도입, MaaS 페널티 1 / non-MaaS 10. 물리적 접근시간·도로·PT 노선·용량·총수요·도매가격(1.3,1.3)은 동일합니다. 모든 가격과 교통 상태는 각 시나리오에서 다시 풀었습니다.')
table(['지표','A 미도입','B 혜택 없음','C 혜택 있음'],[[label,f(A[key],digits),f(B[key],digits),f(C[key],digits)] for label,key,digits in [('MoD 수익','profit_mod',2),('PT 수익','profit_pt',2),('플랫폼 이익','profit_maas',2),('이용자 후생','traveler_welfare',2),('사회후생','social_welfare',2),('MaaS 점유율 (%)','share_maas',2),('자가용 점유율 (%)','share_drive',2),('환승량','transfer_flow',4)]],[170,109,109,109])
table(['차이','MoD 수익','PT 수익','플랫폼 이익','이용자 후생'],[[r['contrast'],f(r['profit_mod']),f(r['profit_pt']),f(r['profit_maas']),f(r['traveler_welfare'])] for r in contrasts],[109,90,90,99,109])
ratio=(C['traveler_welfare']-B['traveler_welfare'])/(C['traveler_welfare']-A['traveler_welfare'])*100
p(f'B에서도 두 기존 운영자의 수익과 총 이용자 후생은 증가하고 플랫폼 이익은 양수입니다. 환승량은 거의 변하지 않지만 가격 경쟁·서비스 선택 대안의 추가만으로 편익이 생깁니다. B→C의 이용자 후생 차이는 A→C의 {f(ratio)}%입니다.')
p('이 비율은 고정된 비교 순서의 산술적 차이 분해입니다. 비선형 시장의 상호작용을 제거한 인과적 기여율이 아닙니다. 순서를 바꾸거나 플랫폼 도입과 다른 비용 변화를 동시에 허용하면 해석도 달라집니다.')
p('원문 Table 2의 미도입 MoD/PT 수익은 1,176.7 / 664.1이고, MaaS 10% 페널티 열은 1,278.1 / 678.6입니다. 현재 절대값은 일치하지 않습니다. 이번 E01은 기존 재구성 모형 안에서 가정의 영향을 분리한 S-class 실험입니다.')

page('2. E03: 두 도매가격을 독립적으로 바꾼 결과')
figure('wholesale_region.png',490,327)
p(f'사전 규칙에 따라 3×3 시범실험의 9개 통과를 확인한 뒤 {size}×{size} 격자를 실행했습니다. 가로축은 PT, 세로축은 MoD의 이용 간선당 도매단가입니다. 가격 0은 무상 용량 제공이라는 진단 조건이고 실무적 협상값이 아닙니다.')
p('초록은 기존 두 운영자 수익 변화·신규 플랫폼 이익·총 이용자 효용 변화가 각각 +0.001보다 큰 점입니다. 하나라도 -0.001 미만이면 비개선, 경계 부호는 미확정입니다. 실패점은 회색으로 구분합니다. 모든 기준은 같은 A 미도입 상태를 사용합니다.')
p('점선은 공통 도매가격 경로입니다. 사각형 색은 계산한 격자점의 판정이며 사이 구간의 연속적 경계나 보간된 균형을 증명하지 않습니다. x 표시는 적어도 한 OD의 평균 기대효용이 10^-8 이상 감소한 점입니다.')
p('도매가격은 운영자 간 매출 배분만 기계적으로 바꾸지 않습니다. 플랫폼의 비용·OD 요금·수요·운영자 소매가격과 교통 상태가 함께 달라집니다. 검증된 점을 협상 결과나 보편적 상생 임계값으로 해석하지 않습니다.')

page('3. 경제적 상호작용과 분배')
figure('economic_surfaces.png',497,360)
p('위 패널은 미도입 대비 MoD/PT 수익 변화, 플랫폼 이익 및 총 이용자 효용 변화입니다. 빈 칸은 검증 실패점입니다. 흰 실선은 가능한 경우 0 수준의 보간 등고선, 점선은 공통 도매가격 경로입니다. 보간선은 추가로 검증한 해가 아닙니다.')
selected=[]
for cm,cp in [(0,1.5),(1.5,0),(1.5,1.5),(3,3)]:
    r=next((r for r in grid if float(r['c_mod'])==cm and float(r['c_pt'])==cp),None)
    if r and r['status']=='PASS': selected.append([f'({cm:g}, {cp:g})',f(r['delta_profit_mod']),f(r['delta_profit_pt']),f(r['profit_maas']),r['harmed_od_count']])
table(['(MoD, PT)','ΔMoD 수익','ΔPT 수익','플랫폼 이익','손해 OD 수'],selected,[117,95,95,95,95])
p('한 운영자의 도매단가만 낮으면 해당 운영자가 손해를 보는 반면 상대 운영자는 이득을 볼 수 있습니다. 따라서 공통 가격 대각선의 상생 결과만으로 비대칭 계약을 일반화할 수 없습니다. 총량 상생점에서도 OD별 편익은 다를 수 있으며, OD 평균이 모든 개인의 편익을 대표하지도 않습니다.')

page('4. 가격·수단 선택 반응과 조건부 해석')
figure('price_share_surfaces.png',497,360)
p('소매가격과 수단분담도 각 도매점에서 새로 계산한 균형 후보의 결과입니다. 기존 총 OD 수요 1,000은 고정되어 있으므로 추가 MaaS/PT 이용은 총 통행량 유발이 아니라 대안 간 재배분입니다.')
p('PT 수익은 소매수입 + 도매수입, 플랫폼 이익은 OD 판매수입 - 두 운영자에 대한 도매지출입니다. 내부 도매이전은 사회후생에 한 번 더 더하지 않습니다. 원시 값과 차이 값은 all_results.csv에 함께 저장했습니다.')
p('첫 PT 접근과 실제 PT 유료 간선 통과량은 다릅니다. 기존 V5의 접근 간선 기반 지표를 유지했으며 이를 원문 표의 지표와 동일하다고 확정하지 않았습니다. 최초 대기, 접근 용량 공유, 선택 척도 및 작은 네트워크 구성에 대한 미확정 항목도 그대로 남습니다.')
p('정부나 보조금은 모형에 없습니다. 따라서 공공예산 포함 Pareto 판정은 NOT_APPLICABLE입니다. 이번 결과를 공공 PT의 최적 정책이나 보조금 효과로 확대하지 않습니다.')

page('5. 검증 결과와 계산 방법')
vals=[]
for record in json.loads((OUT/'manifest.json').read_text()).values():
    path=ROOT/record['path']/'validation.json'
    if path.exists(): vals.append(json.loads(path.read_text()))
table(['검증 항목','관측 최대값 / 상태'],[
['6개 기준선 / 원본 봉인','기존 검증 3종 통과; 3,957 파일 불변'],
['실행 판정',str(summary['status_counts'])],
['자연 잔차 / 척도 조정 잔차',f'{max(v["vi_residual"] for v in vals):.3g} / {max(v["scaled_residual"] for v in vals):.3g}'],
['수요 보존 / 수익 회계',f'{max(v["conservation_error"] for v in vals):.3g} / {max(v["accounting_error"] for v in vals):.3g}'],
['고정 시간 가격 이탈의 최대 이득',f'{max(v["deviation_gain_fixed_t"] for v in vals):.3g}'],
['혼잡 재균형 후 가격 이탈','미수행: 별도 M02 비용·게임 해석 필요'],
['M01 최소 인터페이스','18개 유한값·실행가능성·첫 단계 수식 검사']],[260,237])
p('V5의 ROOT_AUX를 공통 사용했고 원본 Model.evaluate/project는 수정하지 않았습니다. 여유 용량 자원의 10^-6 미만 잔여 지체를 정확한 경계로 투영하는 공통 수치 보정을 적용했습니다. 원시 솔버 해는 raw_solver에 보존하고, 보정 후 요금·잔차·감사를 다시 계산했습니다. 실패나 미수렴은 삭제하지 않습니다.')
bad=[r for r in grid if r['status']!='PASS']
if bad:
    table(['실패 도매점 (MoD, PT)','상태','자연 / scaled 잔차'],[[f'({r["c_mod"]}, {r["c_pt"]})',r['status'],f'{float(r.get("vi_residual") or "nan"):.3g} / {float(r.get("scaled_residual") or "nan"):.3g}'] for r in bad],[190,120,187])
    p('실패점은 함수평가 한도 max_nfev=100에 도달한 뒤에도 VI 잔차와 용량 상보성 조건을 만족하지 못했습니다. 원시 해와 실패 검증을 보존했습니다. 위 최댓값은 실패 후보까지 포함합니다. 수치 Jacobian 내부의 추가 H 호출은 이 한도와 별도입니다. 미수렴은 균형 부재나 복수 균형의 증거가 아닙니다.')
p('원래 변수의 자연 잔차와 flow 좌표의 scaled residual을 구분합니다. 운영자 이탈은 시간·경쟁 가격·플랫폼 요금을 고정한 grid+국소검색이고, MaaS 요금은 현 선택 특수화의 조건부 최적해로 확인했습니다. 2개 OD의 요금 및 운영자 가격 미분도 유한차분과 비교했습니다. 이것은 전역 Nash 증명이 아닙니다.')
p('M01은 PG, 고정 EG, 선탐색 EG를 동일한 evaluate/project 및 원래 변수 잔차로 호출하는 최소 인터페이스입니다. 2네트워크×3초기값×3방법의 2단계 동작 검사는 성능 벤치마크가 아닙니다. 수렴률·속도 우열과 비단조 VI의 전역 수렴을 주장하지 않습니다.')
p('CPU 시간, H/PUMCM 호출 수, H 평가시간, 솔버·전체 wall-clock, 50 ms 간격 프로세스 RSS를 기록했습니다. RSS에는 인터프리터와 이전 할당이 포함되고 관측 사이 순간 피크를 놓칠 수 있습니다. 스레드 1을 요청했으며 이번 E03은 작은 네트워크만 대상으로 합니다.')
p('중단 후 재개된 점의 실행시간은 해당 실행 구간 기준입니다. 이전 구간은 체크포인트 이벤트로 남겼으며 이 값을 무중단 성능 비교에 사용하지 않았습니다.')

page('6. 무엇을 확인했고, 무엇이 남았는가')
p('What was tested: V5의 불변 기준선과 3종 기존 검증; 작은 네트워크의 A/B/C 재균형 대조; 두 도매단가의 독립 격자; 회계·보존·비용 항등식·VI·고정 시간 단독가격 변경; M01 최소 인터페이스입니다.')
failed=[r for r in rows if r['status']!='PASS']
p('What failed: '+(f'{len(failed)}개 계산이 통과하지 못했습니다. manifest의 실패 유형 및 각 failure/validation 파일을 확인해야 하며 경제적 결론에서 제외했습니다.' if failed else '최종 경제 실험에서 검증 실패로 남은 점은 없습니다. 초기 실행의 psutil 누락은 Windows 기본 메모리 API로 해결했고, 집계 컬럼 중복 오류도 수정했습니다. 이 개발 오류 기록은 보존했습니다.')+' 본격적인 M01 수렴 벤치마크와 혼잡 재균형 가격 이탈 검사는 수행하지 않았습니다.')
p('What remains unidentified: 초기 PT 대기, 접근 수요·용량 공유, 섭동함수와 척도, 원문 모드·환승 지표의 정의입니다. node/node 및 Shannon 척도 1은 재구성 기준선이지 저자의 설정을 확정한 것이 아닙니다.')
p('What this supports: 이 재구성 모형에서 플랫폼 진입과 환승 마찰 감소는 구별되는 편익 경로이며, 상생은 PT/MoD 계약단가 조합 및 편익 집계 수준에 조건부입니다. 비대칭 계약과 분배효과를 논문 리뷰의 구체적 질문으로 제시할 수 있습니다.')
p('What this does not support: 원문 수치 재현 성공, 실제 스위스 MaaS 수요 예측, 정부·가입·구독 정책의 검증, 모든 개인의 Pareto 개선, 유일·전역 Nash 균형, EG의 성능 우위 또는 대도시 확장성 증명은 아닙니다.')
p('후속 우선순위: 먼저 M01을 동일 잔차·H 호출 예산의 실제 벤치마크로 완성하고 M02의 다중 초기값/이탈 해석을 강화합니다. 이어 E04의 평균 동일 이질성은 집단별 흐름·공유 혼잡·민감도 회귀검증부터 설계합니다. E05 가입가능성, E06 공공재정, E09 구독상품은 별도 새 모형으로 남깁니다.')
p('재실행: research_setup.py → research_protocol.py → research_experiments.py E01 → E03_pilot → (게이트 통과 시) E03_coarse → research_solvers.py → research_analysis.py → verify_research_v6.py → research_report.py. 최종 결과는 results/research_v6/, 재개 지침은 notes/RESUME_RESEARCH.md입니다. 이 폴더의 원본 지시서 TXT/MD는 변경하지 않았습니다.')
p('자료: 사용자 MaaS_Codex_v6.md 및 Prompt TXT(2026-11-05 기준 지시서), V5 source-to-code 원장, 제공 원 논문 Sections 2-5 / Tables 2-3 / Appendix A, DOI 10.1016/j.trc.2026.105703. 지시서의 실험 아이디어를 원저자의 모형 설정으로 취급하지 않았습니다.')
def footer(c,d):
    c.setFont('Malgun',8); c.setStrokeColor(colors.HexColor('#bdd0d5')); c.line(45,39,550,39); c.drawString(45,25,'MaaS research handoff · finalized 2026-11-08 · reconstruction counterfactual'); c.drawRightString(550,25,str(d.page))
doc=SimpleDocTemplate(str(PDF/'MaaS_Research_Handoff_20261106_ko.pdf'),pagesize=(595.28,841.89),leftMargin=49,rightMargin=49,topMargin=38,bottomMargin=53,title='MaaS research handoff experiments 2026-11-06')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(ROOT/'RESEARCH_V6_RESULTS.md').write_text('# MaaS 연구 실험 결과\n\n'+'\n'.join(md),encoding='utf-8')
print('Report generated:',summary['total'],'runs;',len(improving),'aggregate improving grid points;',len(harms),'with harmed OD averages')
