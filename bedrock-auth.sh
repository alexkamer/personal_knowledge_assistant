#!/bin/bash

# bedrock-auth.sh - Fetch and export AWS Bedrock environment variables

USERID="${1:-atiaide}"  # Default to 'atiaide' if no argument provided
REGION="${2:-us-east-2}" # Default to 'us-east-2' if no argument provided

# Make the API call and capture the response
RESPONSE=$(curl -s -X 'POST' \
  'https://tokengen.aide.infra-host.com/api/generate-token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d "{
  \"userid\": \"$USERID\",
  \"region\": \"$REGION\"
}")

# Check if the request was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to fetch token" >&2
    exit 1
fi

# Extract the export statements using jq
# If jq is not installed, we'll use a fallback method
if command -v jq &> /dev/null; then
    # Using jq (preferred method)
    EXPORTS=$(echo "$RESPONSE" | jq -r '.data.export_statements.linux_mac[]')

    if [ -z "$EXPORTS" ]; then
        echo "Error: Failed to parse response" >&2
        echo "Response: $RESPONSE" >&2
        exit 1
    fi

    EXPIRATION=$(echo "$RESPONSE" | jq -r '.data.expiration')

    echo "$EXPORTS"
    echo "# Token expires at: $EXPIRATION" >&2
else
    # Fallback: parse JSON manually (less robust)
    echo "$RESPONSE" | sed -n '/"linux_mac":/,/]/p' | \
        grep -o '"export [^"]*"' | \
        sed 's/"//g'

    echo "# Tip: Install jq for better JSON parsing and expiration info" >&2
fi
