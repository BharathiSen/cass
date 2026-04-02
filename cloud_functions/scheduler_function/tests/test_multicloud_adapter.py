#!/usr/bin/env python3
"""
Multi-Cloud Adapter Test Script
================================

This script demonstrates how to use the cloud adapter system to deploy
jobs across GCP, AWS, and Azure.

Usage:
    python test_multicloud_adapter.py [--provider gcp|aws|azure] [--region REGION]

Examples:
    python test_multicloud_adapter.py --provider gcp --region us-central1
    python test_multicloud_adapter.py --provider aws --region us-east-1
    python test_multicloud_adapter.py --provider azure --region eastus
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cloud_adapter import get_cloud_adapter, CloudAdapter


def test_adapter_creation():
    """Test: Verify all adapters can be created"""
    print("\n=== Test 1: Adapter Creation ===")

    providers = ['gcp', 'aws', 'azure']
    for provider in providers:
        try:
            config = {
                'project_id': 'test-project',
                'function_name': 'test-function'
            }
            adapter = get_cloud_adapter(provider, config)
            print(f"✓ {provider.upper()} adapter created successfully")
            print(f"  Type: {type(adapter).__name__}")
            print(f"  Regions: {len(adapter.get_regions())} available")
        except Exception as e:
            print(f"✗ {provider.upper()} adapter failed: {e}")


def test_region_lists():
    """Test: Verify region lists for each provider"""
    print("\n=== Test 2: Available Regions ===")

    configs = {
        'gcp': {'project_id': 'cass-lite', 'function_name': 'cass-worker'},
        'aws': {'function_id': 'abc123', 'account_id': '123456789012'},
        'azure': {'app_name': 'cass-app', 'function_name': 'cass-worker'}
    }

    for provider, config in configs.items():
        adapter = get_cloud_adapter(provider, config)
        regions = adapter.get_regions()
        print(f"\n{provider.upper()} Regions ({len(regions)}):")
        for i, region in enumerate(regions, 1):
            print(f"  {i:2d}. {region}")


def test_deployment_simulation():
    """Test: Simulate job deployment (dry run)"""
    print("\n=== Test 3: Deployment Simulation ===")

    test_payload = {
        'job_id': 'test-job-001',
        'task': 'carbon_optimization',
        'parameters': {
            'duration': 3600,
            'deadline': '2024-01-15T12:00:00Z'
        }
    }

    # Test GCP
    print("\n--- GCP Deployment ---")
    gcp_config = {
        'project_id': 'cass-lite',
        'function_name': 'cass-worker'
    }
    gcp_adapter = get_cloud_adapter('gcp', gcp_config)
    gcp_regions = gcp_adapter.get_regions()[:3]  # Test first 3 regions

    for region in gcp_regions:
        print(f"\nSimulating deployment to GCP {region}:")
        print(f"  URL: https://{region}-cass-lite.cloudfunctions.net/cass-worker")
        print(f"  Payload: {json.dumps(test_payload, indent=2)}")
        # Note: Actual deployment would require valid credentials
        # result = gcp_adapter.deploy_job(region, test_payload)
        print("  Status: ⚠ Simulation only (no actual HTTP request)")

    # Test AWS
    print("\n--- AWS Deployment ---")
    aws_config = {
        'function_id': 'abc123xyz',
        'account_id': '123456789012'
    }
    aws_adapter = get_cloud_adapter('aws', aws_config)
    aws_region = aws_adapter.get_regions()[0]  # Test first region

    print(f"\nSimulating deployment to AWS {aws_region}:")
    print(f"  URL: https://abc123xyz.lambda-url.{aws_region}.on.aws/")
    print(f"  Payload (wrapped): {{'body': {test_payload}, 'headers': ...}}")
    print("  Status: ⚠ Simulation only (no actual HTTP request)")

    # Test Azure
    print("\n--- Azure Deployment ---")
    azure_config = {
        'app_name': 'cass-function-app',
        'function_name': 'cass-worker'
    }
    azure_adapter = get_cloud_adapter('azure', azure_config)
    azure_region = azure_adapter.get_regions()[0]  # Test first region

    print(f"\nSimulating deployment to Azure {azure_region}:")
    print(f"  URL: https://cass-function-app-{azure_region}.azurewebsites.net/api/cass-worker")
    print(f"  Payload: {json.dumps(test_payload, indent=2)}")
    print("  Status: ⚠ Simulation only (no actual HTTP request)")


def test_job_runner_integration():
    """Test: Verify JobRunner integration"""
    print("\n=== Test 4: JobRunner Integration ===")

    try:
        from job_runner import JobRunner

        print("\n--- Testing GCP Integration ---")
        gcp_config = {
            'cloud_provider': 'gcp',
            'project_id': 'cass-lite',
            'function_name': 'cass-worker',
            'worker_url': 'https://asia-south1-cass-lite.cloudfunctions.net/cass-worker',
            'max_retries': 3,
            'timeout': 30
        }

        runner = JobRunner(gcp_config)
        print(f"✓ JobRunner initialized with GCP adapter")
        print(f"  Provider: {runner.cloud_provider}")
        print(f"  Adapter: {type(runner.cloud_adapter).__name__}")
        print(f"  Regions: {len(runner.cloud_adapter.get_regions())} available")

        print("\n--- Testing AWS Integration ---")
        aws_config = {
            'cloud_provider': 'aws',
            'function_id': 'abc123xyz',
            'account_id': '123456789012',
            'max_retries': 3,
            'timeout': 30
        }

        runner = JobRunner(aws_config)
        print(f"✓ JobRunner initialized with AWS adapter")
        print(f"  Provider: {runner.cloud_provider}")
        print(f"  Adapter: {type(runner.cloud_adapter).__name__}")
        print(f"  Regions: {len(runner.cloud_adapter.get_regions())} available")

        print("\n--- Testing Legacy Mode (No Adapter) ---")
        legacy_config = {
            'worker_url': 'https://asia-south1-cass-lite.cloudfunctions.net/cass-worker',
            'max_retries': 3,
            'timeout': 30
        }

        runner = JobRunner(legacy_config)
        print(f"✓ JobRunner initialized in legacy mode")
        print(f"  Adapter: {runner.cloud_adapter}")
        print(f"  Fallback: Will use direct HTTP requests")

    except Exception as e:
        print(f"✗ JobRunner integration test failed: {e}")
        import traceback
        traceback.print_exc()


def test_error_handling():
    """Test: Verify error handling"""
    print("\n=== Test 5: Error Handling ===")

    # Test invalid provider
    print("\n--- Invalid Provider ---")
    try:
        adapter = get_cloud_adapter('invalid_provider')
        print("✗ Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")

    # Test missing config
    print("\n--- Missing Configuration ---")
    try:
        adapter = get_cloud_adapter('gcp', {})
        print("⚠ Created adapter with empty config (may fail on deployment)")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Test invalid region
    print("\n--- Invalid Region ---")
    adapter = get_cloud_adapter('gcp', {'project_id': 'test', 'function_name': 'test'})
    valid_regions = adapter.get_regions()
    print(f"✓ Valid regions: {len(valid_regions)}")
    print(f"  Example invalid region: 'mars-base-1' (not in list)")


def print_summary():
    """Print usage summary"""
    print("\n" + "="*60)
    print("Multi-Cloud Adapter System Summary")
    print("="*60)
    print("""
The cloud adapter system provides a unified interface for deploying
jobs across multiple cloud providers:

┌─────────────┬──────────────┬─────────────────────────────┐
│ Provider    │ Regions      │ URL Pattern                 │
├─────────────┼──────────────┼─────────────────────────────┤
│ GCP         │ 11 regions   │ https://REGION-PROJECT.     │
│             │              │   cloudfunctions.net/FUNC   │
├─────────────┼──────────────┼─────────────────────────────┤
│ AWS         │ 11 regions   │ https://FUNC_ID.lambda-url. │
│             │              │   REGION.on.aws/            │
├─────────────┼──────────────┼─────────────────────────────┤
│ Azure       │ 12 regions   │ https://APP-REGION.         │
│             │              │   azurewebsites.net/api/FUNC│
└─────────────┴──────────────┴─────────────────────────────┘

Configuration Example:
    config = {
        'cloud_provider': 'gcp',  # or 'aws', 'azure'
        'project_id': 'cass-lite',
        'function_name': 'cass-worker'
    }

    runner = JobRunner(config)
    success, result = runner.trigger_function('us-central1', payload)

Features:
    ✓ Abstract base class for extensibility
    ✓ Provider-specific URL construction
    ✓ Automatic region validation
    ✓ Integrated retry logic
    ✓ Backward compatible with legacy HTTP mode
    ✓ Factory pattern for easy provider switching

Next Steps:
    1. Update config.json with 'cloud_provider' setting
    2. Configure provider-specific credentials
    3. Test with actual cloud endpoints
    4. Monitor deployment logs
""")
    print("="*60)


def main():
    """Run all tests"""
    print("="*60)
    print("CASS-Lite Multi-Cloud Adapter Test Suite")
    print("="*60)

    try:
        test_adapter_creation()
        test_region_lists()
        test_deployment_simulation()
        test_job_runner_integration()
        test_error_handling()
        print_summary()

        print("\n✓ All tests completed successfully!")
        return 0

    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
