"""
Multi-Cloud Adapter System
Abstract base class and concrete implementations for GCP, AWS, and Azure
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class CloudAdapter(ABC):
    """
    Abstract base class for cloud provider adapters.
    Defines interface for deploying jobs to different cloud platforms.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cloud adapter with configuration.

        Args:
            config: Provider-specific configuration (endpoints, auth, etc.)
        """
        self.config = config or {}
        self.provider_name = self.__class__.__name__.replace('Adapter', '')

    @abstractmethod
    def deploy_job(self, region: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy a job to the specified cloud region.

        Args:
            region: Target cloud region (e.g., 'us-central1', 'us-east-1', 'eastus')
            payload: Job payload containing task data and parameters

        Returns:
            Dict containing deployment result with keys:
                - success: bool
                - job_id: str
                - region: str
                - provider: str
                - message: str
                - response: Any (provider-specific response)
        """
        pass

    @abstractmethod
    def get_regions(self) -> list[str]:
        """
        Get list of available regions for this cloud provider.

        Returns:
            List of region identifiers
        """
        pass

    def _make_request(self, url: str, payload: Dict[str, Any], timeout: int = 30) -> requests.Response:
        """
        Make HTTP request to cloud endpoint with error handling.

        Args:
            url: Target endpoint URL
            payload: Request payload
            timeout: Request timeout in seconds

        Returns:
            Response object
        """
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.provider_name} request failed: {str(e)}")
            raise


class GCPAdapter(CloudAdapter):
    """
    Google Cloud Platform adapter for Cloud Functions and Cloud Run.
    """

    REGIONS = [
        'us-central1', 'us-east1', 'us-west1', 'us-west2',
        'europe-west1', 'europe-west2', 'europe-west3',
        'asia-east1', 'asia-northeast1', 'asia-south1', 'asia-southeast1'
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.config.get('base_url', 'https://REGION-PROJECT_ID.cloudfunctions.net')
        self.function_name = self.config.get('function_name', 'cass-worker')
        self.project_id = self.config.get('project_id', 'cass-lite')

    def deploy_job(self, region: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy job to GCP Cloud Function.

        Args:
            region: GCP region (e.g., 'us-central1')
            payload: Job payload

        Returns:
            Deployment result dictionary
        """
        # Construct GCP Cloud Function URL
        url = self.config.get('worker_url')
        if not url:
            # Fallback to constructing URL from region
            url = f"https://{region}-{self.project_id}.cloudfunctions.net/{self.function_name}"

        logger.info(f"Deploying job to GCP region: {region}")

        try:
            response = self._make_request(url, payload)

            return {
                'success': True,
                'job_id': payload.get('job_id', 'unknown'),
                'region': region,
                'provider': 'GCP',
                'message': f'Job deployed to GCP Cloud Function in {region}',
                'response': response.json() if response.content else {}
            }
        except Exception as e:
            logger.error(f"GCP deployment failed: {str(e)}")
            return {
                'success': False,
                'job_id': payload.get('job_id', 'unknown'),
                'region': region,
                'provider': 'GCP',
                'message': f'Deployment failed: {str(e)}',
                'response': None
            }

    def get_regions(self) -> list[str]:
        """Get available GCP regions."""
        return self.REGIONS


class AWSAdapter(CloudAdapter):
    """
    Amazon Web Services adapter for Lambda functions.
    """

    REGIONS = [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1',
        'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.config.get('base_url', 'https://FUNCTION_ID.lambda-url.REGION.on.aws')
        self.function_name = self.config.get('function_name', 'cass-worker')
        self.account_id = self.config.get('account_id', '123456789012')

    def deploy_job(self, region: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy job to AWS Lambda function.

        Args:
            region: AWS region (e.g., 'us-east-1')
            payload: Job payload

        Returns:
            Deployment result dictionary
        """
        # Construct AWS Lambda URL (using Function URL feature)
        url = self.config.get('worker_url')
        if not url:
            # Fallback to mocked endpoint (replace with actual Lambda URL)
            function_id = self.config.get('function_id', 'abcdefghijk')
            url = f"https://{function_id}.lambda-url.{region}.on.aws/"

        logger.info(f"Deploying job to AWS region: {region}")

        try:
            # AWS Lambda expects different payload structure
            aws_payload = {
                'body': payload,
                'headers': {
                    'Content-Type': 'application/json'
                }
            }

            response = self._make_request(url, aws_payload)

            return {
                'success': True,
                'job_id': payload.get('job_id', 'unknown'),
                'region': region,
                'provider': 'AWS',
                'message': f'Job deployed to AWS Lambda in {region}',
                'response': response.json() if response.content else {}
            }
        except Exception as e:
            logger.error(f"AWS deployment failed: {str(e)}")
            return {
                'success': False,
                'job_id': payload.get('job_id', 'unknown'),
                'region': region,
                'provider': 'AWS',
                'message': f'Deployment failed: {str(e)}',
                'response': None
            }

    def get_regions(self) -> list[str]:
        """Get available AWS regions."""
        return self.REGIONS


class AzureAdapter(CloudAdapter):
    """
    Microsoft Azure adapter for Azure Functions.
    """

    REGIONS = [
        'eastus', 'eastus2', 'westus', 'westus2', 'centralus',
        'northeurope', 'westeurope', 'uksouth',
        'southeastasia', 'eastasia', 'australiaeast', 'centralindia'
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.config.get('base_url', 'https://APP_NAME.azurewebsites.net')
        self.function_name = self.config.get('function_name', 'cass-worker')
        self.app_name = self.config.get('app_name', 'cass-function-app')

    def deploy_job(self, region: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy job to Azure Function.

        Args:
            region: Azure region (e.g., 'eastus')
            payload: Job payload

        Returns:
            Deployment result dictionary
        """
        # Construct Azure Function URL
        url = self.config.get('worker_url')
        if not url:
            # Fallback to constructing URL
            url = f"https://{self.app_name}-{region}.azurewebsites.net/api/{self.function_name}"

        logger.info(f"Deploying job to Azure region: {region}")

        try:
            # Azure Functions can accept direct JSON payload
            response = self._make_request(url, payload)

            return {
                'success': True,
                'job_id': payload.get('job_id', 'unknown'),
                'region': region,
                'provider': 'Azure',
                'message': f'Job deployed to Azure Function in {region}',
                'response': response.json() if response.content else {}
            }
        except Exception as e:
            logger.error(f"Azure deployment failed: {str(e)}")
            return {
                'success': False,
                'job_id': payload.get('job_id', 'unknown'),
                'region': region,
                'provider': 'Azure',
                'message': f'Deployment failed: {str(e)}',
                'response': None
            }

    def get_regions(self) -> list[str]:
        """Get available Azure regions."""
        return self.REGIONS


def get_cloud_adapter(provider: str, config: Optional[Dict[str, Any]] = None) -> CloudAdapter:
    """
    Factory function to get appropriate cloud adapter based on provider.

    Args:
        provider: Cloud provider name ('gcp', 'aws', 'azure')
        config: Provider-specific configuration

    Returns:
        CloudAdapter instance for the specified provider

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower().strip()

    adapters = {
        'gcp': GCPAdapter,
        'google': GCPAdapter,
        'google-cloud': GCPAdapter,
        'aws': AWSAdapter,
        'amazon': AWSAdapter,
        'azure': AzureAdapter,
        'microsoft-azure': AzureAdapter
    }

    adapter_class = adapters.get(provider)
    if not adapter_class:
        raise ValueError(
            f"Unsupported cloud provider: {provider}. "
            f"Supported providers: {', '.join(set(adapters.keys()))}"
        )

    logger.info(f"Initializing {adapter_class.__name__} for provider: {provider}")
    return adapter_class(config)
