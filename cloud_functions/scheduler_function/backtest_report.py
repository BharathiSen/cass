"""
Offline backtesting report generator for scheduler policy strategies.

Usage examples:
  python backtest_report.py --input ./historical_decisions.json
  python backtest_report.py --limit 500 --output-dir ./reports
  python backtest_report.py --input ./historical_decisions.json --strategies balanced,carbon_first,cost_first
"""

import argparse
import copy
import csv
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from firestore_logger import FirestoreLogger
from main import DEFAULT_REGION_COST_USD, DEFAULT_REGION_LATENCY_MS, can_deploy
from policy_engine import PolicyEngine


def _load_config(config_path: str) -> Dict:
    with open(config_path, "r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _read_input_records(input_path: str) -> List[Dict]:
    with open(input_path, "r", encoding="utf-8") as file_obj:
        payload = json.load(file_obj)

    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]

    if isinstance(payload, dict):
        for key in ("decisions", "records", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]

    return []


def _parse_timestamp(raw_value: Optional[str]) -> datetime:
    if not raw_value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(raw_value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def _extract_actual_region(record: Dict) -> Optional[str]:
    return record.get("selected_region") or record.get("region")


def _extract_region_samples(record: Dict) -> Dict[str, float]:
    samples = record.get("region_samples")
    if isinstance(samples, dict) and samples:
        normalized: Dict[str, float] = {}
        for region, value in samples.items():
            try:
                normalized[str(region)] = float(value)
            except (TypeError, ValueError):
                continue
        return normalized
    return {}


def _resolve_carbon_24h(record: Dict, region_samples: Dict[str, float]) -> Dict[str, float]:
    """Build a per-region carbon baseline for scoring from each record."""
    candidates = record.get("all_candidates")
    if isinstance(candidates, list) and candidates:
        carbon_24h: Dict[str, float] = {}
        for row in candidates:
            if not isinstance(row, dict):
                continue
            region = row.get("zone")
            value = row.get("carbon_24h")
            try:
                if region:
                    carbon_24h[str(region)] = float(value)
            except (TypeError, ValueError):
                continue
        if carbon_24h:
            return carbon_24h
    return dict(region_samples)


def _update_state_after_switch(state: Dict, selected_region: str, selected_score: float, ts: str) -> None:
    state["selected_region"] = selected_region
    state["last_deployed_region"] = selected_region
    state["selected_score"] = selected_score
    state["last_switch_timestamp"] = ts
    state["last_deployment_time"] = ts


def run_backtest(
    records: List[Dict],
    base_config: Dict,
    strategies: List[str],
    simulate_stability: bool,
) -> Dict:
    scheduler_cfg = base_config.get("scheduler", {})
    latency_map = scheduler_cfg.get("region_latency_ms", DEFAULT_REGION_LATENCY_MS)
    cost_map = scheduler_cfg.get("region_cost_usd", DEFAULT_REGION_COST_USD)

    clean_records = []
    for row in records:
        samples = _extract_region_samples(row)
        if not samples:
            continue
        clean_records.append(row)

    clean_records.sort(key=lambda row: _parse_timestamp(row.get("timestamp")))

    strategy_outputs: List[Dict] = []

    for strategy in strategies:
        cfg = copy.deepcopy(base_config)
        cfg.setdefault("scheduler", {}).setdefault("policy", {})["strategy_mode"] = strategy

        engine = PolicyEngine(cfg, can_deploy_fn=can_deploy)
        simulated_state: Dict = {}

        per_decision: List[Dict] = []
        matches = 0
        total_actual_carbon = 0.0
        total_predicted_carbon = 0.0
        actual_count = 0

        for row in clean_records:
            ts = row.get("timestamp") or datetime.now(timezone.utc).isoformat()
            actual_region = _extract_actual_region(row)
            samples = _extract_region_samples(row)
            carbon_24h = _resolve_carbon_24h(row, samples)

            ranked = engine.score_regions(
                region_carbon_24h=carbon_24h,
                latest_region_samples=samples,
                latency_map=latency_map,
                cost_map=cost_map,
            )
            if not ranked:
                continue

            if simulate_stability:
                stable = engine.select_stable_region(ranked, scheduler_state=simulated_state)
                selected = stable["selected"]
                switch_reason = stable["decision_reason"]
                switch_applied = bool(stable["switched"])
                if switch_applied:
                    _update_state_after_switch(simulated_state, selected["zone"], selected["score"], ts)
            else:
                selected = ranked[0]
                switch_reason = "best_ranked_no_stability_simulation"
                switch_applied = True

            predicted_region = selected["zone"]
            predicted_carbon = float(samples.get(predicted_region, selected.get("carbon_latest", 0.0)))

            actual_carbon = None
            if actual_region:
                try:
                    actual_carbon = float(samples.get(actual_region, row.get("carbon_intensity")))
                except (TypeError, ValueError):
                    actual_carbon = None

            carbon_delta = None
            if actual_carbon is not None:
                carbon_delta = round(actual_carbon - predicted_carbon, 3)
                total_actual_carbon += actual_carbon
                actual_count += 1
                if predicted_region == actual_region:
                    matches += 1

            total_predicted_carbon += predicted_carbon

            per_decision.append(
                {
                    "timestamp": ts,
                    "actual_region": actual_region,
                    "predicted_region": predicted_region,
                    "predicted_rank": int(selected.get("rank", 1)),
                    "predicted_score": float(selected.get("score", 0.0)),
                    "actual_carbon": actual_carbon,
                    "predicted_carbon": round(predicted_carbon, 3),
                    "carbon_delta_gco2_per_kwh": carbon_delta,
                    "switch_applied": switch_applied,
                    "switch_reason": switch_reason,
                }
            )

        total = len(per_decision)
        matched_total = matches if total > 0 else 0
        avg_predicted = round(total_predicted_carbon / total, 3) if total > 0 else None
        avg_actual = round(total_actual_carbon / actual_count, 3) if actual_count > 0 else None

        strategy_outputs.append(
            {
                "strategy_mode": strategy,
                "records_analyzed": total,
                "matched_historical_region": matched_total,
                "match_rate_percent": round((matched_total / total) * 100, 2) if total > 0 else 0.0,
                "avg_predicted_carbon_gco2_per_kwh": avg_predicted,
                "avg_actual_carbon_gco2_per_kwh": avg_actual,
                "estimated_avg_carbon_delta_gco2_per_kwh": round(avg_actual - avg_predicted, 3)
                if (avg_actual is not None and avg_predicted is not None)
                else None,
                "per_decision": per_decision,
            }
        )

    ranked_summary = sorted(
        strategy_outputs,
        key=lambda item: (
            item["avg_predicted_carbon_gco2_per_kwh"] is None,
            item["avg_predicted_carbon_gco2_per_kwh"] if item["avg_predicted_carbon_gco2_per_kwh"] is not None else 1e9,
        ),
    )

    best_strategy = ranked_summary[0]["strategy_mode"] if ranked_summary else None

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulate_stability": simulate_stability,
        "input_records": len(records),
        "usable_records": len(clean_records),
        "strategies_tested": strategies,
        "best_strategy_by_avg_predicted_carbon": best_strategy,
        "strategy_summaries": [
            {
                "strategy_mode": item["strategy_mode"],
                "records_analyzed": item["records_analyzed"],
                "match_rate_percent": item["match_rate_percent"],
                "avg_predicted_carbon_gco2_per_kwh": item["avg_predicted_carbon_gco2_per_kwh"],
                "avg_actual_carbon_gco2_per_kwh": item["avg_actual_carbon_gco2_per_kwh"],
                "estimated_avg_carbon_delta_gco2_per_kwh": item["estimated_avg_carbon_delta_gco2_per_kwh"],
            }
            for item in ranked_summary
        ],
        "strategy_details": ranked_summary,
    }


def _write_json_report(output_dir: str, report: Dict) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "backtest_report.json")
    with open(path, "w", encoding="utf-8") as file_obj:
        json.dump(report, file_obj, indent=2)
    return path


def _write_csv_report(output_dir: str, report: Dict) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "backtest_report.csv")
    with open(path, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "strategy_mode",
                "timestamp",
                "actual_region",
                "predicted_region",
                "predicted_rank",
                "predicted_score",
                "actual_carbon",
                "predicted_carbon",
                "carbon_delta_gco2_per_kwh",
                "switch_applied",
                "switch_reason",
            ],
        )
        writer.writeheader()
        for strategy in report.get("strategy_details", []):
            mode = strategy.get("strategy_mode")
            for row in strategy.get("per_decision", []):
                writer.writerow(
                    {
                        "strategy_mode": mode,
                        "timestamp": row.get("timestamp"),
                        "actual_region": row.get("actual_region"),
                        "predicted_region": row.get("predicted_region"),
                        "predicted_rank": row.get("predicted_rank"),
                        "predicted_score": row.get("predicted_score"),
                        "actual_carbon": row.get("actual_carbon"),
                        "predicted_carbon": row.get("predicted_carbon"),
                        "carbon_delta_gco2_per_kwh": row.get("carbon_delta_gco2_per_kwh"),
                        "switch_applied": row.get("switch_applied"),
                        "switch_reason": row.get("switch_reason"),
                    }
                )
    return path


def _parse_strategies(raw_strategies: str) -> List[str]:
    tokens = [token.strip().lower().replace("-", "_") for token in raw_strategies.split(",") if token.strip()]
    valid = set(PolicyEngine.STRATEGY_PROFILES.keys())
    filtered = [token for token in tokens if token in valid]
    return filtered if filtered else ["balanced"]


def _fetch_records(config: Dict, limit: int) -> List[Dict]:
    logger = FirestoreLogger(config)
    return logger.fetch_recent_decisions(limit=limit)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate offline policy backtesting reports")
    parser.add_argument("--config", default="config.json", help="Path to scheduler config")
    parser.add_argument("--input", default="", help="Path to historical decisions JSON file")
    parser.add_argument("--limit", type=int, default=0, help="Records to fetch from Firestore when --input is not provided")
    parser.add_argument("--strategies", default="", help="Comma-separated strategy modes")
    parser.add_argument("--output-dir", default="", help="Directory for generated reports")
    parser.add_argument("--disable-stability", action="store_true", help="Disable lock/hysteresis simulation")
    args = parser.parse_args()

    config = _load_config(args.config)
    backtest_cfg = config.get("scheduler", {}).get("backtesting", {})

    configured_strategies = backtest_cfg.get("default_strategies", ["balanced", "carbon_first", "cost_first", "stability_first"])
    strategies_raw = args.strategies or ",".join(configured_strategies)
    strategies = _parse_strategies(strategies_raw)

    default_limit = int(backtest_cfg.get("default_limit", 500))
    resolved_limit = max(int(args.limit), 1) if args.limit > 0 else max(default_limit, 1)

    output_dir = args.output_dir or str(backtest_cfg.get("default_report_dir", "reports/backtest"))

    config_simulate_stability = bool(backtest_cfg.get("simulate_stability", True))
    simulate_stability = config_simulate_stability and not args.disable_stability

    if args.input:
        records = _read_input_records(args.input)
        source = args.input
    else:
        records = _fetch_records(config, limit=resolved_limit)
        source = f"firestore_recent:{resolved_limit}"

    report = run_backtest(
        records=records,
        base_config=config,
        strategies=strategies,
        simulate_stability=simulate_stability,
    )
    report["data_source"] = source

    json_path = _write_json_report(output_dir, report)
    csv_path = _write_csv_report(output_dir, report)

    print("=" * 75)
    print("CASS-Lite Backtest Report")
    print("=" * 75)
    print(f"Data source: {source}")
    print(f"Input records: {report['input_records']}")
    print(f"Usable records: {report['usable_records']}")
    print(f"Best strategy: {report['best_strategy_by_avg_predicted_carbon']}")
    print(f"JSON report: {json_path}")
    print(f"CSV report: {csv_path}")
    print("=" * 75)

    for summary in report.get("strategy_summaries", []):
        print(
            f"- {summary['strategy_mode']}: "
            f"avg_predicted={summary['avg_predicted_carbon_gco2_per_kwh']} gCO2/kWh, "
            f"match_rate={summary['match_rate_percent']}%"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
