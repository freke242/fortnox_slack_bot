#!/usr/bin/env python3
"""
Setup Read-Only Database Role for Staging/Local Environments

This script creates a read-only PostgreSQL role and generates a connection string
for staging and local development environments.

Run this ONCE from production Railway environment after PostgreSQL is added.
"""
import os
import sys
import secrets
import logging
from urllib.parse import urlparse, urlunparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_database_url(url: str) -> dict:
    """Parse DATABASE_URL into components"""
    parsed = urlparse(url)
    return {
        'scheme': parsed.scheme,
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/')
    }

def create_readonly_role():
    """Create read-only role in PostgreSQL"""
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        logger.error("This script must be run from Railway production environment")
        return False
    
    # Parse connection details
    db_info = parse_database_url(database_url)
    
    # Generate secure password for readonly user
    readonly_password = secrets.token_urlsafe(32)
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        logger.info("Creating read-only role...")
        
        # Create readonly role
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fortnox_readonly') THEN
                    CREATE ROLE fortnox_readonly WITH LOGIN PASSWORD %s;
                END IF;
            END
            $$;
        """, (readonly_password,))
        
        # Grant connect permission
        cur.execute(f"""
            GRANT CONNECT ON DATABASE {db_info['database']} TO fortnox_readonly;
        """)
        
        # Grant usage on schema
        cur.execute("""
            GRANT USAGE ON SCHEMA public TO fortnox_readonly;
        """)
        
        # Grant select on all existing tables
        cur.execute("""
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO fortnox_readonly;
        """)
        
        # Grant select on future tables (default privileges)
        cur.execute("""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public 
            GRANT SELECT ON TABLES TO fortnox_readonly;
        """)
        
        cur.close()
        conn.close()
        
        logger.info("✅ Read-only role created successfully!")
        logger.info("")
        logger.info("=" * 70)
        logger.info("📋 READONLY DATABASE CONNECTION STRING")
        logger.info("=" * 70)
        
        # Generate readonly connection string
        readonly_url = urlunparse((
            db_info['scheme'],
            f"fortnox_readonly:{readonly_password}@{db_info['host']}:{db_info['port']}",
            f"/{db_info['database']}",
            '', '', ''
        ))
        
        logger.info("")
        logger.info("Add this to your Railway STAGING service environment variables:")
        logger.info("")
        logger.info(f"DATABASE_URL={readonly_url}")
        logger.info("TOKEN_STORAGE_READONLY=true")
        logger.info("ENVIRONMENT=staging")
        logger.info("")
        logger.info("=" * 70)
        logger.info("🔐 LOCAL DEVELOPMENT SETUP")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Add this to your local .env.development file:")
        logger.info("")
        logger.info(f"DATABASE_URL_RO={readonly_url}")
        logger.info("")
        logger.info("Then use scripts/sync_tokens_from_db.sh to pull tokens locally")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create read-only role: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Setting up read-only database role...")
    logger.info("")
    
    # Check if running in Railway
    if not os.getenv('RAILWAY_ENVIRONMENT'):
        logger.warning("⚠️  Not running in Railway environment")
        logger.warning("   This script should be run via: railway run --service production python3 scripts/setup_db_readonly_role.py")
        logger.warning("")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Aborted.")
            sys.exit(0)
    
    success = create_readonly_role()
    sys.exit(0 if success else 1)
