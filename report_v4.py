"""Generate a reproducible Korean report and complete accepted/rejected manifest."""
import run
import json,csv,datetime,html
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

out=Path('output/pdf'); out.mkdir(parents=True,exist_ok=True)
rows=[]
for folder in sorted(Path('results/v4').iterdir()):
    if not folder.is_dir() or folder.name.startswith('test_'): continue
    r=json.loads((folder/'metrics.json').read_text()) if (folder/'metrics.json').exists() else {}
    a=json.loads((folder/'audit.json').read_text()) if (folder/'audit.json').exists() else {}
    passed=bool(r.get('converged') and a.get('all_retail_deviation_gains_below_1e-4') and abs(r.get('accounting_error',1))<1e-6 and r.get('flow_conservation_error',1)<1e-6)
    status='PASS' if passed else 'REJECTED_DEVIATION' if r.get('converged') and a else 'NOT_CONVERGED' if r else 'ERROR' if (folder/'error.txt').exists() else 'INCOMPLETE'
    entry=dict(run=folder.name,status=status,**r,audit=a)
    if r:
        S=r['share_maas']/100; total=432720 if r['network']=='sioux' else 1000
        bound=r['config']['mode_theta']*total*S/max(1-S,1e-15)
        entry['jensen_profit_lower_bound']=bound
    rows.append(entry)
Path('results/v4/manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
keys=['run','status','share_drive','share_maas','share_non_mod','share_non_pt','share_maas_mod','share_maas_pt','price_mod','price_pt','profit_mod','profit_pt','profit_maas','traveler_welfare','transfer_flow','intermodal_transfers','pt_pt_transfers','pt_access_flow','pt_total_capacity','natural_residual','scaled_residual','accounting_error','jensen_profit_lower_bound']
with Path('results/v4/summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,keys,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
data={r['run']:r for r in rows}
def get(tag): return data.get(tag,{})
def val(r,k,fmt='.2f'): return format(r[k],fmt) if k in r else '-'
def ok(r): return r.get('status')=='PASS'
counts={s:sum(r['status']==s for r in rows) for s in ['PASS','REJECTED_DEVIATION','NOT_CONVERGED','ERROR','INCOMPLETE']}
targets={('sioux',False):dict(share_drive=48.5,share_maas=0,price_mod=.81,price_pt=3.65,profit_mod=221756,profit_pt=337286,profit_maas=0,traveler_welfare=-9934124),('sioux',True):dict(share_drive=40.3,share_maas=39.5,price_mod=1.04,price_pt=2.42,profit_mod=376355,profit_pt=375636,profit_maas=5658,traveler_welfare=-8545142),('small',False):dict(share_drive=23.7,share_maas=0,price_mod=.63,price_pt=1.38,profit_mod=1176.7,profit_pt=664.1,profit_maas=0,traveler_welfare=-19514),('small',True):dict(share_drive=22.5,share_maas=18.9,price_mod=.66,price_pt=1.44,profit_mod=1278.1,profit_pt=678.6,profit_maas=232.9,traveler_welfare=-19287)}
with Path('results/v4/paper_errors.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.writer(f); writer.writerow(['run','status','metric','paper','reconstruction','difference','relative_error_percent','share_error_percentage_points'])
    for r in rows:
        if 'network' not in r: continue
        for key,target in targets[r['network'],r['maas']].items():
            delta=r[key]-target
            writer.writerow([r['run'],r['status'],key,target,r[key],delta,100*delta/abs(target) if target else '',delta if key.startswith('share_') else ''])

plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,2,figsize=(9,6),layout='constrained')
for family,color in [('common','#1f77b4'),('mode','#db6500')]:
    for ax,key,suffix,target in zip(axs.flat,['share_drive','share_maas','profit_maas','profit_pt'],['without','with','with','with'],[48.5,39.5,5658,375636]):
        candidates=[get(f'sioux_{family}_{s:g}_{suffix}') for s in [1,.5,.2,.1,.05,.03,.01]]
        candidates[0]=get('sioux_node_node_total0_'+suffix)
        for j,r in enumerate(candidates):
            if key not in r: continue
            x=r['config']['mode_theta']; ax.scatter(x,r[key],color=color,marker='o' if ok(r) else 'x',s=40,label=family if j==0 else None)
        ax.axhline(target,color='black',ls='--',lw=1); ax.set_xscale('log'); ax.set_xlabel('Mode scale (log axis)'); ax.set_title(key.replace('_',' '))
axs[0,0].legend(); fig.suptitle('Sioux Falls node-access sensitivities: circles pass audit, crosses do not\nDashed lines: published targets; common changes both scales, mode changes root only',fontsize=10)
fig.savefig(out/'v4_scale_diagnostics.png',dpi=180); plt.close(fig)

pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
styles=getSampleStyleSheet()
for k in ['Title','Heading1','Heading2','BodyText','Normal']:
    styles[k].fontName='MalgunBold' if k in ['Title','Heading1','Heading2'] else 'Malgun'
styles['BodyText'].fontSize=9.2; styles['BodyText'].leading=15; styles['BodyText'].spaceAfter=8; styles['BodyText'].wordWrap='CJK'
styles['Title'].fontSize=21; styles['Title'].leading=29
styles['Heading2'].fontSize=13; styles['Heading2'].leading=19
cell=ParagraphStyle('cell',fontName='Malgun',fontSize=7.5,leading=11,wordWrap='CJK')
story=[]; md=[]
def p(t): story.append(Paragraph(html.escape(t),styles['BodyText'])); md.append(t+'\n')
def h(t): story.append(Paragraph(html.escape(t),styles['Heading2'])); md.append('## '+t+'\n')
def table(lines,widths):
    t=Table([[Paragraph(html.escape(str(x)),cell) for x in row] for row in lines],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe7f4')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.whitesmoke,colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([t,Spacer(1,9)]); md.extend(['| '+' | '.join(str(x) for x in row)+' |' for row in [lines[0],['---']*len(lines[0]),*lines[1:]]]); md.append('\n')
def page(): story.append(PageBreak())

story.append(Paragraph('MaaS 재현 정밀화 보고서',styles['Title'])); md.append('# MaaS 재현 정밀화 보고서\n')
p('Revision 4 | 2026년 10월 22일 | PUME 후속 논문 및 외부 검토 의견 반영')
h('결론: 구현과 검증은 진전했지만, 논문 표의 정량 재현은 미완료')
p('공개된 수식과 네트워크로 동작하는 모델을 확장하고, 접근 용량 해석과 효용 척도를 분리하여 시험했다. 현재 시험한 설정 가운데 논문의 점유율, 가격, 운영자 수익, MaaS 이익을 함께 설명하는 설정을 확인하지 못했다. 특정 지표가 비슷한 결과를 원 논문의 재현으로 선택하지 않았다.')
p(f"이번 실행 기록은 {len(rows)}개이며, 수치·가격 변경·회계 검증을 모두 통과한 결과 {counts['PASS']}개, 가격 변경 검증 탈락 {counts['REJECTED_DEVIATION']}개, 미수렴 {counts['NOT_CONVERGED']}개, 오류 {counts['ERROR']}개, 미완료 {counts['INCOMPLETE']}개다. 추가 시작점도 별도 실행으로 센다. PASS는 유한한 가격 탐색을 포함한 수치 검증 통과이며 전역 Nash 균형의 수학적 증명이 아니다.")
h('이전 버전에서 개선한 사항')
p('MoD와 PT의 접근 용량을 독립적으로 지정하고, PT 정류장별·노선/정류장별 용량과 총용량 고정 실험을 추가했다. 모드 선택 척도와 경로 선택 척도를 분리했다. 최초 탑승수단, PT 간 환승, 수단 간 환승, 소매수익·도매지급액·플랫폼 수입을 별도로 기록한다. 작은 척도의 지수 언더플로를 줄이는 정확한 Bellman 변환과 반복별 복구 파일을 추가했다.')
h('후속 논문이 확인해 주는 것과 남은 불확실성')
p('Yao & Zhang의 PUME 후속 논문(arXiv:2607.09568v1, 2026-07-10) 6.1절 식 (37)-(40)은 상태별 척도를 가진 Shannon/log-sum-exp 모형을 제시한다. 따라서 모드와 경로 척도를 구분하는 실험은 이론적으로 가능한 특수형이다. 그러나 부록 E.1의 logit 척도 1, NRL 척도 [0.5,2]는 별도 실험의 설정이며 MaaS 논문의 설정으로 확정할 수 없다. sparsemax는 원 논문의 매끄러움 가정과 동일하게 취급하지 않았다.')
p('원저자에게 연락하지 않았다. 공개 제목·저자 검색과 HOMES/저자 공개 논문 목록을 다시 확인했으나, 확인한 자료에서 원 MaaS 구현을 찾지 못했다. 공개 코드가 없다는 단정은 아니다. 제공받은 원문 PDF는 로컬 보관하고 GitHub에는 재현 코드와 자체 결과만 저장한다.')
page()
h('1. 접근 용량 실험: 구조 해석이 결과를 바꾸는 크기')
p('본문 5.1.1절은 MoD 접근시간이 전체 접근 수요와 차량 수에 의해 결정된다고 설명한다. 따라서 aggregate MoD가 본문에 더 직접적인 해석이다. node MoD는 비교용 대안이다. PT 용량은 각 자원에 주는 경우와 모든 자원에 나누어 총합을 유지하는 경우를 구분했다. 용량을 나누지 않으면 네트워크 전체 PT 접근 용량 자체가 커진다.')
scope=[('node/node','sioux_node_node_total0'),('aggregate/node','sioux_aggregate_node_total0'),('aggregate/line-node','sioux_aggregate_line_node_total0'),('node/node, 총량고정','sioux_node_node_total1')]
lines=[['MoD/PT 범위','운전 전→후 (%)','MaaS (%)','PT 수익 전→후','MaaS 이익','검증 전/후']]
lines.append(['논문','48.5 → 40.3','39.5','337,286 → 375,636','5,658','대상값'])
for label,tag in scope:
    b,a=get(tag+'_without'),get(tag+'_with')
    lines.append([label,f"{val(b,'share_drive')} → {val(a,'share_drive')}",val(a,'share_maas'),f"{val(b,'profit_pt',',.0f')} → {val(a,'profit_pt',',.0f')}",val(a,'profit_maas',',.0f'),f"{b.get('status','-')}/{a.get('status','-')}"])
table(lines,[100,85,50,110,65,95])
p('MoD aggregate/PT node에서 운전 비중은 62.17% → 59.50%다. 단순히 PT만 정류장별로 바꾸어도 논문의 결과는 복원되지 않는다. 총 PT 용량을 고정한 node/node는 도입 전 운전 비중 49.42%로 목표에 가깝지만 MaaS 점유율은 6.60%에 그친다. 용량 가정만으로 모든 차이를 설명할 수 없다.')
h('수익 회계 및 시장점유율 정의')
p('운영자 수익 = 비MaaS 소매수익 + MaaS 도매지급액, 플랫폼 이익 = MaaS 요금수입 - 도매지급액이다. 전체 이익의 합은 소매수익과 MaaS 요금수입의 합과 같아야 한다. 구현은 이 항등식을 매번 검사한다. MoD/PT 시장점유율은 최초 탑승수단으로 분류하고 두 비율의 합이 해당 서비스군 점유율이 되는지 검사한다. 논문의 세부 비율도 동일한 분류인지 확인되지 않아 직접 일치한다고 주장하지 않는다.')
p('PT 간 환승과 MoD-PT 환승은 별도로 집계한다. 논문 표의 transfer flow(0.87, 189.14)는 수요 합계와의 단위·집계 관계가 확인되지 않았다. 임의로 100 또는 1,000으로 나누어 맞추지 않았다.')
page()
h('2. 효용 척도: 수학적 필요조건과 실험')
p('Shannon 모드 선택에서 독립적인 OD 요금 p가 내부 최적값이면 p-C = mu/(1-s)다. C는 조건부 도매비용, s는 OD별 MaaS 선택확률이다. 전체 이익 Pi = mu × 합(q s/(1-s))이다. s/(1-s)의 볼록성과 Jensen 부등식으로 Pi ≥ mu Q S/(1-S)를 얻는다. Q는 전체 수요, S는 전체 MaaS 점유율이다.')
p('논문의 Q=432,720, S=0.395, Pi=5,658을 대입하면 mu ≤ 0.02003이어야 한다. 이는 단순한 Pi ≥ mu Q S에서 얻는 0.0331보다 강한 필요조건이다. 원 논문이 같은 Shannon 모형, 같은 금액 단위, 같은 수요 정의, 내부 OD 요금을 사용한다는 조건 아래 성립한다. 다른 perturbation 함수나 활성 요금제약이면 결론은 달라진다. 이 값은 추정된 정답이 아니다.')
story.append(Image(str(out/'v4_scale_diagnostics.png'),width=505,height=337))
p('공통 척도 감소와 모드 척도만 감소하는 실험을 분리했다. 원은 검증 통과, x는 미수렴 또는 일방적 가격 변경 이익이 남는 결과다. 점을 연결하지 않았으며, x를 균형으로 해석하지 않는다. 낮은 척도로 MaaS 이익 하나를 줄이는 것이 운전 비중과 운영자 수익의 동시 재현을 보장하지 않는다.')
page()
h('3. 작은 네트워크와 교차 검증')
p('작은 네트워크에도 같은 분해를 적용했다. 두 네트워크에 서로 다른 척도를 임의로 맞춰 넣는 것은 원 설정의 복원이 아니므로, 이번 결과는 설정 민감도와 반증 자료로 구분한다. PT 노선 (5,6) 포함 여부는 본문의 노드 수/그림과 부록 표 사이에 차이가 있다. 기본은 부록 기반 노선으로 두고, figure_pt는 노드 5에서 PT 노선을 끝낸다. figure_pt_reverse23은 그림에서 양방향으로 보이는 도로 (2,3)의 역방향도 추가한 별도 가설이다.')
lines=[['실험','운전 전/후','MaaS 비중','MoD 수익','PT 수익','MaaS 이익']]
lines.append(['논문','23.7 / 22.5','18.9','1,278.1','678.6','232.9'])
for label,tag in [('node/node','small_node_node_total0'),('aggregate/node, 재시작','small_aggregate_node_total0_warm'),('aggregate/line-node, 재시작','small_aggregate_line_node_total0_warm'),('node/node, 총량고정','small_node_node_total1')]:
    b,a=get(tag+'_without'),get(tag+'_with')
    lines.append([label+(' [검증 미통과]' if not(ok(a) and ok(b)) else ''),f"{val(b,'share_drive')} / {val(a,'share_drive')}",val(a,'share_maas'),val(a,'profit_mod',',.1f'),val(a,'profit_pt',',.1f'),val(a,'profit_maas',',.1f')])
table(lines,[145,85,65,70,70,70])
h('그림 기반 구조 변형')
lines=[['변형 (MoD 접근 범위)','MaaS 비중','플랫폼 이익','운전 비중','도입 후 검증']]
for scope in ['node','aggregate']:
    for variant in ['figure_pt','figure_pt_reverse23']:
        r=get(f'small_{scope}_{variant}_with')
        lines.append([f'{variant} ({scope})',val(r,'share_maas'),val(r,'profit_maas',',.2f'),val(r,'share_drive'),r.get('status','-')])
table(lines,[215,65,75,65,85])
h('거짓 수렴을 분리한 사례')
p('Sioux Falls 공통 척도 0.2의 최초 MaaS 도입 전 해는 자연 잔차를 만족했지만 PT 가격 변경으로 약 20,738의 추가 이익이 가능해 제외했다. 높은 추가 이익을 주는 가격에서 다시 시작한 deviation_start 실험도 별도 보존한다. 매우 높은 PT 가격과 거의 0인 수요로 정체된 작은 네트워크 결과도 성공 처리하지 않았다. 기존에 검증된 해에서 시작한 추가 실험은 별도 폴더로 남겼다.')
h('검증의 범위')
p('자연 잔차는 논문과 같은 gamma=1e-4, epsilon=1e-6 기준이다. 재현 해는 원 Algorithm 1의 반복 궤적 대신 동일하게 구성한 VI에 대한 보조 root/least-squares 해법을 사용한다. 수렴 속도나 GPU 성능은 재현하지 않았다. 가격 변경 검사는 다른 리더의 시간·가격을 고정한 상태에서 각 운영자의 가격을 0~10 격자와 20,50,100,200 및 국소 최적화로 탐색한다. 유한 탐색이므로 전역 최적성 증명은 아니다.')
page()
h('4. 수치 안정성, 복구 및 재실행')
v=json.loads(Path('results/v4/validation.json').read_text())
table([['검사','결과'],['기존/잠재함수 변환 결과 차이',f"small {v['small_potential_equivalence']:.2e}, Sioux {v['sioux_potential_equivalence']:.2e}"],['강제 중단 후 해의 최대 차이',f"{v['interrupted_restart_state_error']:.2e}"],['초기 상태 가격 미분 검사','척도 0.01까지 정규화 오차 4.5e-9 미만'],['회계 항등식 및 종착 흐름','통과 결과는 각각 절대오차 1e-6 미만']],[235,270])
p('변환은 최단경로 거리 D를 수치적 잠재함수로 사용하여 exp((-c-D_next+D)/theta)를 푼다. 모든 허용 경로를 유지하므로 최단경로만 선택하는 근사는 아니다. 서로 다른 모드/경로 척도는 상태별 척도의 제한된 형태이며, 모든 노드의 임의 척도를 구현한 것은 아니다.')
p('각 허용 반복마다 상태·전체 설정·반복수·잔차·시각·PID·Git commit을 results/v4/<실험>/checkpoints에 저장한다. Windows 파일 잠금 오류를 피하기 위해 완료된 세대 파일을 덮어쓰지 않는다. 새 파일은 임시 파일에서 원자적으로 이름을 바꾼다. 재시작은 optimizer 내부 메모리 전체가 아니라 마지막 상태에서 해법을 재구성한다.')
p('재실행 명령: python batch_v4.py scope / common / mode 및 python repair_v4.py. 프로젝트에 scipy/numpy 등 의존성이 있어야 한다. 완료된 metrics.json은 건너뛰며, 미완료 실험은 마지막 checkpoint를 읽는다. 실패한 결과를 다시 시도할 때에는 원래 결과를 보존하고 새 이름을 사용한다. python report_v4.py는 모든 실행의 manifest.json, summary.csv 및 이 보고서를 다시 생성한다.')
p('요청에 따라 즉시 작업을 시작하고 기존 01:20 예약을 중지했으며, 06:30 복구 예약은 07:40으로 변경했다. 이번 82개 기본 실험과 7개 추가 실험을 모두 마친 뒤 복구 예약도 중지했다. 중단된 실행은 없지만 재시작 파일과 지침은 보존했다. 정량 재현의 미해결 문제와 실행 중단은 구분한다. 사용 한도를 우회하거나 크레딧을 구매하지 않았다.')
h('5. 다음 단계와 판단 기준')
p('우선 현재 기준에서 검증을 통과한 설정과 탈락한 설정을 보존한다. 다음 우선순위는 공개 원문/부록의 모드 진입 상태, 서비스별 비용 단위, 효용 정규화, 환승 집계 정의를 구조별로 대조하는 일이다. 일반 상태별 perturbation이나 다른 매끄러운 생성함수는 명시적 가설로 추가하고, MaaS 없는 가격·점유율부터 검증한 뒤 MaaS를 넣어야 한다. 작은 척도에서 root만 반복하는 대신 다중 시작점과 가격 전역 탐색을 결합하는 것도 필요하다.')
p('통과 기준은 양 네트워크에서 도입 전후의 점유율·가격·각 운영자 수익·플랫폼 이익·후생을 함께 비교하는 것이다. 후생 하나나 운전 비중 하나가 비슷하다는 이유로 성공을 선언하지 않는다. 원저자 문의는 작업의 선행조건으로 두지 않는다.')
h('자료와 산출물')
p('원 연구: Yao, Ma & Zhang (2026), TRC 188, 105703, DOI 10.1016/j.trc.2026.105703. PUMCM: TRISTAN XII 2025 확장초록. 후속 연구: https://arxiv.org/abs/2607.09568 . 네트워크: https://github.com/bstabler/TransportationNetworks/tree/master/SiouxFalls . 추가 해석의 근거는 notes/FOLLOWUP_LEDGER.md에 기록했다.')
p('전체 실행·탈락 이유: results/v4/manifest.json, summary.csv. 논문 대비 지표별 오차는 paper_errors.csv에 있다. OD별 확률·요금·도매비용 및 자원별 흐름은 통과한 실험 폴더의 CSV에 있다. 원 설정, 시작점, 반복 기록, 실패 로그를 함께 보존한다. GitHub: https://github.com/oscar15625/Project-files/tree/maas-reproduction-2026-10-21 .')
def footer(canvas,doc):
    canvas.setFont('Malgun',8); canvas.setFillColor(colors.grey); canvas.drawString(45,25,'MaaS 재현 정밀화 | Revision 4 | 독립 재현, 정량 일치 미완료'); canvas.drawRightString(A4[0]-45,25,str(doc.page))
SimpleDocTemplate(str(out/'MaaS_reproduction_v4_ko.pdf'),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=42,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
Path('REPRODUCTION_V4.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps(counts)); print(out/'MaaS_reproduction_v4_ko.pdf')
