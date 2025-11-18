#!/bin/bash
#
# Example bash script for using the Presentation Intelligence Tool API
# Demonstrates API calls using curl and jq for JSON processing
#

set -e  # Exit on error

API_BASE_URL="http://localhost:5000/api/v1"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Presentation Intelligence Tool - API Example (Bash)"
echo "=================================================="
echo

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed.${NC}"
    echo "Install with: sudo apt install jq (Ubuntu/Debian) or brew install jq (macOS)"
    exit 1
fi

# 1. Get available prompt templates
echo -e "${BLUE}1. Fetching available prompt templates...${NC}"
PROMPTS=$(curl -s "${API_BASE_URL}/prompts")

if [ $? -eq 0 ]; then
    echo "$PROMPTS" | jq -r '.prompts[] | "   - \(.id): \(.name)\n     \(.description)"'
else
    echo -e "${RED}   Failed to fetch prompts${NC}"
    exit 1
fi

echo

# 2. Submit analysis request
echo -e "${BLUE}2. Submitting analysis request...${NC}"

# Create request JSON
REQUEST_JSON=$(cat <<EOF
{
  "title": "Python Network Automation Workshop",
  "presenters": "Network Team",
  "notes": "Comprehensive workshop on automating network operations with Python. Covered Netmiko, NAPALM, and Ansible basics.",
  "resource_urls": [
    "https://raw.githubusercontent.com/ktbyers/netmiko/develop/README.md"
  ],
  "github_url": "https://github.com/ktbyers/netmiko",
  "prompt_template": "network_engineer"
}
EOF
)

echo "   Title: $(echo "$REQUEST_JSON" | jq -r '.title')"
echo "   Template: $(echo "$REQUEST_JSON" | jq -r '.prompt_template')"
echo "   Resources: $(echo "$REQUEST_JSON" | jq -r '.resource_urls | length') URL(s)"

# Submit the request
RESPONSE=$(curl -s -X POST "${API_BASE_URL}/analyze" \
  -H "Content-Type: application/json" \
  -d "$REQUEST_JSON")

if [ $? -ne 0 ]; then
    echo -e "${RED}   API request failed${NC}"
    exit 1
fi

echo

# 3. Handle response
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

if [ "$SUCCESS" = "true" ]; then
    echo -e "${GREEN}3. Analysis completed successfully!${NC}"

    # Extract metadata
    RESOURCES_FETCHED=$(echo "$RESPONSE" | jq -r '.metadata.resources_fetched')
    DATE=$(echo "$RESPONSE" | jq -r '.metadata.date')
    TEMPLATE=$(echo "$RESPONSE" | jq -r '.metadata.prompt_template')

    echo "   Resources fetched: $RESOURCES_FETCHED"
    echo "   Date: $DATE"
    echo "   Template used: $TEMPLATE"

    # Check for warnings
    HAS_WARNINGS=$(echo "$RESPONSE" | jq 'has("warnings")')
    if [ "$HAS_WARNINGS" = "true" ]; then
        WARNING_MSG=$(echo "$RESPONSE" | jq -r '.warnings.message')
        echo -e "${RED}   Warning: $WARNING_MSG${NC}"
    fi

    # Save analysis to file
    OUTPUT_FILE="bash_example_analysis.md"
    echo "$RESPONSE" | jq -r '.analysis' > "$OUTPUT_FILE"
    echo
    echo -e "${GREEN}   Analysis saved to: $OUTPUT_FILE${NC}"

    # Print first 500 characters
    echo
    echo "   Analysis preview:"
    echo "   ------------------------------------------------------------"
    head -c 500 "$OUTPUT_FILE" | sed 's/^/   /'
    echo "..."
    echo "   ------------------------------------------------------------"

else
    ERROR=$(echo "$RESPONSE" | jq -r '.error')
    echo -e "${RED}3. Analysis failed!${NC}"
    echo -e "${RED}   Error: $ERROR${NC}"
    exit 1
fi

echo
echo -e "${GREEN}Done!${NC}"
