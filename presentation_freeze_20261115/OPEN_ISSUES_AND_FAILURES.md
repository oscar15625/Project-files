# 실패·미해결 사항

- E03 원래 실패점: ['E03_coarse/mod_3.5_pt_1.5']. 이후 이웃 조건/재시작과 혼합하지 않음.
- M01 27회 모두 FAILED_NUMERICAL_CHECK. sources/m01_convergence_runs.csv와 states/의 최종 실패 상태 보존. 교통잔차 정체 및 역BPR 경계의 민감도는 보조 원인 진단이며 단일 원인 증명이 아니다.
- 최초 Root 12회 상태: [["A_no_maas_FLOW_TRF_0.95", "PASS"], ["A_no_maas_FLOW_TRF_1", "PASS"], ["A_no_maas_FLOW_TRF_1.05", "FAILED_NUMERICAL_CHECK"], ["A_no_maas_TIME_TRF_1", "FAILED_NUMERICAL_CHECK"], ["B_maas_no_transfer_advantage_FLOW_TRF_0.95", "FAILED_DEVIATION"], ["B_maas_no_transfer_advantage_FLOW_TRF_1", "FAILED_DEVIATION"], ["B_maas_no_transfer_advantage_FLOW_TRF_1.05", "FAILED_NUMERICAL_CHECK"], ["B_maas_no_transfer_advantage_TIME_TRF_1", "FAILED_NUMERICAL_CHECK"], ["C_maas_paper_advantage_FLOW_TRF_0.95", "FAILED_DEVIATION"], ["C_maas_paper_advantage_FLOW_TRF_1", "FAILED_NUMERICAL_CHECK"], ["C_maas_paper_advantage_FLOW_TRF_1.05", "FAILED_NUMERICAL_CHECK"], ["C_maas_paper_advantage_TIME_TRF_1", "FAILED_NUMERICAL_CHECK"]]. 낮은 잔차에도 가격이탈 이익이 큰 후보 및 원시간 잔차 실패를 보존했다.
- 최신 Root 실패3개: [["B_lambda0.65_SCORE_1", "FAILED_VALIDATION"], ["B_maas_no_transfer_advantage_DEMAND_1", "FAILED_VALIDATION"], ["C_maas_paper_advantage_DEMAND_1", "FAILED_VALIDATION"]]. Bλ=.65 기본 시작점의 실패는 .95와1.05 재시작 성공으로 삭제하지 않음.
- M03 기존 Nested 중단은 sources/m03_original_interruption.json에 보존. 후속 attempt2 PASS는 별도 결과이다.
- 가격이탈과 유한차분의 기존 상세 검증은 아카이브로 보존하며 본 closeout은 최적화기를 다시 돌리지 않았다. 저장 경제량·잔차 및 18개 커널 검사는 재실행했다.
- 원문/재구현 MoD 접근용량 차이, 일반 PUMCM 대 Shannon, 개별 후생 및 실증 가입선택은 미해결이다.
- E05는 신규 집단모형을 구현/검증하지 않았으므로 E05_NOT_RUN_DESIGN_ONLY. 실패한 계산이 있거나 검사를 통과했다는 뜻이 아니다.
