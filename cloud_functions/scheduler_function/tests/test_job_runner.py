"""
Unit Tests for JobRunner
=========================
Tests Cloud Function invocation and retry logic.

Test Coverage:
- test_job_runner_retries_then_fails: Verify retry mechanism with exponential backoff
- test_trigger_function_success: Test successful Cloud Function invocation
- test_trigger_function_connection_error: Test connection error handling
"""

import pytest
import requests
import requests_mock
import time
from unittest.mock import patch, MagicMock
from job_runner import JobRunner


def test_job_runner_retries_then_fails():
    """
    Test that JobRunner attempts exactly 3 retries before failing.

    Simulates a Cloud Function that consistently returns 500 errors.
    Verifies:
    - JobRunner makes exactly 3 retry attempts
    - Each retry waits 2 seconds (retry_delay)
    - Final result is (False, error_data) after all retries exhausted

    Uses time.time() mocking to verify retry delays without actually sleeping.
    """
    # Configuration for JobRunner
    config = {
        "cloud_provider": None,  # Disable cloud adapter for legacy HTTP testing
        "regions": {
            "FI": {
                "cloud_function_url": "https://fi-worker.cloudfunctions.net/execute"
            }
        },
        "security": {
            "require_authentication": False  # Disable auth for testing
        }
    }

    # Initialize JobRunner with 3 retries, 2 second delay
    runner = JobRunner(config=config, max_retries=3, retry_delay=2, timeout=30)

    # Mock the authentication method to avoid real auth calls
    with patch.object(runner, 'get_auth_token', return_value=None):
        with requests_mock.Mocker() as mock:
            # Mock Cloud Function to always return 500 Internal Server Error
            mock.post(
                "https://fi-worker.cloudfunctions.net/execute",
                json={"error": "Internal Server Error"},
                status_code=500
            )

            # Mock time.sleep to avoid actual delays during testing
            with patch('time.sleep') as mock_sleep:
                # Prepare payload
                payload = {
                    "task_id": "test-task-123",
                    "region": "FI",
                    "carbon_intensity": 45
                }

                # Trigger the function
                success, response_data = runner.trigger_function("FI", payload)

                # Assertions
                assert success is False, "Function should fail after 3 retries"
                assert response_data is not None, "Should return error response data"

                # Verify 3 POST requests were made (3 retry attempts)
                assert mock.call_count == 3, "Should make exactly 3 HTTP requests"

                # Verify sleep was called 2 times (after attempt 1 and 2, not after final attempt)
                assert mock_sleep.call_count == 2, "Should sleep 2 times (between retries)"

                # Verify sleep was called with correct delay (2 seconds)
                for call in mock_sleep.call_args_list:
                    assert call[0][0] == 2, "Each sleep should be 2 seconds"


def test_trigger_function_success():
    """
    Test successful Cloud Function invocation on first attempt.
    Verifies no retries are made when function succeeds.
    """
    config = {
        "cloud_provider": None,  # Disable cloud adapter for legacy HTTP testing
        "regions": {
            "DE": {
                "cloud_function_url": "https://de-worker.cloudfunctions.net/execute"
            }
        },
        "security": {
            "require_authentication": False
        }
    }

    runner = JobRunner(config=config, max_retries=3, retry_delay=2)

    with patch.object(runner, 'get_auth_token', return_value=None):
        with requests_mock.Mocker() as mock:
            # Mock successful response
            mock.post(
                "https://de-worker.cloudfunctions.net/execute",
                json={
                    "status": "success",
                    "job_id": "job-456",
                    "execution_time": 2.5
                },
                status_code=200
            )

            payload = {
                "task_id": "test-task-456",
                "region": "DE",
                "carbon_intensity": 420
            }

            success, response_data = runner.trigger_function("DE", payload)

            # Assertions
            assert success is True, "Function should succeed on first attempt"
            assert response_data is not None, "Should return response data"
            assert response_data.get('status') == 'success', "Response should indicate success"

            # Verify only 1 request was made (no retries)
            assert mock.call_count == 1, "Should make exactly 1 HTTP request"


def test_trigger_function_connection_error():
    """
    Test handling of connection errors with retry logic.
    Simulates network connection failure.
    """
    config = {
        "cloud_provider": None,  # Disable cloud adapter for legacy HTTP testing
        "regions": {
            "JP": {
                "cloud_function_url": "https://jp-worker.cloudfunctions.net/execute"
            }
        },
        "security": {
            "require_authentication": False
        }
    }

    runner = JobRunner(config=config, max_retries=3, retry_delay=2)

    with patch.object(runner, 'get_auth_token', return_value=None):
        with requests_mock.Mocker() as mock:
            # Mock connection error
            mock.post(
                "https://jp-worker.cloudfunctions.net/execute",
                exc=requests.exceptions.ConnectionError("Network unreachable")
            )

            with patch('time.sleep') as mock_sleep:
                payload = {
                    "task_id": "test-task-789",
                    "region": "JP"
                }

                success, response_data = runner.trigger_function("JP", payload)

                # Assertions
                assert success is False, "Should fail after connection errors"
                assert response_data is not None, "Should return error data"
                assert 'error' in response_data, "Response should contain error field"
                assert response_data['error'] == 'connection_error', "Error type should be connection_error"

                # Verify 3 attempts were made
                assert mock.call_count == 3, "Should retry 3 times on connection error"

                # Verify sleep was called 2 times (between retries)
                assert mock_sleep.call_count == 2, "Should sleep between retries"


def test_trigger_function_timeout():
    """
    Test handling of request timeout with retry logic.
    """
    config = {
        "cloud_provider": None,  # Disable cloud adapter for legacy HTTP testing
        "regions": {
            "IN": {
                "cloud_function_url": "https://in-worker.cloudfunctions.net/execute"
            }
        },
        "security": {
            "require_authentication": False
        }
    }

    runner = JobRunner(config=config, max_retries=3, retry_delay=2, timeout=5)

    with patch.object(runner, 'get_auth_token', return_value=None):
        with requests_mock.Mocker() as mock:
            # Mock timeout exception
            mock.post(
                "https://in-worker.cloudfunctions.net/execute",
                exc=requests.exceptions.Timeout
            )

            with patch('time.sleep') as mock_sleep:
                payload = {"task_id": "test-timeout"}

                success, response_data = runner.trigger_function("IN", payload)

                # Assertions
                assert success is False, "Should fail after timeouts"
                assert response_data is not None
                assert response_data['error'] == 'timeout', "Error should indicate timeout"

                # Verify 3 attempts
                assert mock.call_count == 3, "Should retry 3 times on timeout"
                assert mock_sleep.call_count == 2


def test_trigger_function_eventual_success():
    """
    Test that function succeeds on retry after initial failures.
    Simulates: Fail (500) -> Fail (500) -> Success (200)
    """
    config = {
        "cloud_provider": None,  # Disable cloud adapter for legacy HTTP testing
        "regions": {
            "FI": {
                "cloud_function_url": "https://fi-worker.cloudfunctions.net/execute"
            }
        },
        "security": {
            "require_authentication": False
        }
    }

    runner = JobRunner(config=config, max_retries=3, retry_delay=2)

    with patch.object(runner, 'get_auth_token', return_value=None):
        with requests_mock.Mocker() as mock:
            # Create responses: first two fail, third succeeds
            mock.post(
                "https://fi-worker.cloudfunctions.net/execute",
                [
                    {"json": {"error": "Server busy"}, "status_code": 500},
                    {"json": {"error": "Server busy"}, "status_code": 500},
                    {"json": {"status": "success", "message": "Executed"}, "status_code": 200}
                ]
            )

            with patch('time.sleep') as mock_sleep:
                payload = {"task_id": "retry-test"}

                success, response_data = runner.trigger_function("FI", payload)

                # Assertions
                assert success is True, "Should succeed on third attempt"
                assert response_data is not None, "Response data should not be None"
                assert response_data.get('status') == 'success'

                # Verify 3 requests were made
                assert mock.call_count == 3, "Should make 3 requests total"

                # Verify 2 sleeps (after first and second failures)
                assert mock_sleep.call_count == 2


def test_get_function_url():
    """Test URL retrieval from config."""
    config = {
        "cloud_provider": None,  # Disable cloud adapter for legacy HTTP testing
        "regions": {
            "FI": {
                "cloud_function_url": "https://custom-fi-url.run.app"
            }
        },
        "security": {
            "require_authentication": False
        }
    }

    runner = JobRunner(config=config)

    url = runner.get_function_url("FI")
    assert url == "https://custom-fi-url.run.app"

    # Test fallback for unconfigured region
    url_fallback = runner.get_function_url("XX")
    assert url_fallback is not None, "URL should not be None"
    assert "xx-worker" in url_fallback.lower()


def test_authentication_enabled():
    """Test authentication token generation when enabled."""
    config = {
        "cloud_provider": None,  # Disable cloud adapter for legacy HTTP testing
        "regions": {
            "IN": {
                "cloud_function_url": "https://in-worker.cloudfunctions.net/execute"
            }
        },
        "security": {
            "require_authentication": True
        }
    }

    runner = JobRunner(config=config)

    # Mock the get_auth_token to return a fake token
    with patch.object(runner, 'get_auth_token', return_value="fake-token-12345"):
        with requests_mock.Mocker() as mock:
            mock.post(
                "https://in-worker.cloudfunctions.net/execute",
                json={"status": "success"},
                status_code=200
            )

            payload = {"task_id": "auth-test"}
            success, response_data = runner.trigger_function("IN", payload)

            assert success is True

            # Verify Authorization header was sent
            request_headers = mock.request_history[0].headers
            assert 'Authorization' in request_headers
            assert request_headers['Authorization'] == 'Bearer fake-token-12345'
