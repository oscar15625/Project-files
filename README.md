# Project-files

## travel diary -> time-space 모델 입력 변환

`survey_time_space_model.py`는 목적통행 기준 설문 CSV를 읽어 아래 3개 산출물을 생성합니다.

- `trip_table.csv`: 목적통행 단위 TT/Tin/Tout + activity + service + time-bin state
- `service_profiles.csv`: 서비스별/시간대별 3축 요약치(A_mb, Tin_mean, sigma_mb)
- `on_demand_scenarios.csv`: 일반화 on-demand 및 AV 시나리오 예시

### 실행 예시

```bash
python survey_time_space_model.py \
  --input-csv data/raw_travel_diary.csv \
  --output-dir outputs \
  --encoding cp949 \
  --bin-minutes 30
```

### 매핑 파일(선택)

교통수단/통행목적 코드가 코드북과 다르면 JSON으로 덮어쓸 수 있습니다.

- `--mode-map-json`
- `--purpose-map-json`

예시 (`mode_map.json`):

```json
{
  "active": [1, 2],
  "road_transit": [3],
  "rail": [4],
  "private_road": [5],
  "on_demand_base": [6]
}
```
