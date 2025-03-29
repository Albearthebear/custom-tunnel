#!/bin/bash
# Deploy script for IP Rotation Cloud Function

# Configuration
PROJECT_ID=${PROJECT_ID:-"custom-tunnel-project"}
REGION=${REGION:-"europe-west4"}
FUNCTION_NAME=${FUNCTION_NAME:-"rotate_ip"}
RUNTIME="python310"
MEMORY="256MB"
TIMEOUT="120s"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying IP Rotation Cloud Function${NC}"
echo -e "${YELLOW}Project: ${PROJECT_ID}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Function Name: ${FUNCTION_NAME}${NC}"
echo

# Create a temporary directory for function deployment
TEMP_DIR=$(mktemp -d)
cp ip_rotation_function.py ${TEMP_DIR}/main.py

# Create requirements.txt
cat > ${TEMP_DIR}/requirements.txt << EOF
google-api-python-client==2.86.0
protobuf==4.24.0
EOF

# Enable required services
echo -e "${GREEN}Enabling required services...${NC}"
gcloud services enable \
  cloudfunctions.googleapis.com \
  compute.googleapis.com \
  --project=${PROJECT_ID}

# Deploy the function
echo -e "${GREEN}Deploying function...${NC}"
gcloud functions deploy ${FUNCTION_NAME} \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --runtime=${RUNTIME} \
  --memory=${MEMORY} \
  --timeout=${TIMEOUT} \
  --entry-point=rotate_ip \
  --trigger-http \
  --allow-unauthenticated \
  --source=${TEMP_DIR} \
  --set-env-vars=PROJECT_ID=${PROJECT_ID},REGION=${REGION}

# Clean up
rm -rf ${TEMP_DIR}

echo
echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${YELLOW}Function URL: https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}${NC}"
echo -e "${YELLOW}To trigger IP rotation manually:${NC}"
echo -e "curl https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
echo
echo -e "${YELLOW}To trigger IP rotation with old IP release:${NC}"
echo -e "curl -X POST -H \"Content-Type: application/json\" -d '{\"release_old_ip\": true}' https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
echo
echo -e "${YELLOW}To release a specific IP:${NC}"
echo -e "curl -X POST -H \"Content-Type: application/json\" -d '{\"action\": \"release\", \"ip_name\": \"YOUR_IP_NAME\"}' https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}" 