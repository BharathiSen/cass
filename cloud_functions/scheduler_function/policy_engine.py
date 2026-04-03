"""
Policy engine for region scoring and stable selection.

This module extracts strategy behavior from the scheduler so decision policy
is explicit, testable, and easy to evolve.
"""

from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


class PolicyEngine:
    """Strategy-driven policy engine for multi-objective region selection."""

    STRATEGY_PROFILES = {
        "balanced": {"carbon": 0.60, "latency": 0.25, "cost": 0.15},
        "carbon_first": {"carbon": 0.80, "latency": 0.10, "cost": 0.10},
        "cost_first": {"carbon": 0.30, "latency": 0.10, "cost": 0.60},
        "stability_first": {"carbon": 0.45, "latency": 0.45, "cost": 0.10},
    }

    def __init__(self, config: Dict, can_deploy_fn: Callable[[Optional[str], float], Dict]):
        self.config = config
        self.can_deploy = can_deploy_fn

    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """Normalize to [0, 1] where lower remains better."""
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)

    @staticmethod
    def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
        total = max(sum(max(float(v), 0.0) for v in weights.values()), 1e-9)
        return {k: max(float(v), 0.0) / total for k, v in weights.items()}

    def _get_strategy_settings(self) -> Dict:
        scheduler_cfg = self.config.get("scheduler", {})
        policy_cfg = scheduler_cfg.get("policy", {})
        stability_cfg = scheduler_cfg.get("stability", {})

        raw_mode = str(policy_cfg.get("strategy_mode", "balanced")).strip().lower().replace("-", "_")
        strategy_mode = raw_mode if raw_mode in self.STRATEGY_PROFILES else "balanced"

        profile_weights = dict(self.STRATEGY_PROFILES[strategy_mode])

        # Backward compatibility: keep existing stability.weights behavior.
        legacy_weights = stability_cfg.get("weights") if isinstance(stability_cfg.get("weights"), dict) else None
        custom_weights = policy_cfg.get("custom_weights") if isinstance(policy_cfg.get("custom_weights"), dict) else None

        if custom_weights:
            source = "custom_weights"
            resolved_weights = {
                "carbon": float(custom_weights.get("carbon", profile_weights["carbon"])),
                "latency": float(custom_weights.get("latency", profile_weights["latency"])),
                "cost": float(custom_weights.get("cost", profile_weights["cost"])),
            }
        elif legacy_weights:
            source = "legacy_stability_weights"
            resolved_weights = {
                "carbon": float(legacy_weights.get("carbon", profile_weights["carbon"])),
                "latency": float(legacy_weights.get("latency", profile_weights["latency"])),
                "cost": float(legacy_weights.get("cost", profile_weights["cost"])),
            }
        else:
            source = "strategy_profile"
            resolved_weights = profile_weights

        normalized = self._normalize_weights(resolved_weights)

        return {
            "strategy_mode": strategy_mode,
            "weights": normalized,
            "weights_source": source,
        }

    def score_regions(
        self,
        region_carbon_24h: Dict[str, float],
        latest_region_samples: Dict[str, float],
        latency_map: Dict[str, float],
        cost_map: Dict[str, float],
    ) -> List[Dict]:
        """Score regions using selected strategy profile across carbon/latency/cost."""
        settings = self._get_strategy_settings()
        weights = settings["weights"]

        candidates = []
        for zone, carbon_24h in region_carbon_24h.items():
            candidates.append(
                {
                    "zone": zone,
                    "carbon_24h": float(carbon_24h),
                    "carbon_latest": float(latest_region_samples.get(zone, carbon_24h)),
                    "latency_ms": float(latency_map.get(zone, 150)),
                    "cost_usd": float(cost_map.get(zone, 0.05)),
                }
            )

        all_carbon = [c["carbon_24h"] for c in candidates]
        all_latency = [c["latency_ms"] for c in candidates]
        all_cost = [c["cost_usd"] for c in candidates]

        for c in candidates:
            carbon_norm = self._normalize(c["carbon_24h"], min(all_carbon), max(all_carbon))
            latency_norm = self._normalize(c["latency_ms"], min(all_latency), max(all_latency))
            cost_norm = self._normalize(c["cost_usd"], min(all_cost), max(all_cost))

            c["score_breakdown"] = {
                "carbon": round(weights["carbon"] * carbon_norm, 4),
                "latency": round(weights["latency"] * latency_norm, 4),
                "cost": round(weights["cost"] * cost_norm, 4),
            }
            c["score"] = round(
                c["score_breakdown"]["carbon"]
                + c["score_breakdown"]["latency"]
                + c["score_breakdown"]["cost"],
                4,
            )

        ranked = sorted(candidates, key=lambda item: item["score"])
        for idx, candidate in enumerate(ranked):
            candidate["rank"] = idx + 1

        return ranked

    def select_stable_region(self, ranked_candidates: List[Dict], scheduler_state: Dict) -> Dict:
        """Apply strict deployment lock + hysteresis to avoid thrashing."""
        stability_cfg = self.config.get("scheduler", {}).get("stability", {})
        threshold_pct = float(stability_cfg.get("switch_threshold_percent", 12))
        hold_hours = float(stability_cfg.get("min_hold_hours", 24))

        settings = self._get_strategy_settings()
        strategy_mode = settings["strategy_mode"]
        weights = settings["weights"]

        best = ranked_candidates[0]
        previous_region = scheduler_state.get("last_deployed_region") or scheduler_state.get("selected_region")
        previous_score = scheduler_state.get("selected_score")
        last_switch_raw = scheduler_state.get("last_deployment_time") or scheduler_state.get("last_switch_timestamp")

        deploy_guard = self.can_deploy(last_switch_raw, hold_hours=hold_hours)
        deploy_allowed = bool(deploy_guard["allowed"])
        elapsed_hours = float(deploy_guard["hours_since_last"])

        decision_region = best["zone"]
        decision_reason = "initial_selection"
        switched = True
        previous_candidate = next((c for c in ranked_candidates if c["zone"] == previous_region), None)

        if previous_region and previous_candidate:
            decision_region = previous_region
            switched = False
            decision_reason = "hold_previous_region"

            prev_score = float(previous_score) if previous_score is not None else previous_candidate["score"]
            improvement_pct = ((prev_score - best["score"]) / max(prev_score, 1e-9)) * 100

            if best["zone"] == previous_region:
                decision_reason = "best_region_unchanged"
            elif not deploy_allowed:
                decision_reason = "deployment_locked_for_stability"
            elif improvement_pct < threshold_pct:
                decision_reason = "hysteresis_threshold_not_met"
            else:
                decision_region = best["zone"]
                switched = True
                decision_reason = "threshold_met_switch"

        selected_candidate = next((c for c in ranked_candidates if c["zone"] == decision_region), best)
        next_eligible_hours = float(deploy_guard["next_eligible_in_hours"])

        return {
            "selected": selected_candidate,
            "best": best,
            "ranked": ranked_candidates,
            "switched": switched,
            "decision_reason": decision_reason,
            "last_switch_hours_ago": round(elapsed_hours if elapsed_hours < 1e8 else 0.0, 2),
            "next_eligible_switch_in_hours": round(next_eligible_hours, 2),
            "switch_threshold_percent": threshold_pct,
            "min_hold_hours": hold_hours,
            "deployment_lock_active": not deploy_allowed,
            "strategy_mode": strategy_mode,
            "strategy_weights": {
                "carbon": round(weights["carbon"], 4),
                "latency": round(weights["latency"], 4),
                "cost": round(weights["cost"], 4),
            },
            "strategy_weights_source": settings["weights_source"],
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
