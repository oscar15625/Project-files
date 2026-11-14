# M01 원인 분석·개선 VI 솔버와 클라우드 v8 검증

2026-11-14. 원래 M01 27개 실패, 첫 개선안 12개 시도, 기존 M03 및 클라우드 원본을 보존했습니다.

## 결과

개선안 SCORE의 원래 모형 통과는 **9/9**, 클라우드 nested choice 통과는 **9/10**입니다. 여기서 통과는 보조좌표뿐 아니라 원래 시간변수 자연 잔차 <1e-6, 전체 스케일 잔차 <1e-6, 물리·회계·가격 이탈·미분 검사를 모두 만족하는 경우입니다. 실제 결과는 아래 원시 표와 함께 읽어야 합니다. 이전 첫 개선안 12개 중 저장된 PASS는 2개이며 실패를 삭제하지 않았습니다.

## 왜 M01이 실패했는가

1. **역 BPR 자유류 경계:** 공급이 (t/t0-1)^(1/4)에 비례하여 자유류 부근에서 미분이 매우 커집니다. 기존 블록 진단에서는 PG와 고정 EG의 잔차가 주로 교통 변수에 남았습니다. 미사용 자원의 잔차도 고정 EG에 남지만 전체 원인은 아닙니다. 작은 반복 차이는 자연 잔차 통과를 보장하지 않습니다.
2. **공통 step 축소:** 기존 adaptive EG의 대표 실행은 초기 1e-4를 3.90625e-7까지 줄였습니다. 해당 구현은 step을 다시 키우지 않습니다. 교통과 가격 변수의 서로 다른 척도 때문에 가격 조정도 느려질 수 있습니다. 이는 관측된 구현의 현상이지 모든 adaptive EG의 한계가 아닙니다.
3. **희박 수요의 기울기 소실:** 첫 flow-coordinate root 개선안은 일부 B/C에서 MaaS 요금을 높여 수요가 거의 0인 후보를 만들었습니다. 요금 기울기 q*P*score가 작아도 실제 이윤 최적반응은 아닐 수 있습니다. 한 B 후보는 잔차가 작았지만 MaaS 이윤 증가 여지가 약 121.84여서 FAILED_DEVIATION으로 탈락했습니다. 따라서 잔차만으로 경제적 수용을 판단하면 안 됩니다.
4. **optimizer 종료와 VI 수용의 차이:** 첫 A 1.05 후보는 optimizer의 gtol 조건을 만족했지만 full-scaled 잔차 1.395e-6으로 탈락했습니다. 새 시험은 gtol만 1e-14로 강화했으며 원래 VI 수용기준은 완화하지 않았습니다.

## 개선 알고리즘과 같은 모형의 의미

- 혼잡 시간 대신 x=(f/capacity)에 대응하는 유량 보조좌표를 사용하고 t=t0*(1+0.15*x^4)로 복원합니다.
- 모든 목적지 그래프에 존재하지 않는 자원만 정확히 자유류 하한으로 제거합니다.
- MaaS 요금 조건은 고객 1명당 score=(fare-cost)*kappa-1로 계산합니다. 원래 H_f=q*P_MaaS*score 항등식을 12개 일반·극단 요금 상태에서 검증했습니다. 양의 확률에서는 같은 부호·영점 조건이므로 수요·효용·이윤 목적을 바꾸지 않습니다.
- Nested에서는 w=P_MaaS/(P_non+P_MaaS), kappa=[P_drive*w+(1-w)/lambda]/mu입니다. lambda=1이면 (1-P_MaaS)/mu로 환원됩니다. **MNL의 Wright-omega 요금 공식을 Nested에 적용하지 않았습니다.**
- 모든 가격은 명시적 미지수이며, 같은 고정시간 편미분 조건을 유지합니다. 보조 최소제곱의 trust-region으로 이 투영 잔차의 영점을 찾습니다. 이는 개선된 VI root 솔버이며 원문의 EG 궤적을 재현한 것이 아닙니다.
- 수치 Jacobian 평가까지 실제 H 호출 예산 8,000회에 포함했습니다. 최종 검증 호출은 분리 기록했습니다. SciPy의 max_nfev 자체는 수치 Jacobian 호출을 포함하지 않으므로 별도 계수가 필요합니다. [SciPy 공식 문서](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).

## 원래 모형: cold-start와 대조시험

기존 M01과 같은 Model.initial()*0.95/1/1.05에서 시작했으며 균형 상태로 warm-start하지 않았습니다. DEMAND는 같은 gtol·좌표·제약에서 요금 잔차를 기존 q로만 나누는 대조군입니다. 첫 개선안과 달리 이 대조군은 강화된 gtol을 공유하므로 요금 정규화 효과를 더 직접적으로 확인할 수 있습니다.

| Case | Start | Fare scaling | Status | Strict time PASS | Solver H | Full scaled |
|---|---:|---|---|---|---:|---:|
| A_no_maas | 0.95 | SCORE | PASS | True | 858 | 3.22e-14 |
| A_no_maas | 1.0 | SCORE | PASS | True | 2425 | 1.25e-11 |
| A_no_maas | 1.05 | SCORE | PASS | True | 2071 | 8.18e-12 |
| B_maas_no_transfer_advantage | 0.95 | SCORE | PASS | True | 840 | 6.52e-14 |
| B_maas_no_transfer_advantage | 1.0 | SCORE | PASS | True | 1765 | 1.41e-11 |
| B_maas_no_transfer_advantage | 1.05 | SCORE | PASS | True | 1808 | 1.55e-11 |
| C_maas_paper_advantage | 0.95 | SCORE | PASS | True | 1640 | 6.87e-14 |
| C_maas_paper_advantage | 1.0 | SCORE | PASS | True | 2437 | 7.38e-12 |
| C_maas_paper_advantage | 1.05 | SCORE | PASS | True | 2395 | 1.94e-13 |
| A_no_maas | 1.0 | DEMAND | PASS | True | 2425 | 1.25e-11 |
| B_maas_no_transfer_advantage | 1.0 | DEMAND | FAILED_VALIDATION | False | 1697 | 7.96e-10 |
| C_maas_paper_advantage | 1.0 | DEMAND | FAILED_VALIDATION | False | 6555 | 3.05e-01 |

기존 PG/EG는 각 20,000 H 한도였고 이번 root의 한도는 8,000입니다. 서로 다른 날짜의 시간이나 다른 예산을 엄밀한 알고리즘 순위로 주장하지 않습니다. 같은 수용기준을 통과했는지와 실제 H 호출수를 보고합니다. 이 작은 문제에서의 성공은 Sioux Falls나 전역 수렴 보장이 아닙니다.

## 클라우드 자료 검증

클라우드 원본 해시, 18개 단위·회귀·유한차분 검사, 10개 저장 상태와 원래 국소 가격변경 검사를 독립 재검증했습니다. 원본 입력 123개는 변경하지 않았습니다. lambda=1의 원래 MNL 회귀와 MaaS 없는 A의 lambda 불변성을 확인했습니다. 클라우드 계획의 M03 가격 차이 2.66e-9는 소매가격만의 값이며, MaaS 요금 포함 최대 차이는 4.01e-8입니다. 서술 범위 수정 사항이고 모형 결함은 아닙니다.

클라우드의 valid_pass는 원래 유한 국소 가격 이탈 검사 기준입니다. 새 솔버 후보에는 더 넓은 가격 격자와 구간별 정련, 미분 차분 검사를 추가했습니다. 이것도 전역 Nash 증명은 아닙니다. Nested choice는 상품 선택 상관성, M03 Nested는 교통균형 중첩 알고리즘으로 별개입니다.

## 같은 Nested choice 모형에 적용

클라우드와 같은 B/C, lambda=1/.85/.75/.65/.55 및 같은 도매단가·접근집계·망을 사용했습니다. 클라우드 저장해로 초기화하지 않고 같은 cold-start를 사용했습니다.

| Case | Start | Fare scaling | Status | Strict time PASS | Solver H | Full scaled |
|---|---:|---|---|---|---:|---:|
| B_lambda0.55 | 1.0 | SCORE | PASS | True | 1976 | 1.50e-11 |
| B_lambda0.65 | 1.0 | SCORE | FAILED_VALIDATION | False | 8000 | 2.34e-03 |
| B_lambda0.75 | 1.0 | SCORE | PASS | True | 1934 | 1.82e-11 |
| B_lambda0.85 | 1.0 | SCORE | PASS | True | 1765 | 1.44e-11 |
| B_lambda1.00 | 1.0 | SCORE | PASS | True | 1765 | 1.41e-11 |
| C_lambda0.55 | 1.0 | SCORE | PASS | True | 3447 | 7.42e-12 |
| C_lambda0.65 | 1.0 | SCORE | PASS | True | 3363 | 3.04e-12 |
| C_lambda0.75 | 1.0 | SCORE | PASS | True | 2731 | 9.49e-12 |
| C_lambda0.85 | 1.0 | SCORE | PASS | True | 2398 | 2.44e-12 |
| C_lambda1.00 | 1.0 | SCORE | PASS | True | 2437 | 7.37e-12 |

### 초기값 민감도: 실패를 보존한 추가 시험

B lambda=0.65의 기본 초기값은 8,000 H에서 자연 잔차 약 6.24e-4, 용량 상보성 약 166.81로 실패했습니다. 가격 검사 통과만으로 유효한 해로 분류하지 않았습니다. 같은 솔버·허용오차·H 예산으로 0.95/1.05 두 초기값을 추가 등록했습니다. 재시도 통과는 2/2이며, 적어도 한 개 유효해를 얻은 클라우드 조건은 10/10입니다. 단일 시작점의 무조건적 수렴을 주장하지 않습니다.

| Case | Start | Fare scaling | Status | Strict time PASS | Solver H | Full scaled |
|---|---:|---|---|---|---:|---:|
| B_lambda0.65 | 0.95 | SCORE | PASS | True | 1347 | 6.36e-14 |
| B_lambda0.65 | 1.05 | SCORE | PASS | True | 1977 | 1.24e-11 |

| Accepted case/start | Platform profit | Welfare gain vs A | Harmed ODs | Max price diff vs cloud |
|---|---:|---:|---:|---:|
| B_lambda0.55 / 1.0 | 44.4024 | 26.9381 | 1 | 1.64e-11 |
| B_lambda0.65 / 0.95 | 60.3635 | 41.7660 | 1 | 1.91e-11 |
| B_lambda0.65 / 1.05 | 60.3635 | 41.7660 | 1 | 1.91e-11 |
| B_lambda0.75 / 1.0 | 77.4160 | 57.9264 | 0 | 5.49e-10 |
| B_lambda0.85 / 1.0 | 95.3187 | 75.3207 | 0 | 2.24e-11 |
| B_lambda1.00 / 1.0 | 123.3973 | 103.2870 | 0 | 2.82e-11 |
| C_lambda0.55 / 1.0 | 64.2866 | 83.9473 | 0 | 3.78e-09 |
| C_lambda0.65 / 1.0 | 82.6079 | 101.5011 | 0 | 5.55e-10 |
| C_lambda0.75 / 1.0 | 101.7745 | 120.6276 | 0 | 1.15e-09 |
| C_lambda0.85 / 1.0 | 121.5836 | 140.9217 | 0 | 1.43e-11 |
| C_lambda1.00 / 1.0 | 152.2156 | 172.8628 | 0 | 1.50e-11 |

이 비교는 동일한 경제문제의 독립 해 검증입니다. OD 평균 손실과 집계 개선은 구분하며, 경험적 lambda 추정·개인 Pareto 개선 또는 원 논문 정밀 수치 재현으로 주장하지 않습니다.

## 다음 범위와 재개

우선 이 구현을 Small의 검증된 기준 솔버 후보로 사용할 수 있는지 위 통과 개수로 판단합니다. 이후에는 보다 넓은 초기값·도매계약·네트워크 크기에서 별도 등록 시험을 해야 합니다. EG 자체의 개선을 원하면 유량좌표 및 블록 스케일의 투영 반복을 별도 구현해 동일한 잔차·H 예산으로 비교해야 합니다. 이번 root 결과를 EG 개선으로 부르면 안 됩니다.

`runs/*/COMPLETE.json`이 있는 시도는 재실행하지 않습니다. 중단 시 `checkpoint.npy`는 가장 좋은 좌표 후보이며 SciPy 내부 상태 전체를 복원하는 파일은 아닙니다. 실패는 보존하고 별도 시도로 재개하십시오. 코드·입력 해시·로그와 모든 판정은 이 폴더 및 별도 백업에 있습니다.
