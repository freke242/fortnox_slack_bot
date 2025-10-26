#!/bin/bash
# Sync Fortnox tokens from Railway production database to local file
#
# This script pulls the latest tokens from production database via Railway CLI
# and stores them locally in fortnox_tokens.json for development.
#
# Prerequisites:
# - Railway CLI installed: https://docs.railway.app/develop/cli
# - Logged in: railway login
# - Linked to project: railway link

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TOKEN_FILE="${PROJECT_ROOT}/fortnox_tokens.json"

echo "🔄 Syncing Fortnox tokens from Railway production..."
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

# Run command via Railway CLI to fetch tokens from production database
railway run --service production python3 << 'EOF'
import sys
import json

# Add src to path so we can import TokenManager
sys.path.insert(0, '/app/src')

try:
    from token_manager import TokenManager
    
    tm = TokenManager()
    tokens = tm.load_tokens()
    
    if tokens:
        # Output as JSON to stdout
        print(json.dumps(tokens, indent=2))
    else:
        print("ERROR: No tokens found in database", file=sys.stderr)
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF

# Capture the output
if [ $? -eq 0 ]; then
    # Save the last command output to file
    railway run --service production python3 << 'EOF' > "$TOKEN_FILE"
import sys
import json
sys.path.insert(0, '/app/src')
from token_manager import TokenManager
tm = TokenManager()
tokens = tm.load_tokens()
if tokens:
    print(json.dumps(tokens, indent=2))
else:
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Token sync complete!"
        echo "   Saved to: ${TOKEN_FILE}"
        echo "   You can now run the bot locally with fresh tokens"
    else
        echo ""
        echo "❌ Token sync failed"
        exit 1
    fi
else
    echo ""
    echo "❌ Failed to connect to Railway production"
    echo "   Make sure you're logged in: railway login"
    echo "   And linked to project: railway link"
    exit 1
fi
