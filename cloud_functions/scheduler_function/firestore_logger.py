"""
CASS-Lite v2 - Firestore Logger
================================
Database Logging Module for Google Cloud Firestore

This module handles persisting scheduling decisions, execution results,
and analytics data to Google Cloud Firestore for long-term tracking and visualization.

Author: CASS-Lite v2 Team
Date: November 2025
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import Counter


class FirestoreLogger:
    """
    Logs scheduling decisions and execution results to Google Cloud Firestore.

    This class provides methods to:
    - Save scheduling decisions with full metadata
    - Retrieve historical decisions
    - Compute summary statistics
    - Handle Firestore connection and errors gracefully

    Attributes:
        config (dict): Configuration with Firestore project details
        client: Firestore client instance (None if not initialized)
        collection_name (str): Name of the Firestore collection
        connected (bool): Whether Firestore connection is active
    """

    def __init__(self, config: Dict):
        """
        Initialize the Firestore Logger.

        Args:
            config: Configuration dictionary with Firestore settings
                {
                    'firestore': {
                        'project_id': 'my-project',
                        'collection': 'carbon_logs',
                        'credentials_path': 'path/to/service-account.json'
                    }
                }
        """
        print("\n" + "="*75)
        print("  INITIALIZING FIRESTORE LOGGER")
        print("="*75)

        self.config = config
        self.client = None
        self.collection_name = config.get('firestore', {}).get('collection', 'carbon_logs')
        self.state_collection = config.get('firestore', {}).get('state_collection', 'scheduler_state')
        self._local_state: Dict[str, Any] = {}
        self.connected = False

        # Attempt to initialize Firestore client
        try:
            self._initialize_client()
        except Exception as e:
            print(f"  Could not initialize Firestore client: {str(e)[:100]}")
            print("   Logger will operate in console-only mode")
            print("="*75 + "\n")

    def _initialize_client(self) -> None:
        """
        Initialize Google Cloud Firestore client.

        Attempts to load credentials and connect to Firestore.
        Falls back to console-only mode if connection fails.
        """
        try:
            # Try to import Firestore
            from google.cloud import firestore
            from google.oauth2 import service_account

            firestore_config = self.config.get('firestore', {})
            project_id = firestore_config.get('project_id', '')
            credentials_path = firestore_config.get('credentials_path', '')

            if not project_id:
                print("  No Firestore project_id configured")
                print("   Update config.json with your GCP project ID")
                print("   Operating in console-only mode")
                print("="*75 + "\n")
                return

            # Load credentials if path is provided
            if credentials_path:
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_path
                    )
                    self.client = firestore.Client(
                        project=project_id,
                        credentials=credentials
                    )
                    print(f"✓ Credentials loaded from: {credentials_path}")
                except FileNotFoundError:
                    print(f"  Credentials file not found: {credentials_path}")
                    print("   Attempting default authentication...")
                    self.client = firestore.Client(project=project_id)
            else:
                # Use default credentials (environment variable, gcloud, etc.)
                print("   Using default GCP credentials...")
                self.client = firestore.Client(project=project_id)

            # Test connection
            self.client.collection(self.collection_name).limit(1).get()

            self.connected = True
            print(f" Connected to Firestore successfully!")
            print(f"   Project: {project_id}")
            print(f"   Collection: {self.collection_name}")
            print("="*75 + "\n")

        except ImportError:
            print("  google-cloud-firestore package not installed")
            print("   Install with: pip install google-cloud-firestore")
            print("   Operating in console-only mode")
            print("="*75 + "\n")

        except Exception as e:
            print(f"  Firestore connection failed: {str(e)[:150]}")
            print("   Operating in console-only mode")
            print("="*75 + "\n")

    def log_decision(self, decision_data: Dict, execution_result: Optional[Dict] = None) -> bool:
        """
        Log a scheduling decision to Firestore.

        Args:
            decision_data: Decision information from scheduler
                {
                    'timestamp': '2025-11-06T...',
                    'selected_region': 'FI',
                    'region_name': 'Finland',
                    'carbon_intensity': 42,
                    'savings_gco2': 230,
                    'savings_percent': 84.6,
                    ...
                }
            execution_result: Optional job execution result
                {
                    'success': True,
                    'execution_time_ms': 1234,
                    'response': {...}
                }

        Returns:
            True if logged successfully, False otherwise
        """
        print("\n" + "="*75)
        print(" LOGGING DECISION TO FIRESTORE")
        print("="*75)

        if not self.connected or not self.client:
            print("  Firestore not connected - logging to console only")
            self._log_to_console(decision_data, execution_result)
            print("="*75 + "\n")
            return False

        try:
            # Build log document
            log_doc = {
                # Decision data
                'timestamp': decision_data.get('timestamp'),
                'task_id': f"task_{int(time.time())}",
                'region': decision_data.get('selected_region'),
                'selected_region': decision_data.get('selected_region'),
                'region_name': decision_data.get('region_name'),
                'region_flag': decision_data.get('region_flag'),
                'carbon_intensity': decision_data.get('carbon_intensity'),
                'carbon_intensity_24h_avg': decision_data.get('carbon_intensity_24h_avg'),
                'savings_gco2': decision_data.get('savings_gco2'),
                'savings_percent': decision_data.get('savings_percent'),
                'average_carbon': decision_data.get('average_carbon'),
                'total_regions_checked': decision_data.get('total_regions_checked'),
                'decision_time_ms': decision_data.get('decision_time_ms'),
                'data_timestamp': decision_data.get('data_timestamp'),
                'decision_basis': decision_data.get('decision_basis'),
                'switch_applied': decision_data.get('switch_applied'),
                'switch_reason': decision_data.get('switch_reason'),
                'last_switched_hours_ago': decision_data.get('last_switched_hours_ago'),
                'next_eligible_switch_in_hours': decision_data.get('next_eligible_switch_in_hours'),
                'switch_threshold_percent': decision_data.get('switch_threshold_percent'),
                'min_hold_hours': decision_data.get('min_hold_hours'),
                'selected_score': decision_data.get('selected_score'),
                'score_breakdown': decision_data.get('score_breakdown'),
                'all_candidates': decision_data.get('all_candidates'),
                'region_samples': decision_data.get('region_samples'),

                # Execution result (if provided)
                'execution_success': execution_result.get('success') if execution_result else None,
                'execution_time_ms': execution_result.get('execution_time_ms') if execution_result else None,
                'execution_error': execution_result.get('response', {}).get('error') if execution_result and not execution_result.get('success') else None,

                # Metadata
                'logged_at': datetime.now().isoformat(),
                'scheduler_version': 'CASS-Lite-v2',
            }

            # Add to Firestore
            doc_ref = self.client.collection(self.collection_name).add(log_doc)
            doc_id = doc_ref[1].id

            print(f" Decision logged successfully!")
            print(f"   Document ID: {doc_id}")
            print(f"   Region: {log_doc['region_flag']} {log_doc['selected_region']}")
            print(f"   Carbon: {log_doc['carbon_intensity']} gCO₂/kWh")
            print(f"   Savings: {log_doc['savings_gco2']} gCO₂/kWh ({log_doc['savings_percent']}%)")

            if execution_result:
                status = " Success" if execution_result.get('success') else " Failed"
                print(f"   Execution: {status}")

            print("="*75 + "\n")
            return True

        except Exception as e:
            print(f" Failed to log to Firestore: {str(e)[:150]}")
            print("   Falling back to console logging...")
            self._log_to_console(decision_data, execution_result)
            print("="*75 + "\n")
            return False

    def get_scheduler_state(self) -> Dict[str, Any]:
        """Get persisted scheduler state used for cooldown and hysteresis decisions."""
        if not self.connected or not self.client:
            return self._local_state.copy()

        try:
            doc = self.client.collection(self.state_collection).document('active').get()
            if doc.exists:
                state = doc.to_dict() or {}
                self._local_state = state
                return state
        except Exception as e:
            print(f"  Could not fetch scheduler state from Firestore: {str(e)[:120]}")

        return self._local_state.copy()

    def update_scheduler_state(
        self,
        selected_region: str,
        selected_score: float,
        last_switch_timestamp: str,
    ) -> bool:
        """Persist scheduler state for next-cycle switching decisions."""
        state_payload = {
            'selected_region': selected_region,
            'last_deployed_region': selected_region,
            'selected_score': selected_score,
            'last_switch_timestamp': last_switch_timestamp,
            'last_deployment_time': last_switch_timestamp,
            'updated_at': datetime.now().isoformat(),
        }

        self._local_state = state_payload
        if not self.connected or not self.client:
            return True

        try:
            self.client.collection(self.state_collection).document('active').set(state_payload)
            return True
        except Exception as e:
            print(f"  Could not update scheduler state in Firestore: {str(e)[:120]}")
            return False

    def _log_to_console(self, decision_data: Dict, execution_result: Optional[Dict] = None) -> None:
        """
        Log decision to console as fallback when Firestore is unavailable.

        Args:
            decision_data: Decision information
            execution_result: Optional execution result
        """
        print("\n CONSOLE LOG (Firestore unavailable):")
        print(f"   Timestamp: {decision_data.get('timestamp')}")
        print(f"   Region: {decision_data.get('region_flag', '')} {decision_data.get('selected_region')} - {decision_data.get('region_name')}")
        print(f"   Carbon: {decision_data.get('carbon_intensity')} gCO₂/kWh")
        print(f"   Savings: {decision_data.get('savings_gco2')} gCO₂/kWh ({decision_data.get('savings_percent')}%)")
        print(f"   Decision Time: {decision_data.get('decision_time_ms')} ms")

        if execution_result:
            status = "Success" if execution_result.get('success') else "Failed"
            print(f"   Execution: {status} ({execution_result.get('execution_time_ms')} ms)")

    def fetch_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """
        Fetch the most recent scheduling decisions from Firestore.

        Args:
            limit: Maximum number of records to retrieve (default: 10)

        Returns:
            List of decision dictionaries, ordered by timestamp (newest first)
        """
        print("\n" + "="*75)
        print(f" FETCHING RECENT DECISIONS (last {limit})")
        print("="*75)

        if not self.connected or not self.client:
            print("  Firestore not connected - no historical data available")
            print("="*75 + "\n")
            return []

        try:
            # Query Firestore
            docs = (
                self.client.collection(self.collection_name)
                .order_by('timestamp', direction='DESCENDING')
                .limit(limit)
                .stream()
            )

            decisions = []
            for doc in docs:
                decisions.append(doc.to_dict())

            print(f" Retrieved {len(decisions)} decision(s)")

            # Display summary
            if decisions:
                print("\n Recent Decisions:")
                for i, dec in enumerate(decisions[:5], 1):  # Show first 5
                    print(f"   {i}. {dec.get('region_flag', '')} {dec.get('selected_region')} - {dec.get('carbon_intensity')} gCO₂/kWh ({dec.get('timestamp', 'N/A')[:10]})")

            print("="*75 + "\n")
            return decisions

        except Exception as e:
            print(f" Failed to fetch decisions: {str(e)[:150]}")
            print("="*75 + "\n")
            return []

    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Compute summary statistics from historical data.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with summary statistics
            {
                'total_decisions': 42,
                'avg_carbon_intensity': 123.5,
                'most_frequent_region': 'FI',
                'total_carbon_saved': 12345,
                'avg_savings_percent': 78.3,
                'success_rate': 95.2
            }
        """
        print("\n" + "="*75)
        print(f" COMPUTING SUMMARY STATISTICS (last {days} days)")
        print("="*75)

        if not self.connected or not self.client:
            print("  Firestore not connected - no statistics available")
            print("="*75 + "\n")
            return {}

        try:
            # Calculate date threshold
            threshold = datetime.now() - timedelta(days=days)
            threshold_str = threshold.isoformat()

            # Query Firestore for recent decisions
            docs = (
                self.client.collection(self.collection_name)
                .where('timestamp', '>=', threshold_str)
                .stream()
            )

            decisions = [doc.to_dict() for doc in docs]

            if not decisions:
                print(f"  No decisions found in the last {days} days")
                print("="*75 + "\n")
                return {
                    'total_decisions': 0,
                    'period_days': days
                }

            # Compute statistics
            total_decisions = len(decisions)

            carbon_intensities = [d.get('carbon_intensity', 0) for d in decisions if d.get('carbon_intensity')]
            avg_carbon = sum(carbon_intensities) / len(carbon_intensities) if carbon_intensities else 0

            regions = [d.get('selected_region') for d in decisions if d.get('selected_region')]
            region_counter = Counter(regions)
            most_frequent_region = region_counter.most_common(1)[0] if region_counter else ('N/A', 0)

            total_carbon_saved = sum(d.get('savings_gco2', 0) for d in decisions)

            savings_percents = [d.get('savings_percent', 0) for d in decisions if d.get('savings_percent')]
            avg_savings_percent = sum(savings_percents) / len(savings_percents) if savings_percents else 0

            successful_executions = sum(1 for d in decisions if d.get('execution_success') is True)
            total_with_execution = sum(1 for d in decisions if d.get('execution_success') is not None)
            success_rate = (successful_executions / total_with_execution * 100) if total_with_execution > 0 else 0

            stats = {
                'total_decisions': total_decisions,
                'period_days': days,
                'avg_carbon_intensity': round(avg_carbon, 1),
                'most_frequent_region': most_frequent_region[0],
                'most_frequent_region_count': most_frequent_region[1],
                'total_carbon_saved_gco2': round(total_carbon_saved),
                'avg_savings_percent': round(avg_savings_percent, 1),
                'success_rate': round(success_rate, 1) if total_with_execution > 0 else None,
                'region_distribution': dict(region_counter)
            }

            # Display statistics
            print(f" Statistics computed successfully!")
            print(f"\n Summary (last {days} days):")
            print(f"   Total Decisions: {stats['total_decisions']}")
            print(f"   Avg Carbon Intensity: {stats['avg_carbon_intensity']} gCO₂/kWh")
            print(f"   Most Frequent Region: {stats['most_frequent_region']} ({stats['most_frequent_region_count']} times)")
            print(f"   Total Carbon Saved: {stats['total_carbon_saved_gco2']} gCO₂/kWh")
            print(f"   Avg Savings: {stats['avg_savings_percent']}%")
            if stats['success_rate'] is not None:
                print(f"   Execution Success Rate: {stats['success_rate']}%")

            print("\n Region Distribution:")
            for region, count in region_counter.most_common():
                percent = (count / total_decisions * 100)
                print(f"   {region}: {count} times ({percent:.1f}%)")

            print("="*75 + "\n")
            return stats

        except Exception as e:
            print(f" Failed to compute statistics: {str(e)[:150]}")
            print("="*75 + "\n")
            return {}

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get Firestore connection status.

        Returns:
            Dictionary with connection details
        """
        return {
            'connected': self.connected,
            'collection': self.collection_name,
            'project_id': self.config.get('firestore', {}).get('project_id', 'Not configured'),
            'mode': 'Firestore' if self.connected else 'Console-only'
        }


# Example usage and testing
if __name__ == "__main__":
    """
    Test the Firestore Logger.

    This demonstrates:
    1. Initializing the logger
    2. Logging a sample decision
    3. Fetching recent decisions
    4. Computing statistics
    """

    print("\n" + " " * 25)
    print("   CASS-LITE v2 - FIRESTORE LOGGER TEST")
    print(" " * 25 + "\n")

    # Load config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("  config.json not found, using test configuration")
        config = {
            'firestore': {
                'project_id': '',
                'collection': 'carbon_logs',
                'credentials_path': ''
            }
        }

    # Initialize logger
    logger = FirestoreLogger(config)

    # Display connection status
    status = logger.get_connection_status()
    print("="*75)
    print(" CONNECTION STATUS")
    print("="*75)
    print(f"Mode: {status['mode']}")
    print(f"Connected: {status['connected']}")
    print(f"Collection: {status['collection']}")
    print(f"Project ID: {status['project_id']}")
    print("="*75 + "\n")

    # Create sample decision
    sample_decision = {
        'timestamp': datetime.now().isoformat(),
        'selected_region': 'FI',
        'region_name': 'Finland',
        'region_flag': '',
        'carbon_intensity': 42,
        'savings_gco2': 230,
        'savings_percent': 84.6,
        'average_carbon': 272,
        'total_regions_checked': 6,
        'decision_time_ms': 8726,
        'data_timestamp': datetime.now().isoformat()
    }

    sample_execution = {
        'success': False,
        'execution_time_ms': 5973,
        'response': {'error': 'not_found', 'status_code': 404}
    }

    # Test logging
    print("🧪 Test 1: Logging a decision...")
    logger.log_decision(sample_decision, sample_execution)

    # Test fetching recent decisions
    print("🧪 Test 2: Fetching recent decisions...")
    recent = logger.fetch_recent_decisions(limit=10)

    # Test statistics
    print("🧪 Test 3: Computing summary statistics...")
    stats = logger.get_summary_stats(days=7)

    print("\n" + "="*75)
    print(" FIRESTORE LOGGER TEST COMPLETED")
    print("="*75)
    print(" Notes:")
    print("   - If Firestore is not configured, logger operates in console-only mode")
    print("   - To enable Firestore:")
    print("     1. Create a GCP project")
    print("     2. Enable Firestore API")
    print("     3. Create service account & download JSON key")
    print("     4. Update config.json with project_id and credentials_path")
    print("="*75 + "\n")
