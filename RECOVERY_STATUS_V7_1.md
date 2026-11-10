# v7.1 복구·공유 상태 — 2026-11-10

이번 작업은 사용자의 최신 지시에 따라 장시간 알고리즘 계산을 재시작하지 않고 저장 결과 복구, 가벼운 추가 진단, 보고서 작성, 검증 및 공유 패키징을 수행합니다. 원래 v5/v6 결과는 변경하지 않습니다.

| 단계 | 저장 결과와 판정 | 이번 복구에서 한 일 |
|---|---|---|
| November research_v6 | 76개 시도, 75 PASS, 1 FAILED_VI | 원본 해시 보존 확인 |
| R00 / G00–G02 | 21개 원문 쟁점 및 기준선 재평가 완료 | 보고서에 근거와 재구현 차이 명시 |
| E01-P | 정적 실제 상품/복제/보정 진단 완료 | 재균형·인과분해로 표현하지 않음 |
| E02-PT | 물리 PT 이용·접근·판매채널 분리 완료 | 집계·보고서 생성 |
| E03-D/V | 기존 유효 63점, L1 31점, L2 14점; 비용 형태 진단 | 기존 실패 보존 |
| E03 추가 경계 | 9/9 PASS, 이미 계산됨 | 저장 결과 복구; 추가 최적화 없음 |
| M01 PG/EG | 27/27 시도 완료, 0/27 수렴기준 통과 | 재실행 없음; 모든 실패·호출 로그 보존 |
| M01 경계 진단 | 독립 스칼라 15행 + 저장 상태 잔차 성분 | 이번에 가벼운 추가 진단 실행 |
| M02 | 12개 가격 변화/교통 반응 probe 완료 | 저장 결과 검토·정리 |
| M03 JOINT_AUX | PASS, H 1490회, 기존 실행 약 7.51초 | 저장 결과 재평가 |
| M03 NESTED_SAME_VI | INTERRUPTED_NOT_COMPLETED, 최종 상태·유효 체크포인트 없음 | 재시작하지 않음; 성능 비교 NOT_COMPARABLE |
| Sioux 알고리즘 벤치마크 / Phase C | NOT_RUN | 현재 작업 범위에서 실행하지 않음 |

M01 실패는 이 독립 재구현과 정해진 예산의 결과이며, 저자 EG의 실패나 이론 반증이 아닙니다. 원문의 전체 MoD 접근수요 집계와 코드의 노드별 집계 차이, 시간 역 BPR 수치 표현, 종료지표 차이를 분리해 보아야 합니다. 반복 변화가 0인데 자연 잔차가 남는 경계 진단도 별도로 보존했습니다.

## 파일과 실행 안내

- `results/research_v7_1/Detailed_Review_KR.md`, `Technical_Report_EN.md`: 복구 보고서.
- `results/research_v7_1/validation.json`: 무결성/보고 검증. 모든 수치실험의 PASS 선언이 아님.
- `results/research_v7_1/m01_runs/`: 시도별 설정·상태·체크포인트·실패 기록. 전체 per-H 로그는 로컬 복구 ZIP에 보존.
- `results/research_v7_1/m03_runs/NESTED_SAME_VI/interruption.json`: 미완료 근거.
- `cloud_replay.py`, `CLOUD_README.md`, `requirements-cloud.txt`: 독립 클라우드용 경량 실행 경로.
- `EXPORT_FILE_INVENTORY.csv`, `SHARED_MANIFEST.json`: 공유본 파일 목록·원본/공유본 해시. 텍스트의 로컬 사용자 경로와 BOM만 정규화한 경우 표시.
- `distribution/MaaS_v7_1_Small_Cloud.zip`: 공개 브랜치에서 다운로드 가능한 실행 ZIP.

기존 로컬 브랜치는 `research-v7-1-critical-validation`입니다. 공개 GitHub에는 같은 이름의 정제된 스냅샷 브랜치를 새 Git 이력으로 게시합니다. 따라서 원본 로컬 커밋과 공개 커밋 SHA는 다릅니다. 과거 요청문·원문·기타 비공개 파일이 기존 Git 이력을 따라 게시되지 않도록 분리한 것입니다. 원본 이력은 로컬 bundle에 유지합니다. 최종 공개 SHA와 ZIP SHA256은 별도 전달 기록으로 확인합니다.

## 재개할 때

현재 새 장기 계산은 실행하지 않습니다. 먼저 프로세스와 저장 파일을 확인하고 중복 실행을 피하십시오. M01 27개 완료 시도는 재실행 대상이 아닙니다. NESTED_SAME_VI는 연산 중간 상태가 저장되지 않았으므로 정확히 그 반복부터 이어갈 수 없습니다. 이후 장기 계산을 명시적으로 승인한 경우에만 빈 실행 로그와 interruption.json을 별도 시도 기록으로 보존한 뒤 새로운 실행 디렉터리에서 시작하고, 공통 최종 잔차 기준을 통과해야 비교하십시오. 중단된 시도를 완료/PASS로 간주하면 안 됩니다.

클라우드에서는 우선 `python cloud_replay.py`로 대표 A/B/C 참조해와 실패 상태를 재평가하십시오. 이 명령은 solver를 실행하지 않습니다. 기존 Windows campaign의 전체 verifier는 원본 자료·태그·체크포인트를 전제로 하므로 부분 공유본의 기본 검증 경로가 아닙니다. 상세 범위는 CLOUD_README.md를 참조하십시오.
