#!/bin/bash

################################################################################
# CASS-Lite v2 - Worker Function Deployment Script
################################################################################
#
# This script deploys the worker Cloud Function to Google Cloud Platform.
#
# The worker function:
# - Executes the actual workload in the selected region
# - Simulates carbon-optimized job execution
# - Returns execution results and metrics
#
# Prerequisites:
# - gcloud CLI installed and configured
# - GCP project created
# - Billing enabled
# - Cloud Functions API enabled
#
# Usage:
#   bash deploy_worker.sh
#   or
#   ./deploy_worker.sh
#
# Note: Deploy this function in multiple regions for true carbon optimization!
#
################################################################################

echo "========================================================================"
echo "⚡ CASS-LITE v2 - Deploying Worker Function"
echo "========================================================================"
echo ""

# Configuration
FUNCTION_NAME="run_worker_job"
REGION="asia-south1"
RUNTIME="python311"
MEMORY="256MB"
TIMEOUT="300s"
ENTRY_POINT="run_worker_job"
SOURCE_DIR="cloud_functions/worker_job"

echo "📋 Deployment Configuration:"
echo "   Function Name: $FUNCTION_NAME"
echo "   Region: $REGION"
echo "   Runtime: $RUNTIME"
echo "   Memory: $MEMORY"
echo "   Timeout: $TIMEOUT"
echo "   Entry Point: $ENTRY_POINT"
echo "   Source: $SOURCE_DIR"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ ERROR: gcloud CLI is not installed"
    echo "   Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✓ gcloud CLI found"
echo ""

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "⚠️  WARNING: No active gcloud account found"
    echo "   Run: gcloud auth login"
    echo ""
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "⚠️  WARNING: No GCP project configured"
    echo "   Run: gcloud config set project YOUR_PROJECT_ID"
    echo ""
else
    echo "✓ Using GCP Project: $PROJECT_ID"
    echo ""
fi

# Show multi-region deployment option
echo "========================================================================"
echo "💡 TIP: Multi-Region Deployment"
echo "========================================================================"
echo "For true carbon optimization, deploy this worker function in multiple"
echo "regions that correspond to your target zones:"
echo ""
echo "   🇮🇳 India:        asia-south1 (Mumbai)"
echo "   🇫🇮 Finland:      europe-north1 (Finland)"
echo "   🇩🇪 Germany:      europe-west3 (Frankfurt)"
echo "   🇯🇵 Japan:        asia-northeast1 (Tokyo)"
echo "   🇦🇺 Australia:    australia-southeast1 (Sydney)"
echo "   🇧🇷 Brazil:       southamerica-east1 (São Paulo)"
echo ""
echo "Current deployment region: $REGION"
echo ""

# Confirm deployment
echo "========================================================================"
echo "⚠️  Ready to deploy Cloud Function"
echo "========================================================================"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 0
fi

echo ""
echo "========================================================================"
echo "📦 Deploying Cloud Function..."
echo "========================================================================"
echo ""

# Deploy the function
gcloud functions deploy $FUNCTION_NAME \
    --runtime $RUNTIME \
    --region $REGION \
    --source $SOURCE_DIR \
    --entry-point $ENTRY_POINT \
    --trigger-http \
    --allow-unauthenticated \
    --memory $MEMORY \
    --timeout $TIMEOUT \
    --min-instances 0 \
    --max-instances 1 \
    --set-env-vars PYTHONUNBUFFERED=1

# Check deployment status
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "✅ DEPLOYMENT SUCCESSFUL"
    echo "========================================================================"
    echo ""

    # Get function URL
    FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(httpsTrigger.url)" 2>/dev/null)

    if [ -n "$FUNCTION_URL" ]; then
        echo "🔗 Function URL:"
        echo "   $FUNCTION_URL"
        echo ""
        echo "📋 Test with curl:"
        echo '   curl -X POST '"$FUNCTION_URL"' \'
        echo '     -H "Content-Type: application/json" \'
        echo '     -d '"'"'{"task_id":"test_123","region":"'"$REGION"'","carbon_intensity":42}'"'"
        echo ""
    fi

    echo "✅ Worker function is now live in $REGION!"
    echo ""
    echo "📌 Next steps:"
    echo "   1. Test the function with the URL above"
    echo "   2. Update config.json with the function URL:"
    echo "      \"regions\": {"
    echo "        \"FI\": {"
    echo "          \"cloud_function_url\": \"$FUNCTION_URL\""
    echo "        }"
    echo "      }"
    echo ""
    echo "   3. Deploy to additional regions for multi-region support"
    echo "   4. Run the scheduler to trigger carbon-aware routing"
    echo ""
    echo "========================================================================"
else
    echo ""
    echo "========================================================================"
    echo "❌ DEPLOYMENT FAILED"
    echo "========================================================================"
    echo ""
    echo "Common issues:"
    echo "   - Cloud Functions API not enabled"
    echo "   - Insufficient permissions"
    echo "   - Billing not enabled"
    echo "   - Invalid source directory"
    echo ""
    echo "Run: gcloud functions deploy --help"
    echo ""
    exit 1
fi
