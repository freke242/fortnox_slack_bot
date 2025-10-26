# PostgreSQL Token Storage Implementation Guide

## 📋 Overview

This document describes the PostgreSQL-based token storage implementation for the Fortnox Slack Bot across production, staging, and local development environments.

### **Why PostgreSQL?**

- ✅ **Shared state** - Production manages tokens, staging/local consume them
- ✅ **No token conflicts** - Single source of truth with read-only consumers
- ✅ **Railway native** - Free PostgreSQL tier included
- ✅ **Local dev friendly** - Syncs tokens from database to local file
- ✅ **Automatic refresh** - Only production refreshes tokens

### **Architecture**

```
Environment                 Token Storage Mode         Slack Workspace
--------------------------  -------------------------  ------------------
Production (Railway main)   PostgreSQL (read/write)    Production
Staging (Railway staging)   PostgreSQL (read-only)     Testing/Dev
Local Development           File + DB sync (read-only) Testing/Dev
```

**Key Design:**
- **Production**: Only environment that writes tokens (manages refresh)
- **Staging**: Reads from same database, separate Slack workspace
- **Local**: Syncs tokens from database to local file for development

---

## 🚀 Implementation Steps

### **Step 1: Update Dependencies**

PostgreSQL driver `psycopg2-binary==2.9.9` has been added to `requirements.txt`.

```bash
git add requirements.txt
git commit -m "Add PostgreSQL dependency for shared token storage"
git push origin main
```

### **Step 2: Update Code**

The `src/token_manager.py` has been updated to support:
- PostgreSQL database storage (when `DATABASE_URL` is set)
- Read-only mode (when `TOKEN_STORAGE_READONLY=true`)
- File-based fallback (when no `DATABASE_URL`)

```bash
git add src/token_manager.py
git commit -m "Implement PostgreSQL token storage with read-only mode"
git push origin main
```

### **Step 3: Add PostgreSQL to Railway**

1. Go to Railway dashboard: https://railway.app/dashboard
2. Select your Fortnox Slack Bot **production** project
3. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
4. Railway creates a PostgreSQL instance
5. Railway automatically adds `DATABASE_URL` to the **production** service

**Expected Result:**
- Database service appears in project  
- Production service gets `DATABASE_URL` environment variable
- Format: `postgresql://user:pass@host:port/dbname`

### **Step 4: Configure Staging Service**

Staging uses the **same database** as production but with application-level read-only protection.

No separate database user needed - the `TOKEN_STORAGE_READONLY` flag prevents writes.

### **Step 5: Configure Production Environment**

In Railway dashboard, **production service** → Variables, ensure these are set:

```bash
# Database (auto-injected by Railway when you add PostgreSQL)
DATABASE_URL=postgresql://... # Read/write access

# Environment identification
ENVIRONMENT=production

# Fortnox credentials (already exist)
FORTNOX_CLIENT_ID=...
FORTNOX_CLIENT_SECRET=...
FORTNOX_ACCESS_TOKEN=...  # Used for initial database seed
FORTNOX_REFRESH_TOKEN=... # Used for initial database seed

# Slack credentials - PRODUCTION WORKSPACE
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
```

**Deploy to production:**
```bash
git push origin main
```

Railway will auto-deploy. Check logs for:
```
TokenManager initialized: database storage (read/write)
✅ Database table initialized successfully
✅ Tokens read from database
```

### **Step 6: Configure Staging Environment**

Create a **second service in the same Railway project** that deploys from `staging` branch.

1. **In Railway dashboard** → Your project → Click **"New"** → **"Service"** → **"GitHub Repo"**
2. Select your repo and configure:
   - **Branch**: `staging` (not main)
   - **Name**: e.g., "fortnox-bot-staging"

3. **Configure environment variables** in staging service → Variables:

```bash
# Database - Reference the same PostgreSQL service
# Use "Add Reference" → Select PostgreSQL → DATABASE_URL
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Same as production

# Read-only mode - CRITICAL!
TOKEN_STORAGE_READONLY=true  # Prevents writing to database

# Environment identification
ENVIRONMENT=staging

# Fortnox credentials (same as production)
FORTNOX_CLIENT_ID=...
FORTNOX_CLIENT_SECRET=...

# Slack credentials - TESTING/DEV WORKSPACE (different from production!)
SLACK_BOT_TOKEN=xoxb-[staging-token]...
SLACK_SIGNING_SECRET=[staging-secret]...
SLACK_APP_TOKEN=xapp-[staging-token]...
```

4. **Create and push staging branch:**
```bash
git checkout -b staging
git push origin staging
```

Check staging logs for:
```
TokenManager initialized: database storage (read-only)
✅ Tokens read from database (updated: ...)
⚠️  Token storage is READ-ONLY - save_tokens() skipped
```

### **Step 7: Configure Local Development**

Local development uses file-based storage with sync from production database.

**1. Install Railway CLI (if not already installed):**
```bash
# Via npm
npm i -g @railway/cli

# OR via shell
curl -fsSL https://railway.app/install.sh | sh

# Login
railway login

# Link to your project
railway link
```

**2. Create `.env` file** (or `.env.development`):

```bash
# No DATABASE_URL needed locally - uses file storage

# Fortnox credentials
FORTNOX_CLIENT_ID=...
FORTNOX_CLIENT_SECRET=...

# Slack credentials - TESTING/DEV WORKSPACE (same as staging)
SLACK_BOT_TOKEN=xoxb-[dev-token]...
SLACK_SIGNING_SECRET=[dev-secret]...
SLACK_APP_TOKEN=xapp-[dev-token]...

# Environment identification
ENVIRONMENT=development
```

**3. Sync tokens from production database:**
```bash
./scripts/sync_tokens_from_db.sh
```

This uses Railway CLI to fetch tokens from production and saves them to `fortnox_tokens.json`.

**4. Run bot locally:**
```bash
./venv/bin/python -m src.bot
```

Check logs for:
```
TokenManager initialized: file storage (read/write)
✅ Tokens read from file: fortnox_tokens.json
```

**Re-sync tokens periodically** when they become stale (production refreshes them every 50 minutes).

---

## 🔧 Environment-Specific Behavior

### **Production Environment (Railway main branch)**

**Configuration:**
```bash
DATABASE_URL=postgresql://... # Read/write
ENVIRONMENT=production
SLACK_* = production workspace
```

**Token Storage:** PostgreSQL database (read/write)

**Behavior:**
- ✅ Reads tokens from database
- ✅ Writes refreshed tokens to database (only environment that does this!)
- ✅ Staging sees updates immediately
- ✅ Background refresh every 50 minutes
- ✅ Production Slack workspace

### **Staging Environment (Railway staging branch)**

**Configuration:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}} # Same connection as production
TOKEN_STORAGE_READONLY=true # CRITICAL - prevents writes
ENVIRONMENT=staging
SLACK_* = testing/dev workspace (different from prod!)
```

**Token Storage:** PostgreSQL database (application-level read-only)

**Behavior:**
- ✅ Reads tokens from same database as production
- ⚠️  **Cannot** refresh tokens (TOKEN_STORAGE_READONLY prevents writes)
- ✅ Always has latest tokens from production
- ✅ Testing/Dev Slack workspace (isolated from production users)
- ℹ️  If token refresh is triggered, logs warning and continues without writing

### **Local Development**

**Configuration:**
```bash
# No DATABASE_URL - uses file storage
ENVIRONMENT=development
SLACK_* = testing/dev workspace (same as staging)
```

**Token Storage:** Local file `./fortnox_tokens.json`

**Behavior:**
- ✅ Uses file storage (no database connection while running)
- ✅ Syncs tokens from production database via Railway CLI
- ✅ Writes refreshed tokens to local file (independent from prod)
- ✅ Testing/Dev Slack workspace (same as staging)
- ℹ️  Tokens can drift from production if not synced regularly

**Syncing Tokens for Local Dev:**

```bash
# Pull latest tokens from production database via Railway CLI
./scripts/sync_tokens_from_db.sh
```

The script uses Railway CLI to fetch tokens from production and save locally.

---

## 📝 Deployment Checklist

- [ ] **Step 1:** Update dependencies (psycopg2-binary added)
- [ ] **Step 2:** Update code (TokenManager with PostgreSQL support)
- [ ] **Step 3:** Add PostgreSQL database to Railway production
- [ ] **Step 4:** Configure production environment variables
- [ ] **Step 5:** Deploy to production (`main` branch)
- [ ] **Step 6:** Verify production uses database (check logs)
- [ ] **Step 7:** Create staging service in same Railway project
- [ ] **Step 8:** Configure staging with DATABASE_URL reference and TOKEN_STORAGE_READONLY=true
- [ ] **Step 9:** Deploy to staging (`staging` branch)
- [ ] **Step 10:** Verify staging reads from database in readonly mode
- [ ] **Step 11:** Install Railway CLI locally
- [ ] **Step 12:** Run `sync_tokens_from_db.sh` to pull tokens locally
- [ ] **Step 13:** Test local bot with synced tokens

---

## 🧪 Testing Plan

### **Test 1: Production Uses Database (Read/Write)**
```bash
railway logs --service production | grep "TokenManager"
# Expected: "TokenManager initialized: database storage (read/write)"
# Expected: "✅ Tokens read from database"
# Expected: "✅ Tokens written to database successfully" (on refresh)
```

### **Test 2: Staging Uses Database (Read-Only)**
```bash
railway logs --service staging | grep "TokenManager"
# Expected: "TokenManager initialized: database storage (read-only)"
# Expected: "✅ Tokens read from database"
# Expected: "⚠️  Token storage is READ-ONLY" (if refresh attempted)
```

### **Test 3: Local Uses File Storage**
```bash
./venv/bin/python -m src.bot
# Check logs for: "TokenManager initialized: file storage (read/write)"
# Check logs for: "✅ Tokens read from file: fortnox_tokens.json"
```

### **Test 4: Token Refresh Only Happens in Production**
1. Wait for production token refresh (50 minutes or force)
2. Check production logs: "✅ Tokens written to database successfully"
3. Check staging logs: Should see updated tokens on next read
4. Verify local stays unchanged (until you run sync script)

### **Test 5: Staging Cannot Write Tokens**
1. Try to trigger refresh in staging (shouldn't happen, but test defensive code)
2. Check logs: "⚠️  Token storage is READ-ONLY - save_tokens() skipped"
3. Verify database unchanged (production tokens still there)

### **Test 6: Local Token Sync**
1. Run `./scripts/sync_tokens_from_db.sh`
2. Check `fortnox_tokens.json` was updated
3. Verify matches production database timestamps

---

## 🛠️ Helper Scripts

### **`scripts/sync_tokens_from_db.sh`**

Downloads tokens from production database to local file via Railway CLI.

**Prerequisites:**
- Railway CLI installed and logged in
- Linked to your project (`railway link`)

**Usage:**
```bash
./scripts/sync_tokens_from_db.sh
```

**Result:**
- Updates `fortnox_tokens.json` with latest production tokens
- Fetches directly from production database

---

## 🚨 Troubleshooting

### **Problem: Staging shows "⚠️ Cannot initialize tokens in read-only mode"**

**Cause:** Staging tried to initialize from env vars but is in read-only mode.

**Solution:** Production must seed the database first. Deploy to production before staging.

### **Problem: Local sync fails with "Database connection failed"**

**Cause:** DATABASE_URL_RO not set or invalid.

**Solution:**
1. Run `scripts/setup_db_readonly_role.py` on production
2. Copy the read-only connection string to `.env.development`
3. Retry `./scripts/sync_tokens_from_db.sh`

### **Problem: Production shows "Failed to initialize database"**

**Cause:** DATABASE_URL not set or PostgreSQL not added to Railway.

**Solution:**
1. Verify PostgreSQL was added to Railway project
2. Check that `DATABASE_URL` exists in production environment variables
3. Redeploy production service

### **Problem: Tokens not syncing between production and staging**

**Cause:** Staging using wrong DATABASE_URL (not the readonly one).

**Solution:**
1. Verify staging has the read-only connection string (fortnox_readonly user)
2. Check that `TOKEN_STORAGE_READONLY=true` is set in staging
3. Restart staging service

---

## 🚂 Railway Workflow Summary

### **Production (main branch):**
```bash
# One-time setup
1. Add PostgreSQL to Railway project
2. Run scripts/setup_db_readonly_role.py
3. Configure environment variables
4. git push origin main

# Normal workflow
- Push to main → auto-deploys
- Tokens refresh every 50 minutes
- Database updated automatically
```

### **Staging (staging branch):**
```bash
# One-time setup
1. Create second Railway service for staging branch
2. Configure with readonly DATABASE_URL
3. Set TOKEN_STORAGE_READONLY=true
4. Configure testing Slack workspace credentials

# Normal workflow
- git checkout staging
- git merge main
- git push origin staging
- Staging reads tokens from production database
```

### **Local Development:**
```bash
# One-time setup
1. Create .env.development with DATABASE_URL_RO
2. ./venv/bin/pip install psycopg2-binary

# Normal workflow
- ./scripts/sync_tokens_from_db.sh  # Pull latest tokens
- ./venv/bin/python -m src.bot      # Run bot locally
- Re-sync tokens periodically
```

---

## 📊 Benefits After Implementation

✅ **No more token conflicts** - Only production writes tokens  
✅ **Instant synchronization** - Staging always reads latest tokens  
✅ **Simpler debugging** - One place to check tokens (production database)  
✅ **Better monitoring** - Database timestamps show when tokens were updated  
✅ **Local dev stays simple** - File-based with easy sync  
✅ **Production-ready** - Railway-native PostgreSQL solution  
✅ **Environment isolation** - Production and staging/dev use separate Slack workspaces

---

## 📚 Additional Resources

- **Railway PostgreSQL Docs:** https://docs.railway.app/databases/postgresql
- **psycopg2 Documentation:** https://www.psycopg.org/docs/
- **Fortnox OAuth Docs:** https://developer.fortnox.se/general/authentication/

---

**Last Updated:** 2025-10-26  
**Status:** ✅ Implemented - Ready for deployment  
**Estimated Time:** 1-2 hours total implementation + testing
