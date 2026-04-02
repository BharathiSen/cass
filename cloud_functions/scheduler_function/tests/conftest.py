"""
Pytest Configuration and Shared Fixtures
=========================================
Common test utilities and fixtures for scheduler tests.
"""

import pytest
import sys
from pathlib import Path

# Add scheduler directory to Python path for imports
scheduler_path = Path(__file__).parent.parent
if str(scheduler_path) not in sys.path:
    sys.path.insert(0, str(scheduler_path))


@pytest.fixture
def sample_carbon_data():
    """Sample carbon intensity data for testing."""
    return {
        "IN": {
            "zone": "IN",
            "carbonIntensity": 650,
            "datetime": "2025-01-15T10:30:00Z",
            "updatedAt": "2025-01-15T10:35:00Z"
        },
        "FI": {
            "zone": "FI",
            "carbonIntensity": 45,
            "datetime": "2025-01-15T10:30:00Z",
            "updatedAt": "2025-01-15T10:35:00Z"
        },
        "DE": {
            "zone": "DE",
            "carbonIntensity": 420,
            "datetime": "2025-01-15T10:30:00Z",
            "updatedAt": "2025-01-15T10:35:00Z"
        }
    }


@pytest.fixture
def sample_job_runner_config():
    """Sample JobRunner configuration for testing."""
    return {
        "regions": {
            "IN": {
                "cloud_function_url": "https://asia-south1-cass-lite.cloudfunctions.net/run_worker_job"
            },
            "FI": {
                "cloud_function_url": "https://europe-north1-cass-lite.cloudfunctions.net/run_worker_job"
            },
            "DE": {
                "cloud_function_url": "https://europe-west3-cass-lite.cloudfunctions.net/run_worker_job"
            }
        },
        "security": {
            "require_authentication": False,  # Disabled for testing
            "service_account": "scheduler-sa@cass-lite.iam.gserviceaccount.com"
        },
        "monitoring": {
            "alerts": {
                "high_error_rate_threshold": 0.05
            }
        }
    }


@pytest.fixture
def sample_job_payload():
    """Sample job payload for Cloud Function invocation."""
    return {
        "task_id": "test-task-12345",
        "region": "FI",
        "carbon_intensity": 45,
        "timestamp": "2025-01-15T10:30:00Z",
        "priority": "high"
    }


@pytest.fixture
def mock_api_key():
    """Mock ElectricityMap API key for testing."""
    return "test-api-key-gwASf8vJiQ92CPIuRzuy"
