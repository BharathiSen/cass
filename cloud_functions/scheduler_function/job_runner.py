"""
CASS-Lite v2 - Job Runner
==========================
Cloud Function Execution Module

This module handles triggering Google Cloud Functions in the selected region.
It sends HTTP POST requests with job payloads and handles responses with retry logic.

Author: CASS-Lite v2 Team
Date: November 2025
"""

import json
import time
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime


class JobRunner:
    """
    Executes serverless jobs by triggering Google Cloud Functions.

    This class handles:
    - HTTP POST requests to Cloud Functions
    - Retry logic for failed requests
    - Response validation and error handling
    - Success/failure logging

    Attributes:
        config (dict): Configuration loaded from config.json
        max_retries (int): Maximum retry attempts (default: 3)
        retry_delay (int): Delay between retries in seconds (default: 2)
        timeout (int): Request timeout in seconds (default: 30)
    """

    def __init__(self, config: Dict, max_retries: int = 3, retry_delay: int = 2, timeout: int = 30):
        """
        Initialize the Job Runner.

        Args:
            config: Configuration dictionary with region URLs
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Seconds to wait between retries (default: 2)
            timeout: HTTP request timeout in seconds (default: 30)
        """
        self.config = config
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        print("="*75)
        print(" JOB RUNNER INITIALIZED")
        print("="*75)
        print(f"✓ Max Retries: {self.max_retries}")
        print(f"✓ Retry Delay: {self.retry_delay}s")
        print(f"✓ Timeout: {self.timeout}s")
        print("="*75 + "\n")

    def get_function_url(self, region: str) -> Optional[str]:
        """
        Get the Cloud Function URL for a specific region.

        Args:
            region: Region code (e.g., 'FI', 'IN', 'DE')

        Returns:
            Cloud Function URL string, or None if not configured
        """
        region_config = self.config.get('regions', {}).get(region, {})
        url = region_config.get('cloud_function_url', '')

        if not url:
            print(f"  No Cloud Function URL configured for region {region}")
            # Generate placeholder URL for demonstration
            url = f"https://{region.lower()}-worker.cloudfunctions.net/execute"
            print(f"   Using placeholder: {url}")

        return url

    def get_auth_token(self) -> Optional[str]:
        """Return bearer token for authenticated function calls.

        Default implementation is no-op; callers/tests can override or patch.
        """
        return None

    def trigger_function(self, region: str, payload: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Trigger a Cloud Function in the specified region with retry logic.

        Args:
            region: Target region code (e.g., 'FI', 'IN')
            payload: JSON payload to send to the Cloud Function

        Returns:
            Tuple of (success: bool, response_data: dict or None)
        """
        print("\n" + "="*75)
        print(" TRIGGERING CLOUD FUNCTION")
        print("="*75)
        print(f" Region: {region}")
        print(f"📦 Task ID: {payload.get('task_id', 'N/A')}")
        print(f" Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Get Cloud Function URL
        function_url = self.get_function_url(region)
        if not function_url:
            print(" Cannot trigger function: No URL available")
            return False, None

        print(f"🔗 URL: {function_url}")
        print("="*75 + "\n")

        # Attempt to trigger with retries
        for attempt in range(1, self.max_retries + 1):
            print(f" Attempt {attempt}/{self.max_retries}...")

            try:
                # Send POST request
                start_time = time.time()

                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'CASS-Lite-v2-Scheduler'
                }

                require_auth = self.config.get('security', {}).get('require_authentication', False)
                if require_auth:
                    token = self.get_auth_token()
                    if token:
                        headers['Authorization'] = f'Bearer {token}'

                response = requests.post(
                    function_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                elapsed_time = round((time.time() - start_time) * 1000)  # milliseconds

                # Handle response
                success, response_data = self.handle_response(response, elapsed_time)

                if success:
                    print(f" Function triggered successfully (attempt {attempt})")
                    return True, response_data
                else:
                    print(f"  Function returned error (attempt {attempt})")

                    # Retry if not last attempt
                    if attempt < self.max_retries:
                        print(f"⏳ Retrying in {self.retry_delay} seconds...\n")
                        time.sleep(self.retry_delay)
                    else:
                        print(" All retry attempts exhausted")
                        return False, response_data

            except requests.exceptions.Timeout:
                print(f"  Request timeout (>{self.timeout}s)")

                if attempt < self.max_retries:
                    print(f"⏳ Retrying in {self.retry_delay} seconds...\n")
                    time.sleep(self.retry_delay)
                else:
                    print(" All retry attempts exhausted")
                    return False, {'error': 'timeout', 'message': 'Request timed out'}

            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Connection error: {str(e)[:100]}")

                if attempt < self.max_retries:
                    print(f"⏳ Retrying in {self.retry_delay} seconds...\n")
                    time.sleep(self.retry_delay)
                else:
                    print(" All retry attempts exhausted")
                    return False, {'error': 'connection_error', 'message': str(e)}

            except requests.exceptions.RequestException as e:
                print(f" Request failed: {str(e)[:100]}")

                if attempt < self.max_retries:
                    print(f"⏳ Retrying in {self.retry_delay} seconds...\n")
                    time.sleep(self.retry_delay)
                else:
                    print(" All retry attempts exhausted")
                    return False, {'error': 'request_exception', 'message': str(e)}

            except Exception as e:
                print(f" Unexpected error: {str(e)[:100]}")
                return False, {'error': 'unexpected', 'message': str(e)}

        return False, None

    def handle_response(self, response: requests.Response, elapsed_time: int) -> Tuple[bool, Optional[Dict]]:
        """
        Handle and validate Cloud Function response.

        Args:
            response: HTTP response object
            elapsed_time: Request duration in milliseconds

        Returns:
            Tuple of (success: bool, response_data: dict or None)
        """
        print("\n" + "="*75)
        print("📨 CLOUD FUNCTION RESPONSE")
        print("="*75)
        print(f"  Response Time: {elapsed_time} ms")
        print(f" Status Code: {response.status_code}")

        # Parse response body
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {
                'raw_response': response.text[:200] if response.text else 'Empty response',
                'content_type': response.headers.get('Content-Type', 'unknown')
            }

        # Check status code
        if response.status_code == 200:
            print(" Status: SUCCESS (200 OK)")
            print(f"📦 Response Data:")

            # Pretty print response
            if isinstance(response_data, dict):
                for key, value in list(response_data.items())[:5]:  # Show first 5 keys
                    print(f"   {key}: {value}")
            else:
                print(f"   {str(response_data)[:100]}")

            print("="*75 + "\n")
            return True, response_data

        elif response.status_code == 404:
            print(" Status: NOT FOUND (404)")
            print("   The Cloud Function URL does not exist")
            print("    Tip: Update config.json with correct URL or deploy function")
            print("="*75 + "\n")
            return False, {'error': 'not_found', 'status_code': 404, 'data': response_data}

        elif response.status_code == 403:
            print(" Status: FORBIDDEN (403)")
            print("   Authentication or permission error")
            print("    Tip: Check IAM permissions for the Cloud Function")
            print("="*75 + "\n")
            return False, {'error': 'forbidden', 'status_code': 403, 'data': response_data}

        elif response.status_code == 500:
            print(" Status: INTERNAL SERVER ERROR (500)")
            print("   Cloud Function encountered an error")
            print(f"   Error: {response_data}")
            print("="*75 + "\n")
            return False, {'error': 'server_error', 'status_code': 500, 'data': response_data}

        elif response.status_code == 503:
            print(" Status: SERVICE UNAVAILABLE (503)")
            print("   Cloud Function is temporarily unavailable")
            print("="*75 + "\n")
            return False, {'error': 'unavailable', 'status_code': 503, 'data': response_data}

        else:
            print(f"  Status: UNEXPECTED ({response.status_code})")
            print(f"   Response: {response_data}")
            print("="*75 + "\n")
            return False, {'error': 'unexpected_status', 'status_code': response.status_code, 'data': response_data}

    def execute_job(self, instructions: Dict) -> Dict:
        """
        Execute a job using the provided instructions.

        This is the main entry point that coordinates the entire job execution.

        Args:
            instructions: Job instructions from scheduler
                {
                    'target_region': 'FI',
                    'cloud_function_url': 'https://...',
                    'payload': {...},
                    'metadata': {...}
                }

        Returns:
            Execution result dictionary
            {
                'success': True/False,
                'region': 'FI',
                'response': {...},
                'execution_time_ms': 1234,
                'attempts': 1,
                'timestamp': '2025-11-06T...'
            }
        """
        print("\n" + "="*75)
        print(" EXECUTING JOB")
        print("="*75)

        target_region = instructions.get('target_region')
        payload = instructions.get('payload', {})
        metadata = instructions.get('metadata', {})

        print(f" Target Region: {target_region}")
        print(f"📦 Task ID: {payload.get('task_id', 'N/A')}")
        print(f" Carbon Intensity: {payload.get('carbon_intensity', 'N/A')} gCO₂/kWh")
        print(f" Reason: {payload.get('reason', 'N/A')}")
        print("="*75)

        # Trigger the function
        start_time = time.time()
        success, response_data = self.trigger_function(target_region, payload)
        execution_time = round((time.time() - start_time) * 1000)

        # Build result
        result = {
            'success': success,
            'region': target_region,
            'response': response_data,
            'execution_time_ms': execution_time,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata
        }

        # Final status
        print("\n" + "="*75)
        if success:
            print(" JOB EXECUTION SUCCESSFUL")
            print("="*75)
            print(f" Region: {target_region}")
            print(f"  Total Time: {execution_time} ms")
            print(f"✓ Task Completed Successfully")
        else:
            print(" JOB EXECUTION FAILED")
            print("="*75)
            print(f" Region: {target_region}")
            print(f"  Total Time: {execution_time} ms")
            print(f"✗ Task Failed After {self.max_retries} Attempts")
            if response_data:
                print(f"   Error: {response_data.get('error', 'Unknown')}")

        print("="*75 + "\n")

        return result


# Example usage and testing
if __name__ == "__main__":
    """
    Test the Job Runner with sample instructions.

    This demonstrates:
    1. Loading configuration
    2. Creating job instructions
    3. Triggering Cloud Function
    4. Handling response
    """

    print("\n" + "🔧" * 25)
    print("   CASS-LITE v2 - JOB RUNNER TEST")
    print("🔧" * 25 + "\n")

    # Load config
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("  config.json not found, using test configuration")
        config = {
            'regions': {
                'FI': {
                    'name': 'Finland',
                    'cloud_function_url': 'https://fi-worker.cloudfunctions.net/execute'
                }
            }
        }

    # Initialize Job Runner
    runner = JobRunner(config, max_retries=3, retry_delay=2, timeout=10)

    # Create sample job instructions
    sample_instructions = {
        'target_region': 'FI',
        'region_name': 'Finland',
        'cloud_function_url': 'https://fi-worker.cloudfunctions.net/execute',
        'payload': {
            'task_id': f'test_task_{int(time.time())}',
            'scheduled_at': datetime.now().isoformat(),
            'carbon_intensity': 40,
            'reason': 'carbon_optimized',
            'test_mode': True
        },
        'metadata': {
            'scheduler_version': 'CASS-Lite-v2',
            'decision_timestamp': datetime.now().isoformat(),
            'carbon_savings_gco2': 260
        }
    }

    print("\n Sample Job Instructions Created:")
    print(f"   Region: {sample_instructions['target_region']}")
    print(f"   Task ID: {sample_instructions['payload']['task_id']}")
    print(f"   Carbon: {sample_instructions['payload']['carbon_intensity']} gCO₂/kWh\n")

    # Execute job
    result = runner.execute_job(sample_instructions)

    # Display result
    print("\n" + "="*75)
    print(" EXECUTION RESULT")
    print("="*75)
    print(f"Success: {result['success']}")
    print(f"Region: {result['region']}")
    print(f"Execution Time: {result['execution_time_ms']} ms")
    print(f"Timestamp: {result['timestamp']}")
    print("="*75)

    if result['success']:
        print("\n Job Runner test completed successfully!")
    else:
        print("\n  Job Runner test completed with errors")
        print(" Note: This is expected if Cloud Functions are not deployed yet")
        print("   The runner is working correctly - URLs just need to be deployed!")

    print("\n" + "="*75)
    print("📌 NEXT STEPS:")
    print("="*75)
    print("1. Deploy Cloud Functions to the configured URLs")
    print("2. Update config.json with actual Cloud Function URLs")
    print("3. Integrate job_runner with main.py scheduler")
    print("4. Add Firestore logging for execution results")
    print("="*75 + "\n")
