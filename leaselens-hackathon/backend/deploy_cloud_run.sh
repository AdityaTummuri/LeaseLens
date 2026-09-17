#!/usr/bin/env bash
# ==============================================================================
# LeaseLens Backend — Automated Google Cloud Run Deployment Script
#
# Automates:
# 1. Verification of Google Cloud environment & active project
# 2. Enabling required GCP APIs (Cloud Run, Artifact Registry, Cloud Build)
# 3. Building and submitting Docker image via Cloud Build
# 4. Deploying fully-managed Cloud Run service with dynamic port mapping
# 5. Outputting the public HTTPS URL and performing /api/health verification
# ==============================================================================

set -euo pipefail

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}======================================================${RESET}"
echo -e "${BOLD}${BLUE}  🔍 LeaseLens Backend — Google Cloud Run Deployment  ${RESET}"
echo -e "${BOLD}${BLUE}======================================================${RESET}"

# Navigate to backend directory containing Dockerfile
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 1. Verify gcloud CLI installation
if ! command -v gcloud &>/dev/null; then
    # Check if installed in user's home or standard SDK locations
    if [ -x "${HOME}/google-cloud-sdk/bin/gcloud" ]; then
        export PATH="${HOME}/google-cloud-sdk/bin:${PATH}"
    else
        echo -e "${RED}❌ Error: 'gcloud' CLI is not installed or not found in PATH.${RESET}"
        echo -e "Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
fi

# 2. Determine and validate Google Cloud Project ID
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
if [ -z "${PROJECT_ID}" ]; then
    PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
fi

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" = "(unset)" ]; then
    echo -e "${RED}❌ Error: Google Cloud Project ID is not set.${RESET}"
    echo -e "Please specify your project ID using one of the following:"
    echo -e "  export GOOGLE_CLOUD_PROJECT=\"your-gcp-project-id\""
    echo -e "  gcloud config set project \"your-gcp-project-id\""
    exit 1
fi

SERVICE_NAME="${SERVICE_NAME:-leaselens-backend}"
REGION="${REGION:-us-central1}"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:v1"

echo -e "${BLUE}ℹ️  Project ID :${RESET} ${BOLD}${PROJECT_ID}${RESET}"
echo -e "${BLUE}ℹ️  Service    :${RESET} ${BOLD}${SERVICE_NAME}${RESET}"
echo -e "${BLUE}ℹ️  Region     :${RESET} ${BOLD}${REGION}${RESET}"
echo -e "${BLUE}ℹ️  Target Tag :${RESET} ${BOLD}${IMAGE_TAG}${RESET}"
echo ""

# 3. Enable Required Google Cloud APIs
echo -e "${YELLOW}Step 1/4: Enabling required Google Cloud APIs...${RESET}"
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}"
echo -e "${GREEN}✅ Required APIs are active.${RESET}"
echo ""

# 4. Build and Submit Container Image via Cloud Build
echo -e "${YELLOW}Step 2/4: Building and submitting container image via Cloud Build...${RESET}"
gcloud builds submit \
    --tag "${IMAGE_TAG}" \
    --project="${PROJECT_ID}" \
    "${SCRIPT_DIR}"
echo -e "${GREEN}✅ Container image successfully built: ${IMAGE_TAG}${RESET}"
echo ""

# 5. Deploy to Google Cloud Run
echo -e "${YELLOW}Step 3/4: Deploying to Google Cloud Run (managed platform)...${RESET}"
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_TAG}" \
    --platform managed \
    --allow-unauthenticated \
    --region "${REGION}" \
    --project="${PROJECT_ID}" \
    --set-env-vars="PORT=8000,ENVIRONMENT=production" \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --concurrency 80 \
    --timeout 120s

echo -e "${GREEN}✅ Deployment to Google Cloud Run complete.${RESET}"
echo ""

# 6. Retrieve Service URL and Validate Health
echo -e "${YELLOW}Step 4/4: Retrieving service URL and verifying health...${RESET}"
SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" \
    --platform managed \
    --region "${REGION}" \
    --project="${PROJECT_ID}" \
    --format 'value(status.url)')"

echo -e "${BOLD}${GREEN}🚀 Service URL: ${SERVICE_URL}${RESET}"
echo ""

# Validate live endpoint
HEALTH_URL="${SERVICE_URL}/api/health"
echo -e "${BLUE}Testing health endpoint: ${HEALTH_URL}${RESET}"

if command -v curl &>/dev/null; then
    HTTP_STATUS="$(curl -s -o /tmp/health_response.json -w "%{http_code}" "${HEALTH_URL}" || true)"
    if [ "${HTTP_STATUS}" = "200" ]; then
        echo -e "${GREEN}✅ Health check passed! Endpoint returned HTTP 200.${RESET}"
        cat /tmp/health_response.json
        echo ""
    else
        echo -e "${YELLOW}⚠️ Endpoint returned HTTP status: ${HTTP_STATUS}. It may still be initializing.${RESET}"
    fi
fi

echo -e "${BOLD}${GREEN}======================================================${RESET}"
echo -e "${BOLD}${GREEN}  Deployment successfully completed!                  ${RESET}"
echo -e "${BOLD}${GREEN}  API Base URL: ${SERVICE_URL}                         ${RESET}"
echo -e "${BOLD}${GREEN}======================================================${RESET}"
