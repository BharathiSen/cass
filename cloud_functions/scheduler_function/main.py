"""
CASS-Lite v2 - Main Scheduler
==============================
Carbon-Aware Serverless Scheduler Decision Engine

This is the core orchestrator that:
1. Fetches real-time carbon intensity data from multiple regions
2. Selects the greenest (lowest carbon) region
3. Logs the decision for tracking and analytics
4. Prepares deployment instructions for the job runner

Author: CASS-Lite v2 Team
Date: November 2025
"""

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
from carbon_fetcher import CarbonFetcher
from job_runner import JobRunner
from firestore_logger import FirestoreLogger
from policy_engine import PolicyEngine


DEFAULT_REGION_LATENCY_MS = {
    "IN": 10,
    "FI": 180,
    "DE": 150,
    "JP": 90,
    "AU-NSW": 140,
    "BR-CS": 350,
}

DEFAULT_REGION_COST_USD = {
    "IN": 0.0476,
    "FI": 0.0570,
    "DE": 0.0475,
    "JP": 0.0560,
    "AU-NSW": 0.0595,
    "BR-CS": 0.0450,
}


def can_deploy(last_deployment_time: Optional[str], hold_hours: float = 24.0) -> Dict[str, float | bool]:
    """
    Deployment guard for strict cooldown policy.

    Returns:
        {
            "allowed": bool,
            "hours_since_last": float,
            "next_eligible_in_hours": float,
        }
    """
    if not last_deployment_time:
        return {
            "allowed": True,
            "hours_since_last": 1e9,
            "next_eligible_in_hours": 0.0,
        }

    try:
        dt = datetime.fromisoformat(str(last_deployment_time).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours_since = (now - dt.astimezone(timezone.utc)).total_seconds() / 3600
        allowed = hours_since >= hold_hours
        return {
            "allowed": allowed,
            "hours_since_last": round(max(hours_since, 0.0), 2),
            "next_eligible_in_hours": round(max(hold_hours - hours_since, 0.0), 2),
        }
    except Exception:
        # Fail-safe: allow deployment instead of hard-failing scheduler.
        return {
            "allowed": True,
            "hours_since_last": 1e9,
            "next_eligible_in_hours": 0.0,
        }


class CarbonScheduler:
    """
    Main scheduler that orchestrates carbon-aware deployment decisions.

    This class integrates carbon data fetching, decision logic, and
    prepares instructions for serverless job execution.

    Attributes:
        config (dict): Configuration loaded from config.json
        fetcher (CarbonFetcher): Carbon intensity data fetcher
        last_decision (dict): Most recent scheduling decision
    """

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the Carbon Scheduler.

        Args:
            config_path: Path to configuration file (default: config.json)
        """
        print("="*75)
        print("🚀 CASS-LITE v2 - CARBON-AWARE SERVERLESS SCHEDULER")
        print("="*75)
        print(f"⏰ Initializing scheduler at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize carbon fetcher
        api_key = self.config.get('api', {}).get('electricitymap_key', '')
        cache_ttl = self.config.get('api', {}).get('cache_ttl_seconds', 300)

        if not api_key or api_key == "YOUR_API_KEY_HERE":
            # Use hardcoded key for now (in production, use environment variables)
            api_key = "gwASf8vJiQ92CPIuRzuy"

        self.fetcher = CarbonFetcher(api_key=api_key, cache_ttl=cache_ttl)
        self.job_runner = JobRunner(self.config, max_retries=3, retry_delay=2, timeout=30)
        self.firestore_logger = FirestoreLogger(self.config)
        self.policy_engine = PolicyEngine(self.config, can_deploy_fn=can_deploy)
        self.last_decision = None

        print(f"✓ Configuration loaded from {config_path}")
        print(f"✓ Carbon fetcher initialized ({len(self.fetcher.regions)} regions)")
        print(f"✓ Job runner initialized")
        print(f"✓ Firestore logger initialized")
        print(f"✓ Policy engine initialized")
        print(f"✓ Cache TTL: {cache_ttl} seconds\n")

    def _load_config(self, config_path: str) -> dict:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to config.json

        Returns:
            Dictionary containing configuration
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file not found: {config_path}")
            print("   Using default configuration...")
            return {
                "api": {"electricitymap_key": "", "cache_ttl_seconds": 300},
                "regions": {},
                "scheduler": {"check_interval_minutes": 15}
            }
        except json.JSONDecodeError as e:
            print(f"⚠️  Error parsing config file: {e}")
            print("   Using default configuration...")
            return {}

    @staticmethod
    def _weighted_average(values: List[float]) -> float:
        """Weighted moving average where recent values get higher weights."""
        if not values:
            return 0.0
        weights = list(range(1, len(values) + 1))
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        return weighted_sum / sum(weights)

    def _build_24h_region_carbon(self, latest_region_samples: Dict[str, float]) -> Dict[str, float]:
        """
        Build smoothed 24h carbon values per region using historical decision logs.
        Falls back to current samples if 24h history is sparse.
        """
        stability_cfg = self.config.get("scheduler", {}).get("stability", {})
        use_weighted = stability_cfg.get("use_weighted_moving_average", True)
        lookback_hours = int(stability_cfg.get("lookback_hours", 24))
        lookback_threshold = datetime.now() - timedelta(hours=lookback_hours)

        history_by_region: Dict[str, List[tuple]] = {zone: [] for zone in latest_region_samples.keys()}
        recent_logs = self.firestore_logger.fetch_recent_decisions(limit=500)

        for row in recent_logs:
            ts_raw = row.get("timestamp")
            if not ts_raw:
                continue
            try:
                ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                continue
            if ts < lookback_threshold:
                continue

            samples = row.get("region_samples")
            if isinstance(samples, dict) and samples:
                for zone, carbon in samples.items():
                    try:
                        if zone in history_by_region:
                            history_by_region[zone].append((ts, float(carbon)))
                    except (TypeError, ValueError):
                        continue
                continue

            # Backward compatibility with older logs (selected region only)
            legacy_region = row.get("selected_region") or row.get("region")
            legacy_carbon = row.get("carbon_intensity")
            try:
                if legacy_region in history_by_region and legacy_carbon is not None:
                    history_by_region[legacy_region].append((ts, float(legacy_carbon)))
            except (TypeError, ValueError):
                continue

        smoothed = {}
        for zone, latest in latest_region_samples.items():
            entries = sorted(history_by_region.get(zone, []), key=lambda item: item[0])
            values = [item[1] for item in entries]
            values.append(float(latest))  # include freshest reading
            smoothed[zone] = self._weighted_average(values) if use_weighted else (sum(values) / len(values))

        return smoothed

    def _score_regions(
        self,
        region_carbon_24h: Dict[str, float],
        latest_region_samples: Dict[str, float],
    ) -> List[Dict]:
        """Compute composite scores using the configured policy strategy."""
        scheduler_cfg = self.config.get("scheduler", {})
        latency_map = scheduler_cfg.get("region_latency_ms", DEFAULT_REGION_LATENCY_MS)
        cost_map = scheduler_cfg.get("region_cost_usd", DEFAULT_REGION_COST_USD)
        return self.policy_engine.score_regions(
            region_carbon_24h=region_carbon_24h,
            latest_region_samples=latest_region_samples,
            latency_map=latency_map,
            cost_map=cost_map,
        )

    def _select_stable_region(self, ranked_candidates: List[Dict]) -> Dict:
        """Apply strategy-aware stable selection (lock + hysteresis)."""
        state = self.firestore_logger.get_scheduler_state()
        return self.policy_engine.select_stable_region(ranked_candidates, scheduler_state=state)

    def make_decision(self) -> Optional[Dict]:
        """
        Core decision-making logic: Analyze carbon data and choose deployment region.

        This method:
        1. Fetches carbon intensity for all regions
        2. Identifies the greenest region
        3. Calculates carbon savings
        4. Logs the decision

        Returns:
            Dictionary containing the scheduling decision, or None if failed
            {
                'timestamp': '2025-11-05T13:45:00',
                'selected_region': 'FI',
                'region_name': 'Finland',
                'region_flag': '🇫🇮',
                'carbon_intensity': 40,
                'savings_gco2': 260,
                'savings_percent': 86.5,
                'average_carbon': 300,
                'total_regions_checked': 6,
                'decision_time_ms': 1234
            }
        """
        print("\n" + "="*75)
        print("🧠 MAKING CARBON-AWARE SCHEDULING DECISION")
        print("="*75)

        start_time = time.time()

        # Step 1: Fetch carbon intensity data for all regions
        print("\n📡 Step 1: Fetching current region carbon data...")
        all_data = self.fetcher.fetch_all_regions(display_details=False)
        latest_samples = {
            zone: payload["carbonIntensity"]
            for zone, payload in all_data.items()
            if payload and "carbonIntensity" in payload
        }

        if not latest_samples:
            print("\n❌ DECISION FAILED: Could not fetch carbon data")
            return None

        # Step 2: Build 24h trend-smoothed carbon values
        print("\n📈 Step 2: Building 24h smoothed carbon trend...")
        carbon_24h = self._build_24h_region_carbon(latest_samples)

        # Step 3: Composite scoring
        ranked = self._score_regions(carbon_24h, latest_samples)
        if not ranked:
            print("\n❌ DECISION FAILED: Could not score regions")
            return None

        # Step 4: Stable switch policy (cooldown + hysteresis)
        stable_choice = self._select_stable_region(ranked)
        selected = stable_choice["selected"]

        # Step 5: Build decision record
        decision_time_ms = round((time.time() - start_time) * 1000)
        avg_24h_carbon = sum(carbon_24h.values()) / len(carbon_24h)
        savings = round(avg_24h_carbon - selected["carbon_24h"], 1)
        savings_percent = round((savings / avg_24h_carbon) * 100, 1) if avg_24h_carbon > 0 else 0.0
        region_info = self.fetcher.regions.get(selected["zone"], {"name": selected["zone"], "flag": "🌍"})

        # Persist stable scheduler state for next cycle
        if stable_choice["switched"]:
            self.firestore_logger.update_scheduler_state(
                selected_region=selected["zone"],
                selected_score=selected["score"],
                last_switch_timestamp=datetime.now(timezone.utc).isoformat(),
            )

        decision = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'selected_region': selected['zone'],
            'region_name': region_info.get('name', selected['zone']),
            'region_flag': region_info.get('flag', '🌍'),
            'carbon_intensity': round(selected['carbon_latest'], 1),
            'carbon_intensity_24h_avg': round(selected['carbon_24h'], 1),
            'savings_gco2': savings,
            'savings_percent': savings_percent,
            'average_carbon': round(avg_24h_carbon, 1),
            'total_regions_checked': len(ranked),
            'decision_time_ms': decision_time_ms,
            'data_timestamp': datetime.now(timezone.utc).isoformat(),
            'decision_basis': f"24h_weighted_average:{stable_choice['strategy_mode']}",
            'strategy_mode': stable_choice['strategy_mode'],
            'strategy_weights': stable_choice['strategy_weights'],
            'strategy_weights_source': stable_choice['strategy_weights_source'],
            'switch_applied': stable_choice['switched'],
            'switch_reason': stable_choice['decision_reason'],
            'deployment_lock_active': stable_choice['deployment_lock_active'],
            'last_switched_hours_ago': stable_choice['last_switch_hours_ago'],
            'next_eligible_switch_in_hours': stable_choice['next_eligible_switch_in_hours'],
            'switch_threshold_percent': stable_choice['switch_threshold_percent'],
            'min_hold_hours': stable_choice['min_hold_hours'],
            'selected_score': selected['score'],
            'score_breakdown': selected['score_breakdown'],
            'all_candidates': stable_choice['ranked'],
            'region_samples': {k: round(v, 1) for k, v in latest_samples.items()},
        }

        # Store decision
        self.last_decision = decision

        # Step 6: Log decision summary
        print("\n" + "="*75)
        print("✅ DECISION COMPLETE")
        print("="*75)
        print(f"🎯 Selected Region: {decision['region_flag']} {decision['region_name']} ({decision['selected_region']})")
        print(f"🌱 Carbon Intensity (24h avg): {decision['carbon_intensity_24h_avg']} gCO₂/kWh")
        print(f"⚡ Current Carbon: {decision['carbon_intensity']} gCO₂/kWh")
        print(f"💰 Carbon Savings: {decision['savings_gco2']} gCO₂/kWh ({decision['savings_percent']}%)")
        print(f"🧭 Decision Basis: {decision['decision_basis']}")
        print(f"🎛️ Strategy Mode: {decision['strategy_mode']}")
        print(f"🔁 Switch Applied: {decision['switch_applied']} ({decision['switch_reason']})")
        if decision['deployment_lock_active']:
            print("🛡️ Deployment locked for stability")
        print(f"⏱️ Next Eligible Switch In: {decision['next_eligible_switch_in_hours']}h")
        print(f"⚡ Decision Time: {decision['decision_time_ms']} ms")
        print(f"📊 Regions Analyzed: {decision['total_regions_checked']}")
        print("="*75 + "\n")

        return decision

    def prepare_job_instructions(self, decision: Optional[Dict] = None) -> Optional[Dict]:
        """
        Prepare instructions for the job runner to execute workload.

        Args:
            decision: Scheduling decision (uses last_decision if None)

        Returns:
            Dictionary with job execution instructions
            {
                'target_region': 'FI',
                'cloud_function_url': 'https://...',
                'payload': {...},
                'metadata': {...}
            }
        """
        if decision is None:
            decision = self.last_decision

        if not decision:
            print("⚠️  No decision available to prepare job instructions")
            return None

        print("\n" + "="*75)
        print("📋 PREPARING JOB EXECUTION INSTRUCTIONS")
        print("="*75)

        target_region = decision['selected_region']

        # Get Cloud Function URL from config
        cloud_function_url = self.config.get('regions', {}).get(
            target_region, {}
        ).get('cloud_function_url', '')

        if not cloud_function_url:
            cloud_function_url = f"https://{target_region.lower()}-worker.cloudfunctions.net/execute"
            print(f"⚠️  No Cloud Function URL configured for {target_region}")
            print(f"   Using placeholder: {cloud_function_url}")

        # Build job instructions
        instructions = {
            'target_region': target_region,
            'region_name': decision['region_name'],
            'cloud_function_url': cloud_function_url,
            'payload': {
                'task_id': f"task_{int(time.time())}",
                'scheduled_at': decision['timestamp'],
                'carbon_intensity': decision['carbon_intensity'],
                'reason': 'carbon_optimized'
            },
            'metadata': {
                'scheduler_version': 'CASS-Lite-v2',
                'decision_timestamp': decision['timestamp'],
                'carbon_savings_gco2': decision['savings_gco2'],
                'carbon_savings_percent': decision['savings_percent']
            }
        }

        print(f"✓ Target Region: {decision['region_flag']} {target_region}")
        print(f"✓ Cloud Function: {cloud_function_url}")
        print(f"✓ Task ID: {instructions['payload']['task_id']}")
        print(f"✓ Carbon Intensity: {decision['carbon_intensity']} gCO₂/kWh")
        print("="*75 + "\n")

        return instructions

    def log_decision_to_console(self, decision: Dict) -> None:
        """
        Log decision details to console (placeholder for Firestore logging).

        Args:
            decision: The scheduling decision to log
        """
        print("\n" + "="*75)
        print("📝 LOGGING DECISION (Console)")
        print("="*75)
        print(f"Timestamp: {decision['timestamp']}")
        print(f"Region: {decision['region_flag']} {decision['selected_region']} - {decision['region_name']}")
        print(f"Carbon: {decision['carbon_intensity']} gCO₂/kWh")
        print(f"Savings: {decision['savings_gco2']} gCO₂/kWh ({decision['savings_percent']}%)")
        print(f"Decision Time: {decision['decision_time_ms']} ms")
        print("="*75)
        print("💡 Note: Firestore logging will be implemented in firestore_logger.py")
        print("="*75 + "\n")

    def run_scheduling_cycle(self) -> bool:
        """
        Execute a complete scheduling cycle.

        This is the main workflow:
        1. Make carbon-aware decision
        2. Prepare job instructions
        3. Log the decision
        4. (Later) Trigger job execution via job_runner

        Returns:
            True if cycle completed successfully, False otherwise
        """
        print("\n" + "="*75)
        print("🔄 STARTING SCHEDULING CYCLE")
        print("="*75)
        print(f"⏰ Cycle started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        try:
            # Step 1: Make decision
            decision = self.make_decision()
            if not decision:
                print("❌ Scheduling cycle failed: No decision made\n")
                return False

            # Step 2: Prepare job instructions
            instructions = self.prepare_job_instructions(decision)
            if not instructions:
                print("❌ Scheduling cycle failed: Could not prepare instructions\n")
                return False

            # Step 3: Log decision
            self.log_decision_to_console(decision)

            # Step 4: Execute job via job runner
            print("="*75)
            print("🚀 EXECUTING JOB IN GREENEST REGION")
            print("="*75 + "\n")

            execution_result = self.job_runner.execute_job(instructions)

            # Step 5: Save to Firestore
            self.firestore_logger.log_decision(decision, execution_result)

            # Summary
            print("="*75)
            print("📌 SCHEDULING CYCLE SUMMARY:")
            print("="*75)
            print("   1. ✅ Carbon data fetched from 6 regions")
            print("   2. ✅ Decision made (greenest region selected)")
            print("   3. ✅ Job triggered via Cloud Function")
            print("   4. ✅ Results logged to Firestore/Console")
            print("   5. ⏳ Dashboard visualization (next phase)")
            print("="*75 + "\n")

            if execution_result['success']:
                print("✅ SCHEDULING CYCLE COMPLETED SUCCESSFULLY\n")
                return True
            else:
                print("⚠️  SCHEDULING CYCLE COMPLETED WITH WARNINGS")
                print("   (Decision was made, but job execution had issues)\n")
                return True  # Still return True since decision was made

        except Exception as e:
            print(f"\n❌ Scheduling cycle failed with error: {e}\n")
            return False

    def get_status(self) -> Dict:
        """
        Get current scheduler status and statistics.

        Returns:
            Dictionary with scheduler status information
        """
        return {
            'scheduler_active': True,
            'regions_configured': len(self.fetcher.regions),
            'last_decision': self.last_decision,
            'cache_ttl_seconds': self.config.get('api', {}).get('cache_ttl_seconds', 300),
            'current_time': datetime.now().isoformat()
        }


# Main execution
if __name__ == "__main__":
    """
    Run the CASS-Lite v2 scheduler.

    This demonstrates a complete scheduling cycle:
    1. Initialize scheduler
    2. Fetch carbon data
    3. Make decision
    4. Prepare job instructions
    5. Log decision
    """

    print("\n" + "🌍" * 25)
    print("   CASS-LITE v2 - CARBON-AWARE SERVERLESS SCHEDULER")
    print("   Making the cloud greener, one decision at a time 🌱")
    print("🌍" * 25 + "\n")

    # Initialize scheduler
    scheduler = CarbonScheduler(config_path="config.json")

    # Run a scheduling cycle
    success = scheduler.run_scheduling_cycle()

    if success:
        # Show status
        print("\n" + "="*75)
        print("📊 SCHEDULER STATUS")
        print("="*75)
        status = scheduler.get_status()
        print(f"Active: {status['scheduler_active']}")
        print(f"Regions: {status['regions_configured']}")
        print(f"Cache TTL: {status['cache_ttl_seconds']}s")
        if status['last_decision']:
            print(f"Last Decision: {status['last_decision']['selected_region']} @ {status['last_decision']['carbon_intensity']} gCO₂/kWh")
        print("="*75 + "\n")

        print("🎉 Scheduler test completed successfully!")
        print("💡 Next: Implement job_runner.py to actually trigger Cloud Functions\n")
    else:
        print("❌ Scheduler test failed. Please check the errors above.\n")


# ============================================================================
# CLOUD FUNCTION HTTP ENTRY POINT
# ============================================================================

import functions_framework

@functions_framework.http
def run_scheduler(request):
    """
    HTTP Cloud Function entry point for scheduling.

    This function is triggered via HTTP POST and runs a complete
    carbon-aware scheduling cycle.

    Args:
        request (flask.Request): The HTTP request object

    Returns:
        JSON response with scheduling results
    """
    print("="*75)
    print("🚀 CLOUD FUNCTION: run_scheduler")
    print("="*75)
    print(f"⏰ Triggered at: {datetime.now().isoformat()}")
    print(f"🔗 Request method: {request.method}")

    try:
        # Get request data (if any)
        request_json = request.get_json(silent=True)
        print(f"📦 Request payload: {request_json if request_json else 'None'}")

        # Initialize scheduler
        print("\n📋 Initializing Carbon Scheduler...")
        scheduler = CarbonScheduler(config_path='config.json')

        # Backend safety guard: block explicit region switch requests during lock window.
        if request_json and request_json.get('requested_region'):
            req_region = request_json.get('requested_region')
            state = scheduler.firestore_logger.get_scheduler_state()
            current_region = state.get('last_deployed_region') or state.get('selected_region')
            hold_hours = float(scheduler.config.get('scheduler', {}).get('stability', {}).get('min_hold_hours', 24))
            guard = can_deploy(state.get('last_deployment_time') or state.get('last_switch_timestamp'), hold_hours=hold_hours)

            if current_region and req_region != current_region and not guard['allowed']:
                response_data = {
                    'success': False,
                    'status': 'locked',
                    'message': 'Deployment locked for stability',
                    'current_region': current_region,
                    'requested_region': req_region,
                    'next_eligible_switch_in_hours': guard['next_eligible_in_hours'],
                    'cloud_function': 'run_scheduler',
                    'triggered_at': datetime.now().isoformat(),
                }
                return (response_data, 423, {'Content-Type': 'application/json'})

        # Run scheduling cycle
        print("\n🔄 Running scheduling cycle...")
        success = scheduler.run_scheduling_cycle()

        if success and scheduler.last_decision:
            decision = scheduler.last_decision

            response_data = {
                'success': True,
                'status': 'completed',
                'decision': {
                    'region': decision.get('selected_region'),
                    'region_name': decision.get('region_name'),
                    'region_flag': decision.get('region_flag'),
                    'strategy_mode': decision.get('strategy_mode'),
                    'carbon_intensity': decision.get('carbon_intensity'),
                    'savings_gco2': decision.get('savings_gco2'),
                    'savings_percent': decision.get('savings_percent'),
                    'decision_time_ms': decision.get('decision_time_ms'),
                    'timestamp': decision.get('timestamp'),
                    'switch_reason': decision.get('switch_reason'),
                    'deployment_lock_active': decision.get('deployment_lock_active'),
                    'next_eligible_switch_in_hours': decision.get('next_eligible_switch_in_hours'),
                },
                'message': f"✅ Scheduled job in {decision.get('region_name')} ({decision.get('carbon_intensity')} gCO₂/kWh)",
                'cloud_function': 'run_scheduler',
                'triggered_at': datetime.now().isoformat()
            }

            print("\n" + "="*75)
            print("✅ CLOUD FUNCTION COMPLETED SUCCESSFULLY")
            print("="*75)
            print(f"🌱 Selected Region: {decision.get('region_flag')} {decision.get('selected_region')}")
            print(f"⚡ Carbon Intensity: {decision.get('carbon_intensity')} gCO₂/kWh")
            print(f"💰 Carbon Savings: {decision.get('savings_gco2')} gCO₂/kWh")
            print("="*75)

            return (response_data, 200, {'Content-Type': 'application/json'})

        else:
            response_data = {
                'success': False,
                'status': 'failed',
                'message': '❌ Scheduling cycle failed',
                'cloud_function': 'run_scheduler',
                'triggered_at': datetime.now().isoformat()
            }

            print("\n" + "="*75)
            print("❌ CLOUD FUNCTION FAILED")
            print("="*75)

            return (response_data, 500, {'Content-Type': 'application/json'})

    except Exception as e:
        error_message = str(e)
        print(f"\n❌ ERROR: {error_message}")

        response_data = {
            'success': False,
            'status': 'error',
            'error': error_message,
            'message': '❌ Unexpected error in scheduling',
            'cloud_function': 'run_scheduler',
            'triggered_at': datetime.now().isoformat()
        }

        return (response_data, 500, {'Content-Type': 'application/json'})
