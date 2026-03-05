from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


LEG_MAX = 6

# 기본값은 예시이며, 실제 데이터 코드북에 맞게 --mode-map-json / --purpose-map-json으로 덮어쓸 수 있습니다.
DEFAULT_MODE_MAP = {
    "active": [1, 2],
    "road_transit": [3],
    "rail": [4],
    "private_road": [5],
    "on_demand_base": [6],
}

DEFAULT_PURPOSE_MAP = {
    "M": [1, 2, 3],  # mandatory
    "N": [4, 5, 6],  # maintenance
    "D": [7, 8, 9],  # discretionary
}


@dataclass(frozen=True)
class ParsedLeg:
    leg_index: int
    mode_code: int | None
    mode_group: str
    arrival_minute: int
    duration_minute: int



def _invert_group_mapping(group_to_codes: dict[str, list[int]]) -> dict[int, str]:
    code_to_group: dict[int, str] = {}
    for group, codes in group_to_codes.items():
        for code in codes:
            code_to_group[int(code)] = group
    return code_to_group



def parse_ampm_time_to_minute(ampm: Any, hour: Any, minute: Any) -> int | None:
    """설문의 (오전/오후, 시, 분) 컬럼을 0~1439 분으로 변환합니다."""
    if pd.isna(hour) or pd.isna(minute):
        return None

    h = int(hour)
    m = int(minute)
    ampm_text = str(ampm).strip()

    if ampm_text == "오후" and h < 12:
        h += 12
    elif ampm_text == "오전" and h == 12:
        h = 0

    return h * 60 + m



def _safe_int(value: Any) -> int | None:
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None



def parse_trip_row(
    row: pd.Series,
    mode_code_to_group: dict[int, str],
    purpose_code_to_activity: dict[int, str],
) -> dict[str, Any] | None:
    start_min = parse_ampm_time_to_minute(
        row.get("목적통행_출발시각(오전 오후)"),
        row.get("목적통행_출발시각(시)"),
        row.get("목적통행_출발시각(분)"),
    )
    if start_min is None:
        return None

    prev_arrival = start_min
    parsed_legs: list[ParsedLeg] = []

    for k in range(1, LEG_MAX + 1):
        mode_code = _safe_int(row.get(f"수단통행{k}_교통수단"))
        arrival_min = parse_ampm_time_to_minute(
            row.get(f"수단통행{k}_도착시각(오전 오후)"),
            row.get(f"수단통행{k}_도착시각(시)"),
            row.get(f"수단통행{k}_도착시각(분)"),
        )

        if arrival_min is None:
            continue

        # 자정 넘김 보정 (survey에서 다음날 시간이 기록될 수 있음)
        while arrival_min < prev_arrival:
            arrival_min += 24 * 60

        duration = arrival_min - prev_arrival
        if duration < 0:
            # 이론상 방어 코드
            continue

        mode_group = mode_code_to_group.get(mode_code, "unknown")
        parsed_legs.append(
            ParsedLeg(
                leg_index=k,
                mode_code=mode_code,
                mode_group=mode_group,
                arrival_minute=arrival_min,
                duration_minute=duration,
            )
        )
        prev_arrival = arrival_min

    if not parsed_legs:
        return None

    tt = prev_arrival - start_min
    if tt <= 0:
        return None

    tin = sum(leg.duration_minute for leg in parsed_legs if leg.mode_group != "active")
    tout = max(tt - tin, 0)

    in_vehicle_legs = [leg for leg in parsed_legs if leg.mode_group != "active"]
    if in_vehicle_legs:
        main_leg = max(in_vehicle_legs, key=lambda leg: leg.duration_minute)
    else:
        main_leg = max(parsed_legs, key=lambda leg: leg.duration_minute)

    purpose_code = _safe_int(row.get("통행목적"))
    activity = purpose_code_to_activity.get(purpose_code, "D")

    person_id = row.get("IDX")
    trip_order = _safe_int(row.get("목적통행_통행순서"))
    trip_id = f"{person_id}_{trip_order}" if trip_order is not None else str(person_id)

    return {
        "trip_id": trip_id,
        "person_id": person_id,
        "trip_order": trip_order,
        "origin_admin_code": row.get("목적통행_출발지_행정동코드"),
        "dest_admin_code": row.get("목적통행_도착지_행정동코드"),
        "start_min": start_min,
        "end_min": prev_arrival,
        "TT": tt,
        "Tin": tin,
        "Tout": tout,
        "main_mode_code": main_leg.mode_code,
        "service": main_leg.mode_group,
        "activity": activity,
        "purpose_code": purpose_code,
        "num_legs": len(parsed_legs),
        "num_in_vehicle_legs": len(in_vehicle_legs),
        "date_year": row.get("통행일자(년)"),
        "date_month": row.get("통행일자(월)"),
        "date_day": row.get("통행일자(일)"),
        "weekday": row.get("통행일자(요일)"),
    }



def build_trip_table(
    raw_df: pd.DataFrame,
    mode_map: dict[str, list[int]] | None = None,
    purpose_map: dict[str, list[int]] | None = None,
    bin_minutes: int = 30,
) -> pd.DataFrame:
    mode_map = mode_map or DEFAULT_MODE_MAP
    purpose_map = purpose_map or DEFAULT_PURPOSE_MAP

    mode_code_to_group = _invert_group_mapping(mode_map)
    purpose_code_to_activity = _invert_group_mapping(purpose_map)

    rows: list[dict[str, Any]] = []
    for _, row in raw_df.iterrows():
        parsed = parse_trip_row(row, mode_code_to_group, purpose_code_to_activity)
        if parsed is not None:
            rows.append(parsed)

    trips = pd.DataFrame(rows)
    if trips.empty:
        return trips

    trips["time_bin"] = (trips["start_min"] // bin_minutes).astype(int)

    # Survey-based state: time-bin 수요 압력
    bin_count = trips.groupby("time_bin")["trip_id"].size().rename("demand_bin")
    trips = trips.merge(bin_count, on="time_bin", how="left")

    service_bin_count = (
        trips.groupby(["time_bin", "service"])["trip_id"]
        .size()
        .rename("demand_service_bin")
        .reset_index()
    )
    trips = trips.merge(service_bin_count, on=["time_bin", "service"], how="left")

    return trips



def estimate_service_profiles(trips: pd.DataFrame) -> pd.DataFrame:
    """
    서비스별·시간대별 3축 요약치:
    - A_mb: out-of-vehicle time 평균
    - Tin_mean, TT_mean
    - sigma_mb: TT 표준편차 (uncertainty proxy)
    - p95_mb: TT 95분위
    """
    if trips.empty:
        return pd.DataFrame()

    def _p95(series: pd.Series) -> float:
        return float(np.quantile(series, 0.95))

    prof = (
        trips.groupby(["service", "time_bin"])
        .agg(
            n=("trip_id", "size"),
            A_mb=("Tout", "mean"),
            Tin_mean=("Tin", "mean"),
            TT_mean=("TT", "mean"),
            sigma_mb=("TT", "std"),
            p95_mb=("TT", _p95),
            demand_bin=("demand_bin", "mean"),
            demand_service_bin=("demand_service_bin", "mean"),
        )
        .reset_index()
    )

    prof["sigma_mb"] = prof["sigma_mb"].fillna(0.0)

    return prof



def build_on_demand_scenarios(
    profiles: pd.DataFrame,
    base_service: str = "on_demand_base",
) -> pd.DataFrame:
    """
    on-demand 일반화/AV 시나리오 파라미터를 생성합니다.
    base_service가 없으면 private_road를 대체 기준으로 사용합니다.
    """
    if profiles.empty:
        return pd.DataFrame()

    base = profiles[profiles["service"] == base_service].copy()
    if base.empty:
        base = profiles[profiles["service"] == "private_road"].copy()
    if base.empty:
        return pd.DataFrame()

    scenarios = {
        "OD_generic_conservative": {"dA": 2.0, "k_mult": 1.03, "sigma_mult": 1.05},
        "OD_generic_mid": {"dA": 4.0, "k_mult": 1.08, "sigma_mult": 1.12},
        "OD_generic_aggressive_pool": {"dA": 7.0, "k_mult": 1.15, "sigma_mult": 1.20},
        "OD_AV_mid": {"dA": -2.0, "k_mult": 0.98, "sigma_mult": 0.95},
    }

    out_frames: list[pd.DataFrame] = []
    for name, p in scenarios.items():
        s = base.copy()
        s["service"] = name
        s["A_mb"] = (s["A_mb"] + p["dA"]).clip(lower=0)
        s["Tin_mean"] = s["Tin_mean"] * p["k_mult"]
        s["TT_mean"] = s["A_mb"] + s["Tin_mean"]
        s["sigma_mb"] = s["sigma_mb"] * p["sigma_mult"]
        s["p95_mb"] = s["TT_mean"] + 1.64 * s["sigma_mb"]
        out_frames.append(s)

    return pd.concat(out_frames, ignore_index=True)



def _read_json_mapping(path: str | None) -> dict[str, list[int]] | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(k): [int(x) for x in v] for k, v in data.items()}



def run_pipeline(
    input_csv: Path,
    output_dir: Path,
    encoding: str,
    bin_minutes: int,
    mode_map_json: str | None,
    purpose_map_json: str | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_df = pd.read_csv(input_csv, encoding=encoding)

    mode_map = _read_json_mapping(mode_map_json)
    purpose_map = _read_json_mapping(purpose_map_json)

    trips = build_trip_table(
        raw_df,
        mode_map=mode_map,
        purpose_map=purpose_map,
        bin_minutes=bin_minutes,
    )
    profiles = estimate_service_profiles(trips)
    scenarios = build_on_demand_scenarios(profiles)

    trips.to_csv(output_dir / "trip_table.csv", index=False, encoding="utf-8-sig")
    profiles.to_csv(output_dir / "service_profiles.csv", index=False, encoding="utf-8-sig")
    scenarios.to_csv(output_dir / "on_demand_scenarios.csv", index=False, encoding="utf-8-sig")

    print(f"[DONE] trips={len(trips):,}, profiles={len(profiles):,}, scenarios={len(scenarios):,}")
    print(f"[OUT] {output_dir}")



def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Travel diary 목적통행 데이터를 time-space 모델 입력으로 변환합니다."
    )
    p.add_argument("--input-csv", required=True, type=Path, help="원본 설문 CSV 경로")
    p.add_argument("--output-dir", required=True, type=Path, help="출력 폴더")
    p.add_argument("--encoding", default="utf-8", help="CSV 인코딩 (예: cp949, utf-8)")
    p.add_argument("--bin-minutes", default=30, type=int, help="time bin 크기(분)")
    p.add_argument(
        "--mode-map-json",
        default=None,
        help='교통수단 그룹 매핑 JSON 파일 경로. 예: {"rail":[11,12],"road_transit":[7]}',
    )
    p.add_argument(
        "--purpose-map-json",
        default=None,
        help='통행목적→활동(M/N/D) 매핑 JSON 파일 경로. 예: {"M":[1,2],"N":[3],"D":[4,5]}',
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        encoding=args.encoding,
        bin_minutes=args.bin_minutes,
        mode_map_json=args.mode_map_json,
        purpose_map_json=args.purpose_map_json,
    )
