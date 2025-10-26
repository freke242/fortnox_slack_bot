#!/bin/bash
# Sync Fortnox tokens from Railway PostgreSQL database to local file
#
# This script pulls the latest tokens from production database (read-only)
# and stores them locally in fortnox_tokens.json for development.
#
# Prerequisites:
# - DATABASE_URL_RO in .env or .env.development (readonly connection string)
# - psycopg2-binary installed in venv

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TOKEN_FILE="${PROJECT_ROOT}/fortnox_tokens.json"

echo "🔄 Syncing Fortnox tokens from database..."
echo ""

# Check for DATABASE_URL_RO
if [ -f "${PROJECT_ROOT}/.env.development" ]; then
    source "${PROJECT_ROOT}/.env.development"
fi

if [ -z "$DATABASE_URL_RO" ]; then
    echo "❌ DATABASE_URL_RO not found in environment"
    echo ""
    echo "Please add DATABASE_URL_RO to your .env.development file"
    echo "Get the readonly connection string from:"
    echo "  railway run --service production python3 scripts/setup_db_readonly_role.py"
    echo ""
    exit 1
fi

# Run Python script to fetch and save tokens
"${PROJECT_ROOT}/venv/bin/python3" << 'EOF'
import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    logger.error("psycopg2 not installed in venv")
    logger.error("Run: ./venv/bin/pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL_RO = os.getenv('DATABASE_URL_RO')
if not DATABASE_URL_RO:
    logger.error("DATABASE_URL_RO not found")
    sys.exit(1)

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL_RO)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Fetch tokens
    cur.execute("""
        SELECT access_token, refresh_token, updated_at
        FROM fortnox_tokens 
        WHERE id = 1
    """)
    row = cur.fetchone()
    
    if not row:
        logger.error("No tokens found in database")
        logger.error("Production must initialize tokens first")
        sys.exit(1)
    
    # Save to local file
    tokens = {
        'access_token': row['access_token'],
        'refresh_token': row['refresh_token']
    }
    
    with open('fortnox_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2)
    
    logger.info(f"✅ Tokens synced to fortnox_tokens.json")
    logger.info(f"   Last updated: {row['updated_at']}")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    logger.error(f"Database connection failed: {e}")
    logger.error("Check that DATABASE_URL_RO is correct")
    sys.exit(1)
except Exception as e:
    logger.error(f"Failed to sync tokens: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Token sync complete!"
    echo "   You can now run the bot locally with fresh tokens"
else
    echo ""
    echo "❌ Token sync failed"
    exit 1
fi
