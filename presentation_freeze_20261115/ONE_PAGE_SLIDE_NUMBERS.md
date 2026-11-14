# 발표용 핵심 수치 — 독립 Small 재구현

| 근거 | 검증된 수치 | 단위·해석 |
|---|---|---|
| E01 | B−A 103.29; C−B 69.58; C−A 172.86 | 총 기대효용, 모형 단위 |
| 정적 Placebo | 독립복제 +575.18; 분할보정 0; 실제 B상품 +113.56 | A 상태 고정; 재균형 아님 |
| E03 | 64 중 63 PASS; 공동개선31; OD 비악화14; 공동개선이나 OD손실17 | 3 OD 평균; 개인 Pareto 아님 |
| Nested Choice B | λ1→.55 이익123.40→44.40; 후생증가103.29→26.94; 손실OD0→1 | 새로운 행동 반사실; λ 미추정 |
| M01 | 27 중 0 PASS | 시도별 solver H=20,000 |
| Root | 원모형9/9; Nested기본9/10; 재시작2/2; DEMAND1/3 | 총24 중21 STRICT PASS; 3실패 보존 |
| M03 | Joint/Nested PASS; H1,490/12,309 | 단일 warm-start, 세션 다름 |

PT 실제 이용통행/링크이용량 A,B,C: {"E01/A_no_maas": {"any_actual_pt_trips": 392.46447071039796, "pt_vehicle_link_traversals": 591.6084811467686}, "E01/B_maas_no_transfer_advantage": {"any_actual_pt_trips": 394.6636998303868, "pt_vehicle_link_traversals": 594.8824834172391}, "E01/C_maas_paper_advantage": {"any_actual_pt_trips": 408.0321356784415, "pt_vehicle_link_traversals": 593.6348587507024}}

수치 출처와 SHA: CLAIM_LEDGER.csv 및 baseline_audit/facts.json. 원 논문 Table 2/3의 수치가 아니다.
