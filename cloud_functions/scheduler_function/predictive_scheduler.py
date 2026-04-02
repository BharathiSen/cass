"""
Predictive Multi-Objective Scheduler

Uses time-series forecasting (Prophet) to predict future carbon intensity
and optimizes region selection based on weighted objectives:
- Carbon intensity (environmental impact)
- Network latency (performance)
- Regional cost (economic efficiency)
"""

import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np

# Prophet for time series forecasting
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available. Install with: pip install prophet")

from carbon_fetcher import CarbonFetcher
from firestore_logger import FirestoreLogger


# Regional cost per vCPU-hour (USD) - Based on Google Cloud pricing
REGION_COSTS = {
    'IN': 0.0476,  # Mumbai
    'FI': 0.0570,  # Finland (Europe-North1)
    'DE': 0.0475,  # Frankfurt
    'JP': 0.0560,  # Tokyo
    'AU-NSW': 0.0595,  # Sydney
    'BR-CS': 0.0450,  # São Paulo
}

# Average network latency from asia-south1 (ms)
REGION_LATENCY = {
    'IN': 10,    # Mumbai (same region)
    'FI': 180,   # Finland
    'DE': 150,   # Frankfurt
    'JP': 90,    # Tokyo
    'AU-NSW': 140,  # Sydney
    'BR-CS': 350,   # São Paulo
}


class PredictiveScheduler:
    """Multi-objective scheduler with carbon intensity forecasting"""

    def __init__(self, firestore_project_id: str = "cass-lite", api_key: str = ""):
        # Initialize carbon fetcher with API key from environment or parameter
        import os
        api_key = api_key or os.getenv('ELECTRICITYMAP_API_KEY', 'gwASf8vJiQ92CPIuRzuy')
        self.carbon_fetcher = CarbonFetcher(api_key=api_key)

        # Create config for FirestoreLogger
        config = {
            'firestore': {
                'project_id': firestore_project_id,
                'collection': 'decisions',
                'credentials_path': ''
            }
        }
        self.firestore_logger = FirestoreLogger(config)
        self.logger = logging.getLogger(__name__)

    def fetch_historical_data(
        self,
        region: str,
        hours: int = 168
    ) -> List[Dict]:
        """
        Fetch historical carbon intensity data from Firestore

        Args:
            region: Region code (e.g., 'FI', 'DE')
            hours: Number of hours of history to fetch

        Returns:
            List of historical data points with timestamp and carbon_intensity
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # Query Firestore for historical decisions
            decisions = self.firestore_logger.get_decisions_by_region(
                region=region,
                start_time=start_time,
                end_time=end_time,
                limit=hours * 12  # 12 data points per hour (5-min intervals)
            )

            return [
                {
                    'timestamp': d.get('timestamp'),
                    'carbon_intensity': d.get('carbon_intensity', 0)
                }
                for d in decisions
                if d.get('carbon_intensity') is not None
            ]
        except Exception as e:
            self.logger.error(f"Failed to fetch historical data for {region}: {e}")
            return []

    def predict_carbon_intensity(
        self,
        region: str,
        hours_ahead: int = 24
    ) -> Optional[float]:
        """
        Predict future carbon intensity using Prophet forecasting

        Args:
            region: Region code
            hours_ahead: Hours to forecast ahead

        Returns:
            Predicted carbon intensity (gCO2/kWh) or None if prediction fails
        """
        if not PROPHET_AVAILABLE:
            self.logger.warning("Prophet not available, using current value")
            return None

        # Fetch historical data
        historical = self.fetch_historical_data(region, hours=168)  # 1 week

        if len(historical) < 48:  # Need at least 2 days of data
            self.logger.warning(f"Insufficient data for {region}, need 48+ points, got {len(historical)}")
            return None

        try:
            # Prepare data for Prophet (requires 'ds' and 'y' columns)
            import pandas as pd
            df = pd.DataFrame({
                'ds': [h['timestamp'] for h in historical],
                'y': [h['carbon_intensity'] for h in historical]
            })

            # Handle duplicates by averaging
            df = df.groupby('ds').agg({'y': 'mean'}).reset_index()

            # Train Prophet model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05
            )

            # Suppress Prophet logging
            import logging as prophet_logging
            prophet_logging.getLogger('prophet').setLevel(prophet_logging.ERROR)

            model.fit(df)

            # Make future dataframe
            future = model.make_future_dataframe(periods=hours_ahead, freq='H')
            forecast = model.predict(future)

            # Get prediction for hours_ahead from now
            predicted_value = forecast.iloc[-1]['yhat']

            return max(0, predicted_value)  # Ensure non-negative

        except Exception as e:
            self.logger.error(f"Prediction failed for {region}: {e}")
            return None

    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize value to [0, 1] range

        Args:
            value: Value to normalize
            min_val: Minimum value in dataset
            max_val: Maximum value in dataset

        Returns:
            Normalized value between 0 and 1
        """
        if max_val == min_val:
            return 0.5
        return (value - min_val) / (max_val - min_val)

    def calculate_multi_objective_score(
        self,
        carbon_intensity: float,
        latency: float,
        cost: float,
        all_carbon: List[float],
        all_latency: List[float],
        all_costs: List[float],
        w_carbon: float = 0.5,
        w_latency: float = 0.3,
        w_cost: float = 0.2
    ) -> float:
        """
        Calculate weighted multi-objective score

        Args:
            carbon_intensity: Carbon intensity (gCO2/kWh)
            latency: Network latency (ms)
            cost: Regional cost (USD/vCPU-hour)
            all_carbon: List of all carbon values for normalization
            all_latency: List of all latency values
            all_costs: List of all cost values
            w_carbon: Weight for carbon objective (0-1)
            w_latency: Weight for latency objective (0-1)
            w_cost: Weight for cost objective (0-1)

        Returns:
            Weighted score (lower is better)
        """
        # Normalize each objective to [0, 1]
        norm_carbon = self.normalize_value(
            carbon_intensity,
            min(all_carbon),
            max(all_carbon)
        )
        norm_latency = self.normalize_value(
            latency,
            min(all_latency),
            max(all_latency)
        )
        norm_cost = self.normalize_value(
            cost,
            min(all_costs),
            max(all_costs)
        )

        # Weighted sum (lower is better)
        score = (w_carbon * norm_carbon +
                 w_latency * norm_latency +
                 w_cost * norm_cost)

        return score

    def select_optimal_region(
        self,
        w_carbon: float = 0.5,
        w_latency: float = 0.3,
        w_cost: float = 0.2,
        use_prediction: bool = True,
        hours_ahead: int = 1
    ) -> Dict:
        """
        Select optimal region using multi-objective optimization

        Args:
            w_carbon: Weight for carbon objective
            w_latency: Weight for latency objective
            w_cost: Weight for cost objective
            use_prediction: Use forecasted carbon intensity
            hours_ahead: Hours to forecast ahead

        Returns:
            Dict with optimal region and decision details
        """
        # Normalize weights
        total_weight = w_carbon + w_latency + w_cost
        w_carbon /= total_weight
        w_latency /= total_weight
        w_cost /= total_weight

        # Fetch current carbon intensity
        carbon_data_raw = self.carbon_fetcher.fetch_all_regions(display_details=False)

        # Extract carbon intensity values from response
        carbon_data = {}
        for region, data in carbon_data_raw.items():
            if data and 'carbonIntensity' in data:
                carbon_data[region] = data['carbonIntensity']
            elif data and 'carbon_intensity' in data:
                carbon_data[region] = data['carbon_intensity']

        if not carbon_data:
            return {
                'success': False,
                'error': 'Failed to fetch carbon data'
            }

        # Build candidate regions with metrics
        candidates = []

        for region, intensity in carbon_data.items():
            # Use prediction if available, otherwise current value
            if use_prediction:
                predicted = self.predict_carbon_intensity(region, hours_ahead)
                carbon_value = predicted if predicted is not None else intensity
            else:
                carbon_value = intensity

            candidates.append({
                'region': region,
                'carbon_intensity': carbon_value,
                'current_intensity': intensity,
                'predicted_intensity': predicted if use_prediction else None,
                'latency': REGION_LATENCY.get(region, 100),
                'cost': REGION_COSTS.get(region, 0.05)
            })

        # Extract metrics for normalization
        all_carbon = [c['carbon_intensity'] for c in candidates]
        all_latency = [c['latency'] for c in candidates]
        all_costs = [c['cost'] for c in candidates]

        # Calculate scores for each candidate
        for candidate in candidates:
            candidate['score'] = self.calculate_multi_objective_score(
                carbon_intensity=candidate['carbon_intensity'],
                latency=candidate['latency'],
                cost=candidate['cost'],
                all_carbon=all_carbon,
                all_latency=all_latency,
                all_costs=all_costs,
                w_carbon=w_carbon,
                w_latency=w_latency,
                w_cost=w_cost
            )

        # Sort by score (lower is better)
        candidates.sort(key=lambda x: x['score'])

        optimal = candidates[0]

        # Calculate savings vs average
        avg_carbon = np.mean(all_carbon)
        savings = avg_carbon - optimal['carbon_intensity']

        return {
            'success': True,
            'region': optimal['region'],
            'carbon_intensity': optimal['carbon_intensity'],
            'current_intensity': optimal['current_intensity'],
            'predicted_intensity': optimal.get('predicted_intensity'),
            'latency': optimal['latency'],
            'cost': optimal['cost'],
            'score': optimal['score'],
            'weights': {
                'carbon': w_carbon,
                'latency': w_latency,
                'cost': w_cost
            },
            'savings_gco2': savings,
            'avg_carbon_intensity': avg_carbon,
            'all_candidates': candidates,
            'timestamp': datetime.utcnow().isoformat()
        }

    def generate_pareto_frontier(
        self,
        objective1: str = 'carbon',
        objective2: str = 'latency'
    ) -> List[Dict]:
        """
        Generate Pareto frontier for two objectives

        Args:
            objective1: First objective ('carbon', 'latency', or 'cost')
            objective2: Second objective

        Returns:
            List of Pareto-optimal points
        """
        carbon_data_raw = self.carbon_fetcher.fetch_all_regions(display_details=False)

        # Extract carbon intensity values
        carbon_data = {}
        for region, data in carbon_data_raw.items():
            if data and 'carbonIntensity' in data:
                carbon_data[region] = data['carbonIntensity']
            elif data and 'carbon_intensity' in data:
                carbon_data[region] = data['carbon_intensity']

        if not carbon_data:
            return []

        # Build all solutions
        solutions = []
        for region, intensity in carbon_data.items():
            solutions.append({
                'region': region,
                'carbon': intensity,
                'latency': REGION_LATENCY.get(region, 100),
                'cost': REGION_COSTS.get(region, 0.05)
            })

        # Find Pareto-optimal solutions
        pareto_frontier = []

        for i, sol_i in enumerate(solutions):
            is_dominated = False

            for j, sol_j in enumerate(solutions):
                if i == j:
                    continue

                # Check if sol_j dominates sol_i
                obj1_better = sol_j[objective1] <= sol_i[objective1]
                obj2_better = sol_j[objective2] <= sol_i[objective2]
                at_least_one_strictly_better = (
                    sol_j[objective1] < sol_i[objective1] or
                    sol_j[objective2] < sol_i[objective2]
                )

                if obj1_better and obj2_better and at_least_one_strictly_better:
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_frontier.append(sol_i)

        # Sort by first objective
        pareto_frontier.sort(key=lambda x: x[objective1])

        return pareto_frontier


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    scheduler = PredictiveScheduler()

    # Test with different weight configurations
    print("\n=== Carbon-Optimized (70% carbon, 20% latency, 10% cost) ===")
    result = scheduler.select_optimal_region(
        w_carbon=0.7,
        w_latency=0.2,
        w_cost=0.1,
        use_prediction=False
    )

    if result['success']:
        print(f"✓ Selected Region: {result['region']}")
        print(f"  Carbon: {result['carbon_intensity']:.1f} gCO2/kWh")
        print(f"  Latency: {result['latency']}ms")
        print(f"  Cost: ${result['cost']:.4f}/vCPU-hour")
        print(f"  Score: {result['score']:.3f}")

    print("\n=== Latency-Optimized (20% carbon, 70% latency, 10% cost) ===")
    result = scheduler.select_optimal_region(
        w_carbon=0.2,
        w_latency=0.7,
        w_cost=0.1,
        use_prediction=False
    )

    if result['success']:
        print(f"✓ Selected Region: {result['region']}")
        print(f"  Carbon: {result['carbon_intensity']:.1f} gCO2/kWh")
        print(f"  Latency: {result['latency']}ms")
        print(f"  Cost: ${result['cost']:.4f}/vCPU-hour")
        print(f"  Score: {result['score']:.3f}")

    print("\n=== Balanced (50% carbon, 30% latency, 20% cost) ===")
    result = scheduler.select_optimal_region(
        w_carbon=0.5,
        w_latency=0.3,
        w_cost=0.2,
        use_prediction=False
    )

    if result['success']:
        print(f"✓ Selected Region: {result['region']}")
        print(f"  Carbon: {result['carbon_intensity']:.1f} gCO2/kWh")
        print(f"  Latency: {result['latency']}ms")
        print(f"  Cost: ${result['cost']:.4f}/vCPU-hour")
        print(f"  Score: {result['score']:.3f}")
