#!/bin/bash
# Sync Fortnox tokens from Railway production volume to local file
#
# This script fetches fortnox_tokens.json from the production Railway volume
# (persisted across deploys) and saves it locally for development.
#
# Setup (ONE TIME):
# 1. In Railway dashboard → Production service → Settings
# 2. Add a Volume: Mount path = /data
# 3. Redeploy production (tokens will be saved to volume after next refresh)
#
# Prerequisites:
# - Railway CLI installed and linked

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TOKEN_FILE="${PROJECT_ROOT}/fortnox_tokens.json"

echo "🔄 Syncing Fortnox tokens from Railway production volume..."
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

# Fetch tokens from Railway volume
TOKENS_JSON=$(railway run --service production cat /data/fortnox_tokens.json 2>/tmp/railway_err)

if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch tokens from Railway volume"
    echo ""
    if [ -f /tmp/railway_err ]; then
        cat /tmp/railway_err
        rm -f /tmp/railway_err
    fi
    echo ""
    echo "Make sure:"
    echo "  1. Railway volume is added to production (/data mount path)"
    echo "  2. Production has run at least once to save tokens"
    echo "  3. You're logged in: railway login && railway link"
    exit 1
fi
rm -f /tmp/railway_err

if [ -z "$TOKENS_JSON" ]; then
    echo "❌ Token file is empty on production volume"
    echo "   Wait for production to refresh tokens, then try again"
    exit 1
fi

# Validate JSON
REFRESH_TOKEN=$(echo "$TOKENS_JSON" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('refresh_token',''))" 2>/dev/null)

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

