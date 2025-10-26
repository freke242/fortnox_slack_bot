#!/bin/bash
# Sync Fortnox tokens from Railway production to local file
#
# This script uses `railway ssh` to cat the persisted fortnox_tokens.json file
# from the production service volume and saves it locally for development.
#
# Prerequisites:
# - Railway CLI installed and linked (`railway login`, `railway link`)
# - Production service mounted volume at /data containing fortnox_tokens.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TOKEN_FILE="${PROJECT_ROOT}/fortnox_tokens.json"
LOCAL_PYTHON="${PROJECT_ROOT}/venv/bin/python3"

echo "🔄 Fetching Fortnox tokens from Railway production..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found"
    echo ""
    echo "Install it first:"
    echo "  npm i -g @railway/cli"
    echo "  OR"
    echo "  curl -fsSL https://railway.app/install.sh | sh"
    echo ""
    exit 1
fi

TOKENS_JSON=""
REMOTE_PATH="/data/fortnox_tokens.json"
TMP_ERR="$(mktemp)"

if ! TOKENS_JSON=$(railway ssh --service production -- cat "$REMOTE_PATH" 2>"$TMP_ERR"); then
    echo "❌ Failed to retrieve tokens from Railway production"
    echo ""
    cat "$TMP_ERR"
    rm -f "$TMP_ERR"
    exit 1
fi
rm -f "$TMP_ERR"

if [ -z "$TOKENS_JSON" ]; then
    echo "❌ Failed to retrieve tokens from Railway production"
    exit 1
fi

# Ensure local Python is available for JSON parsing (prefer project venv)
if [ ! -x "$LOCAL_PYTHON" ]; then
    if command -v python3 &> /dev/null; then
        LOCAL_PYTHON="python3"
    else
        echo "❌ Python 3 not found"
        echo "   Run: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
        exit 1
    fi
fi

# Validate JSON
REFRESH_TOKEN=$(echo "$TOKENS_JSON" | "$LOCAL_PYTHON" -c "import sys, json; data=json.load(sys.stdin); print(data.get('refresh_token',''))" 2>/dev/null)

if [ -z "$REFRESH_TOKEN" ]; then
    echo "❌ Invalid token format from production"
    exit 1
fi

# Save to local file
echo "$TOKENS_JSON" > "$TOKEN_FILE"

echo "✅ Token sync complete!"
echo "   Saved to: ${TOKEN_FILE}"
echo "   Refresh token ends with: ...${REFRESH_TOKEN: -3}"
echo "   You can now run the bot locally with fresh tokens"

