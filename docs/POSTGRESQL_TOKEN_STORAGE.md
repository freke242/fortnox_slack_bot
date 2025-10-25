# PostgreSQL Token Storage Migration Guide

## 📋 Overview

This document describes how to migrate from file-based token storage to PostgreSQL-based shared token storage across all environments.

### **Why PostgreSQL?**

- ✅ **Shared state** - Production and staging share the same tokens
- ✅ **No token conflicts** - Single source of truth
- ✅ **Railway native** - Free PostgreSQL tier included
- ✅ **Local dev friendly** - Falls back to file storage when DB not available
- ✅ **Automatic sync** - All environments always have latest tokens

### **Current State**

```
Environment          Token Storage
------------------   --------------------------
Production (Railway) → /data/fortnox_tokens.json (Railway volume)
Staging (Railway)    → /data/fortnox_tokens.json (Railway volume)
Local Development    → ./fortnox_tokens.json (local file)
```

**Problem:** Each environment has separate token files, leading to occasional conflicts when Fortnox rotates refresh tokens.

### **Target State**

```
Environment          Token Storage
------------------   --------------------------
Production (Railway) → PostgreSQL database (shared)
Staging (Railway)    → PostgreSQL database (shared)
Local Development    → ./fortnox_tokens.json (fallback to file)
```

**Benefit:** Production and staging always share the same tokens. Local dev can sync when needed.

---

## 🚀 Implementation Steps

### **Step 1: Add PostgreSQL to Railway**

1. Go to Railway dashboard: https://railway.app/dashboard
2. Select your Fortnox Slack Bot project
3. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
4. Railway creates a PostgreSQL instance
5. Railway automatically adds `DATABASE_URL` to both services

**Expected Result:**
- Database service appears in project
- Both `production` and `staging` services get `DATABASE_URL` env var
- Format: `postgresql://user:pass@host:port/dbname`

### **Step 2: Update Dependencies**

Add PostgreSQL driver to `requirements.txt`:

```txt
# Add after existing dependencies
psycopg2-binary==2.9.9
```

Commit and push:
```bash
git add requirements.txt
git commit -m "Add PostgreSQL dependency for shared token storage"
git push origin main
```

### **Step 3: Update Token Manager**

Replace `src/token_manager.py` with the new implementation:

**Key Changes:**
- Detect `DATABASE_URL` environment variable
- Use PostgreSQL when available (Railway production/staging)
- Fall back to file storage when not available (local development)
- Automatic table creation on first run
- Thread-safe database operations

**File: `src/token_manager.py`**

```python
"""
Token Manager - Handles Fortnox token storage
Supports both PostgreSQL (Railway) and file-based (local) storage
"""
import os
import json
import threading
import logging
from contextlib import contextmanager
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
USE_DATABASE = DATABASE_URL is not None

# File configuration
TOKEN_FILE = os.getenv('TOKEN_FILE', 'fortnox_tokens.json')

# Import PostgreSQL driver only if database is configured
if USE_DATABASE:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        logger.warning("psycopg2 not installed, falling back to file storage")
        USE_DATABASE = False


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    if not USE_DATABASE:
        raise RuntimeError("Database not configured")
    
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


class TokenManager:
    """
    Manages Fortnox OAuth tokens with support for both database and file storage
    
    Storage Strategy:
    - Railway (production/staging): PostgreSQL database (shared)
    - Local development: JSON file
    
    Thread Safety:
    - Database: PostgreSQL handles concurrency
    - File: Uses threading.Lock for file operations
    """
    
    def __init__(self):
        self.file_lock = threading.Lock()
        self.storage_type = "database" if USE_DATABASE else "file"
        
        logger.info(f"TokenManager initialized with {self.storage_type} storage")
        
        if USE_DATABASE:
            self._init_database()
    
    def _init_database(self):
        """Create tokens table if it doesn't exist"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS fortnox_tokens (
                            id INTEGER PRIMARY KEY DEFAULT 1,
                            access_token TEXT NOT NULL,
                            refresh_token TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT single_row CHECK (id = 1)
                        );
                        
                        -- Create index for faster lookups
                        CREATE INDEX IF NOT EXISTS idx_tokens_updated 
                        ON fortnox_tokens(updated_at DESC);
                    """)
            logger.info("Database table initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def read_tokens(self) -> Optional[Dict[str, str]]:
        """
        Read tokens from storage
        
        Returns:
            dict with 'access_token' and 'refresh_token' keys, or None if not found
        """
        if USE_DATABASE:
            return self._read_from_db()
        else:
            return self._read_from_file()
    
    def _read_from_db(self) -> Optional[Dict[str, str]]:
        """Read tokens from PostgreSQL database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT access_token, refresh_token, updated_at
                        FROM fortnox_tokens 
                        WHERE id = 1
                    """)
                    row = cur.fetchone()
                    
                    if row:
                        logger.info(f"Tokens read from database (updated: {row['updated_at']})")
                        return {
                            'access_token': row['access_token'],
                            'refresh_token': row['refresh_token']
                        }
                    else:
                        logger.warning("No tokens found in database")
                        return None
        except Exception as e:
            logger.error(f"Failed to read tokens from database: {e}")
            return None
    
    def _read_from_file(self) -> Optional[Dict[str, str]]:
        """Read tokens from JSON file (local development)"""
        with self.file_lock:
            try:
                if not os.path.exists(TOKEN_FILE):
                    logger.warning(f"Token file not found: {TOKEN_FILE}")
                    return None
                
                with open(TOKEN_FILE, 'r') as f:
                    tokens = json.load(f)
                    logger.info(f"Tokens read from file: {TOKEN_FILE}")
                    return tokens
            except Exception as e:
                logger.error(f"Failed to read tokens from file: {e}")
                return None
    
    def write_tokens(self, access_token: str, refresh_token: str) -> bool:
        """
        Write tokens to storage
        
        Args:
            access_token: Fortnox access token
            refresh_token: Fortnox refresh token
            
        Returns:
            True if successful, False otherwise
        """
        if USE_DATABASE:
            return self._write_to_db(access_token, refresh_token)
        else:
            return self._write_to_file(access_token, refresh_token)
    
    def _write_to_db(self, access_token: str, refresh_token: str) -> bool:
        """Write tokens to PostgreSQL database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO fortnox_tokens (id, access_token, refresh_token)
                        VALUES (1, %s, %s)
                        ON CONFLICT (id) 
                        DO UPDATE SET 
                            access_token = EXCLUDED.access_token,
                            refresh_token = EXCLUDED.refresh_token,
                            updated_at = CURRENT_TIMESTAMP
                    """, (access_token, refresh_token))
            
            logger.info("Tokens written to database successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to write tokens to database: {e}")
            return False
    
    def _write_to_file(self, access_token: str, refresh_token: str) -> bool:
        """Write tokens to JSON file (local development)"""
        with self.file_lock:
            try:
                tokens = {
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
                
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(tokens, f, indent=2)
                
                logger.info(f"Tokens written to file: {TOKEN_FILE}")
                return True
            except Exception as e:
                logger.error(f"Failed to write tokens to file: {e}")
                return False
    
    def migrate_from_env(self, access_token: str, refresh_token: str) -> bool:
        """
        Migrate tokens from environment variables to storage
        
        Args:
            access_token: Token from FORTNOX_ACCESS_TOKEN env var
            refresh_token: Token from FORTNOX_REFRESH_TOKEN env var
            
        Returns:
            True if migration successful
        """
        logger.info(f"Migrating tokens from environment to {self.storage_type}")
        return self.write_tokens(access_token, refresh_token)
    
    def get_storage_info(self) -> Dict[str, str]:
        """Get information about current storage configuration"""
        info = {
            'storage_type': self.storage_type,
            'environment': os.getenv('ENVIRONMENT', 'unknown')
        }
        
        if USE_DATABASE:
            info['database_url'] = DATABASE_URL[:30] + '...' if DATABASE_URL else 'None'
        else:
            info['token_file'] = TOKEN_FILE
        
        return info
```

Commit changes:
```bash
git add src/token_manager.py
git commit -m "Implement PostgreSQL token storage with file fallback"
git push origin main
```

### **Step 4: Migrate Existing Tokens**

After deployment, initialize the database with current tokens:

**Option A: Via Railway CLI**
```bash
# Link to production service
railway link

# Run migration script
railway run --service production python3 << 'EOF'
from src.token_manager import TokenManager
import os

tm = TokenManager()

# Get tokens from environment variables (your current setup)
access_token = os.getenv('FORTNOX_ACCESS_TOKEN')
refresh_token = os.getenv('FORTNOX_REFRESH_TOKEN')

if access_token and refresh_token:
    success = tm.write_tokens(access_token, refresh_token)
    if success:
        print("✅ Tokens migrated to database successfully")
        print(f"Storage info: {tm.get_storage_info()}")
    else:
        print("❌ Migration failed")
else:
    print("❌ Tokens not found in environment variables")
EOF
```

**Option B: Via Railway Dashboard**
1. Go to production service
2. Click **"Deploy"** → **"Run a Command"**
3. Paste the migration script above

**Expected Output:**
```
✅ Tokens migrated to database successfully
Storage info: {'storage_type': 'database', 'environment': 'production', 'database_url': 'postgresql://...'}
```

### **Step 5: Verify Database**

Check that tokens are in the database:

```bash
railway run --service production python3 << 'EOF'
from src.token_manager import TokenManager

tm = TokenManager()
tokens = tm.read_tokens()

if tokens:
    print("✅ Tokens found in database")
    print(f"Access token: {tokens['access_token'][:20]}...")
    print(f"Refresh token: {tokens['refresh_token'][:20]}...")
else:
    print("❌ No tokens in database")
EOF
```

### **Step 6: Remove Old Environment Variables (Optional)**

Once tokens are in the database, you can remove them from Railway env vars:

1. Go to Railway dashboard
2. Production service → Variables
3. **Keep for fallback:** `FORTNOX_CLIENT_SECRET`
4. **Optional to remove:** `FORTNOX_ACCESS_TOKEN`, `FORTNOX_REFRESH_TOKEN`

**Note:** Your code has fallback logic, so keeping them as backup is fine.

---

## 🔧 Environment-Specific Behavior

### **Production Environment (Railway)**

**Configuration:**
```bash
# Railway environment variables
DATABASE_URL=postgresql://...  # Auto-injected by Railway
FORTNOX_CLIENT_SECRET=...
SLACK_BOT_TOKEN=xoxb-production...
SLACK_APP_TOKEN=xapp-production...
ENVIRONMENT=production
```

**Token Storage:** PostgreSQL database (shared with staging)

**Behavior:**
- Reads tokens from database
- Writes refreshed tokens to database
- Staging service sees updates immediately
- No file storage used

### **Staging Environment (Railway)**

**Configuration:**
```bash
# Railway environment variables
DATABASE_URL=postgresql://...  # Same database as production
FORTNOX_CLIENT_SECRET=...
SLACK_BOT_TOKEN=xoxb-dev...
SLACK_APP_TOKEN=xapp-dev...
ENVIRONMENT=staging
```

**Token Storage:** PostgreSQL database (shared with production)

**Behavior:**
- Reads tokens from same database as production
- Can refresh tokens (writes to shared database)
- Production service sees updates immediately
- No file storage used

### **Local Development**

**Configuration:**
```bash
# .env.development (no DATABASE_URL)
FORTNOX_ACCESS_TOKEN=...  # Fallback only
FORTNOX_REFRESH_TOKEN=... # Fallback only
FORTNOX_CLIENT_SECRET=...
SLACK_BOT_TOKEN=xoxb-dev...
SLACK_APP_TOKEN=xapp-dev...
ENVIRONMENT=development
```

**Token Storage:** Local file `./fortnox_tokens.json`

**Behavior:**
- Uses file storage (no database connection)
- Reads from `fortnox_tokens.json`
- Writes refreshed tokens to local file
- Independent from production/staging tokens

**Syncing Tokens for Local Dev:**

When you need fresh tokens locally:

```bash
# Method 1: Download from database via Railway CLI
railway link
railway run --service production python3 << 'EOF'
from src.token_manager import TokenManager
import json

tm = TokenManager()
tokens = tm.read_tokens()

with open('fortnox_tokens.json', 'w') as f:
    json.dump(tokens, f, indent=2)

print("✅ Tokens downloaded to fortnox_tokens.json")
EOF

# Method 2: Use script (create this)
./scripts/sync_tokens_from_railway.sh
```

---

## 📝 Migration Checklist

- [ ] **Step 1:** Add PostgreSQL database to Railway project
- [ ] **Step 2:** Update `requirements.txt` with `psycopg2-binary`
- [ ] **Step 3:** Replace `src/token_manager.py` with new implementation
- [ ] **Step 4:** Deploy to Railway (push to main branch)
- [ ] **Step 5:** Migrate existing tokens to database
- [ ] **Step 6:** Verify tokens in database
- [ ] **Step 7:** Test production bot (should work with database tokens)
- [ ] **Step 8:** Test staging bot (should share tokens with production)
- [ ] **Step 9:** Download tokens for local development
- [ ] **Step 10:** Test local bot (should use file storage)
- [ ] **Step 11:** (Optional) Remove token env vars from Railway
- [ ] **Step 12:** Update documentation

---

## 🧪 Testing Plan

### **Test 1: Production Uses Database**
```bash
railway logs --service production | grep "TokenManager"
# Expected: "TokenManager initialized with database storage"
# Expected: "Tokens read from database"
```

### **Test 2: Staging Uses Same Database**
```bash
railway logs --service staging | grep "TokenManager"
# Expected: "TokenManager initialized with database storage"
# Expected: "Tokens read from database"
```

### **Test 3: Local Uses File**
```bash
./venv/bin/python -m src.bot
# Check logs for: "TokenManager initialized with file storage"
# Check logs for: "Tokens read from file: fortnox_tokens.json"
```

### **Test 4: Token Refresh Syncs Across Environments**
1. Trigger token refresh in production (wait for auto-refresh or force)
2. Check staging logs - should see updated tokens immediately
3. Verify both services show same `updated_at` timestamp

### **Test 5: Local Development Independence**
1. Refresh tokens locally
2. Check production database - should remain unchanged
3. Verify local file was updated

---

## 🛠️ Helper Scripts

Create these scripts to make token management easier:

### **`scripts/sync_tokens_from_railway.sh`**
```bash
#!/bin/bash
# Download tokens from Railway production database to local file

set -e

echo "🔄 Syncing tokens from Railway production..."

railway link --service production 2>/dev/null || echo "Already linked"

railway run python3 << 'EOF'
from src.token_manager import TokenManager
import json

tm = TokenManager()
tokens = tm.read_tokens()

if tokens:
    with open('fortnox_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2)
    print("✅ Tokens synced to fortnox_tokens.json")
else:
    print("❌ No tokens found in database")
    exit(1)
EOF

echo "✅ Sync complete!"
```

Make it executable:
```bash
chmod +x scripts/sync_tokens_from_railway.sh
```

### **`scripts/check_token_storage.sh`**
```bash
#!/bin/bash
# Check token storage configuration across all environments

echo "=== Production Token Storage ==="
railway run --service production python3 << 'EOF'
from src.token_manager import TokenManager
tm = TokenManager()
info = tm.get_storage_info()
print(f"Type: {info['storage_type']}")
print(f"Environment: {info['environment']}")
if 'database_url' in info:
    print(f"Database: {info['database_url']}")
EOF

echo ""
echo "=== Staging Token Storage ==="
railway run --service staging python3 << 'EOF'
from src.token_manager import TokenManager
tm = TokenManager()
info = tm.get_storage_info()
print(f"Type: {info['storage_type']}")
print(f"Environment: {info['environment']}")
if 'database_url' in info:
    print(f"Database: {info['database_url']}")
EOF

echo ""
echo "=== Local Token Storage ==="
./venv/bin/python << 'EOF'
from src.token_manager import TokenManager
import sys
tm = TokenManager()
info = tm.get_storage_info()
print(f"Type: {info['storage_type']}")
print(f"Environment: {info['environment']}")
if 'token_file' in info:
    print(f"File: {info['token_file']}")
EOF
```

Make it executable:
```bash
chmod +x scripts/check_token_storage.sh
```

---

## 🚨 Rollback Plan

If something goes wrong, you can revert to file-based storage:

1. **Revert code:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Railway will auto-deploy previous version**

3. **Token files are still on Railway volumes** (not deleted)

4. **Fallback to env vars** still works (env vars weren't deleted)

---

## 📊 Benefits After Migration

✅ **No more token conflicts** - Single source of truth  
✅ **Instant synchronization** - Production and staging always in sync  
✅ **Simpler debugging** - One place to check tokens  
✅ **Better monitoring** - Database has `updated_at` timestamps  
✅ **Local dev stays simple** - Still uses files  
✅ **Production-ready** - Railway-native solution  

---

## 📚 Additional Resources

- **Railway PostgreSQL Docs:** https://docs.railway.app/databases/postgresql
- **psycopg2 Documentation:** https://www.psycopg.org/docs/
- **Fortnox OAuth Docs:** https://developer.fortnox.se/general/authentication/

---

## 💡 Future Improvements

Once PostgreSQL is working, consider:

1. **Token expiration tracking** - Store token expiry times
2. **Audit log** - Track when tokens were refreshed and by which service
3. **Health endpoint** - Expose token age for monitoring
4. **Automatic token download** - Git hook to sync tokens on checkout

---

**Last Updated:** 2025-10-25  
**Status:** 📝 Planning - Not yet implemented  
**Estimated Time:** 1-2 hours total implementation + testing
