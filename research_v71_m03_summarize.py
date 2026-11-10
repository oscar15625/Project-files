"""Validate and report M03 alone, without rerunning any solver or other experiment."""
from research_v71 import *
P=O/'m03_followup_20261110'
def main():
    joint=O/'m03_runs/JOINT_AUX';nested=P/'NESTED_SAME_VI_attempt2'
    assert read(nested/'launch.json')['status']=='FINISHED'
    rows=[];states=[]
    for p in [joint,nested]:
        r=read(p/'metrics.json');m=Model(**r['config']);y=np.load(p/'state.npy');x=np.load(p/'coordinates.npy');current,d=metrics(m,y,x)
        err=max(abs(current[k]-r[k]) for k in current);assert err<1e-6
        valid=read(p/'validation.json')
        if r['status']=='PASS':assert d['natural_aux']<1e-6 and r['full_scaled']<1e-6 and valid['status']=='PASS'
        rows.append(dict(method=r['method'],status=r['status'],natural_aux=d['natural_aux'],natural_direct=d['natural_direct'],full_scaled=r['full_scaled'],total_h_calls=r['total_h_calls'],total_pumcm_calls=r['total_pumcm_calls'],seconds=r['seconds'],cpu_seconds=r['cpu_seconds'],inner_solves=r['inner_solves'],inner_failures=r['inner_failures'],profit_mod=r['profit_mod'],profit_pt=r['profit_pt'],profit_maas=r['profit_maas'],traveler_welfare=r['traveler_welfare'],max_metric_replay_error=err,source=p.relative_to(ROOT).as_posix()))
        states.append(y)
    assert read(joint/'metrics.json')['config']==read(nested/'metrics.json')['config']
    outcsv('m03_followup_20261110/comparison.csv',rows)
    a,b=rows;both=all(r['status']=='PASS' for r in rows)
    price_gap=float(np.max(np.abs(states[0][m.nt:]-states[1][m.nt:])))
    profit_gap=max(abs(a[k]-b[k]) for k in ['profit_mod','profit_pt','profit_maas'])
    summary=dict(status='COMPARABLE_SMALL_PROTOTYPE' if both else 'NOT_COMPARABLE',joint_reused=True,other_experiments_rerun=False,original_nested_interruption_preserved=True,price_max_absolute_difference=price_gap,operator_profit_max_absolute_difference=profit_gap,h_call_ratio_nested_over_joint=b['total_h_calls']/a['total_h_calls'] if both else None,wall_ratio_descriptive_only=b['seconds']/a['seconds'] if both else None,caveat='One small warm-start case, different execution sessions; timings include instrumentation and validation. No general efficiency ranking or paper-EG claim.',results=rows)
    write(P/'summary.json',summary)
    table='| 방법 | 판정 | 자연 잔차(보조좌표) | H 호출 | PUMCM 호출 | 시간(초) | 내부 solve | 내부 실패 |\n|---|---|---:|---:|---:|---:|---:|---:|\n'+'\n'.join(f"| {r['method']} | {r['status']} | {r['natural_aux']:.3g} | {r['total_h_calls']} | {r['total_pumcm_calls']} | {r['seconds']:.3f} | {r['inner_solves']} | {r['inner_failures']} |" for r in rows)
    report=f'''# M03 단독 후속 결과 — 2026-11-10

판정: **{summary['status']}**. 기존 Joint 해를 재사용하고 Nested만 별도 새 시도로 실행했습니다. M01, M02, E01–E03 및 v5/v6 실험은 재실행하지 않았습니다. 원래 중단 폴더와 이전 보고서는 보존했습니다.

{table}

두 해의 최대 가격 차이는 {price_gap:.6g}, MoD/PT/플랫폼 수익의 최대 차이는 {profit_gap:.6g}입니다. 저장 상태를 다시 평가해 지표 일치와 최종 잔차를 확인했습니다. PASS 여부는 solver 성공 플래그가 아니라 잔차·물리·회계·가격 이탈 검사를 따릅니다.

설정: Small network, 도매단가 (1.5,1.5), 같은 참조 교통 상태에서 모든 가격을 3% 높인 시작점. 기존 Nested의 inner max_nfev=100, outer max_nfev=50, outer diff_step=1e-4 및 허용오차를 유지했습니다. 새 실행은 경로와 진행 기록만 추가했으며 내부 초기값 재사용·허용오차 완화 등 계산 단축은 적용하지 않았습니다.

H 호출 비율(Nested/Joint): {summary['h_call_ratio_nested_over_joint']}. 시간 비율(서술적): {summary['wall_ratio_descriptive_only']}. 두 실행은 서로 다른 세션에서 수행했고 Nested에는 진행 저장을 추가했으므로 시간을 엄밀한 동시 조건 벤치마크로 해석하면 안 됩니다. 호출수에도 내부 수치 Jacobian과 최종 검증을 포함합니다. 둘 다 통과한 경우에만 이 한 개의 작은 warm-start 사례에 대한 비용 비교가 가능합니다. 대규모 우위, 일반적인 해법 순위 또는 논문 EG의 성능을 입증하는 결과가 아닙니다.

Nested는 가격 조건 평가마다 교통균형을 내부에서 풉니다. 가격 조건은 원래 고정시간 편미분을 유지하며, 사업자가 교통반응까지 전략적으로 고려하는 다른 게임으로 바꾸지 않았습니다.

원시 기록은 NESTED_SAME_VI_attempt2/ 아래에 있습니다. 마지막 내부해는 저장되지만 SciPy 외부 최적화 전체 상태의 재시작 체크포인트는 아닙니다. 중단 기록을 삭제하거나 기존 실패를 덮어쓰지 않았습니다.
'''
    (P/'M03_REPORT_KR.md').write_text(report,encoding='utf-8')
    (P/'M03_REPORT_EN.md').write_text('# M03-only follow-up\n\n'+json.dumps(summary,indent=2)+'\n\nThe prior joint result is reused, not rerun. Nested retains the original numerical protocol and same fixed-time partial price conditions. Both final states were replayed; no other experiment was executed. The old interrupted attempt is preserved. The comparison is restricted to this small warm-start prototype; sessions and logging overhead differ.\n',encoding='utf-8')
    write(P/'manifest.json',{p.relative_to(ROOT).as_posix():digest(p) for p in P.rglob('*') if p.is_file() and p.name!='manifest.json'})
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
