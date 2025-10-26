# 🤖 Agent Documentation

This file contains important context and commands for AI coding agents working on this project. It helps maintain consistency across sessions and provides quick reference for common tasks.

---

## 🍺 **IMPORTANT: Business Context**

**This is a CRAFT BREWERY inventory system.**

⚠️ **Critical Guidelines for AI Agents:**

1. **Never use mainstream/commercial beer brands** (e.g., Carlsberg, Tuborg, Heineken) or craftwashing brands (e.g., Brutal Brewing) in examples or documentation
2. **This brewery produces high-quality craft beer** - treat it with respect in all communications
3. **Use appropriate craft beer examples:**
   - Beerium (e.g., "Beerium ISWID 6.5%" / "I'll Sleep When I'm Dead")
   - Stigbergets Bryggeri
   - Omnipollo
   - Or generic craft styles: "Imperial Stout 8.5%", "Hazy IPA 6.5%", "Sour Ale 4.2%"
4. **Context matters:** This is about artisanal brewing, unique flavors, and craft beer culture
5. **Documentation examples** should reflect the quality and craftsmanship of the products
6. **Avoid craftwashing:** Some brands appear craft but are owned by large commercial breweries

**Why this matters:** Using commercial beer brands in a craft brewery context is disrespectful to the business and the craft beer industry. Always maintain awareness of the business domain.

---

## 🔧 Development Environment

### Virtual Environment
This project uses a Python virtual environment located at `./venv/`

**Important**: Always use the venv Python interpreter when running scripts:
```bash
./venv/bin/python <script_name>.py
```

**Do NOT use**:
- `python` (not installed on this system)
- `python3` (uses system Python, missing dependencies)

### Required Dependencies
All Python dependencies are installed in the virtual environment. If you need to install new packages:
```bash
./venv/bin/pip install <package_name>
./venv/bin/pip freeze > requirements.txt  # Update requirements
```

---

## 🧪 Testing

### Test Fortnox API Connection
To test the Fortnox API integration:
```bash
./venv/bin/python test_fortnox.py
```

**Expected Output**:
- ✅ Successfully retrieves all articles from Fortnox (with pagination)
- ✅ Filters articles that are in stock
- ✅ Displays sample articles

### Run the Bot
To start the Slack bot:
```bash
./venv/bin/python -m src.bot
```

The bot must be running for Slack commands to work.

---

## 📁 Project Structure

```
fortnox_slack_bot/
├── src/                        # Source code package
│   ├── bot.py                 # Main Slack bot application
│   ├── fortnox_client.py      # Fortnox API client (with pagination)
│   └── token_manager.py       # Token persistence handler
├── tests/                      # Test suite
│   ├── test_fortnox.py        # API connection test
│   ├── test_horeca_lookup.py  # HoReCa price list test
│   └── test_*.py              # Other tests
├── scripts/                    # Utility scripts
│   ├── get_fortnox_token.py   # OAuth token generator
│   ├── refresh_token.py       # Manual token refresh
│   └── setup.sh               # Initial setup script
├── docs/                       # Documentation
│   ├── QUICKSTART.md          # Getting started guide
│   ├── FORTNOX_SETUP.md       # Fortnox API setup
│   ├── RAILWAY_DEPLOYMENT.md  # Railway deployment
│   └── *.md                   # Other documentation
├── deployment/                 # Deployment configuration
│   ├── Dockerfile             # Docker configuration
│   ├── entrypoint.sh          # Container entrypoint
│   └── docker-compose.yml     # Local Docker setup
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example               # Environment template
├── fortnox_tokens.json         # Persistent token storage (not in git, auto-created)
└── venv/                       # Virtual environment (not in git)
```

### 🚂 Railway Deployment

This project uses **Dockerfile** for Railway deployment. 

**⚠️ IMPORTANT**: If you add new Python files that are needed at runtime:
- Update the `COPY *.py .` line in `Dockerfile` if files are in subdirectories
- Or add specific `COPY` commands for new files
- Railway only includes files explicitly copied in the Dockerfile

**Example**: When `token_manager.py` was added, the Dockerfile needed updating from:
```dockerfile
COPY app.py .
COPY fortnox_client.py .
```
to:
```dockerfile
COPY *.py .
```

---

## 🔑 Key Implementation Details

### Token Management

#### **Multi-Environment Strategy (Production, Staging, Local)**

The bot uses **PostgreSQL for production/staging** and **file-based storage for local development**:

**Production (Railway main branch):**
- PostgreSQL database with read/write access
- Refreshes tokens every 50 minutes
- Saves updated tokens to database

**Staging (Railway staging branch):**
- Same PostgreSQL database (read-only via `TOKEN_STORAGE_READONLY=true`)
- Reads tokens from database (production manages refresh)
- Never refreshes tokens itself

**Local Development:**
- File-based storage (`fortnox_tokens.json`)
- **MUST use `TOKEN_STORAGE_READONLY=true` in `.env`**
- Sync tokens from production via: `./scripts/sync_tokens_from_db.sh`

#### **⚠️ CRITICAL: Fortnox OAuth Token Behavior**

**NEVER generate separate OAuth tokens for local development!**

Fortnox **only allows ONE active OAuth session per application**. When you generate new tokens (via `scripts/get_fortnox_token.py`), it **invalidates ALL previous refresh tokens**, including production's tokens.

**What happens if you generate new tokens locally:**
1. Run `./venv/bin/python scripts/get_fortnox_token.py` locally
2. ❌ **Production's refresh token is IMMEDIATELY INVALIDATED**
3. ❌ Production bot fails with "invalid_grant" error
4. ❌ Staging bot also fails (reads from same database)
5. 💥 **Entire system breaks until you regenerate tokens in production**

**Correct approach for local development:**
1. Set `TOKEN_STORAGE_READONLY=true` in local `.env`
2. Sync tokens from production: `./scripts/sync_tokens_from_db.sh`
3. Never run `get_fortnox_token.py` unless you're intentionally updating production

**Token Management Files:**
- `src/token_manager.py` - Handles reading/writing tokens with thread-safe locking
- `fortnox_tokens.json` - Stores current access_token and refresh_token locally (created automatically)
- `scripts/get_fortnox_token.py` - ⚠️ **PRODUCTION ONLY** - Generates initial tokens via OAuth flow
- `scripts/sync_tokens_from_db.sh` - Syncs tokens from production to local file

### Fortnox API Pagination
The `fortnox_client.py` implements automatic pagination:
- **Limit**: 500 articles per request (maximum allowed by API)
- **Method**: Uses `offset` parameter to fetch all pages
- **Total articles**: 519 (as of last test)
- **Articles in stock**: 139 (as of last test)

### Rate Limits
- **Fortnox API**: 300 requests/minute per access token
- **Current usage**: ~2 requests per full article fetch (well within limits)
- **Rate limit handling**: All commands and test scripts now handle rate limit errors gracefully
  - When rate limit is hit (HTTP 429), a `FortnoxRateLimitError` is raised
  - Processing stops immediately to prevent cascading failures
  - User-friendly message is displayed: "API rate limit exceeded, please wait a few minutes"
  - ⚠️ **IMPORTANT**: If you hit rate limits during testing, wait 3-5 minutes before retrying

### Data Type Handling
- `QuantityInStock` may be returned as string or number - code handles both
- Always convert to float before comparison

---

## 🐛 Common Issues

### "invalid_grant" or "Invalid refresh token" error
**Cause**: Refresh token rotation - Fortnox issued a new refresh token that wasn't saved
**Solution**: 
1. Token file system now handles this automatically (as of 2025-10-25)
2. If you see this error, regenerate tokens: `./venv/bin/python scripts/get_fortnox_token.py`
3. Restart the bot - it will create `fortnox_tokens.json` automatically
4. On Railway: Make sure environment variables are set (used for initial migration only)

### "Command 'python' not found"
**Solution**: Use `./venv/bin/python` instead of `python`

### "Fortnox API rate limit exceeded (429)"
**Cause**: Too many API requests in a short period (>300 per minute)
**Solution**: 
1. Wait 3-5 minutes before making new requests
2. The bot automatically stops processing when rate limit is hit
3. All test scripts now handle this gracefully with clear error messages
4. **Prevention**: Avoid running multiple test scripts simultaneously

### "ModuleNotFoundError: No module named 'X'"
**Solution**: 
1. Ensure venv is activated or use `./venv/bin/python`
2. Check that module is in `requirements.txt`
3. Reinstall if needed: `./venv/bin/pip install -r requirements.txt`

### Bot not responding in Slack
**Solution**:
1. Check bot is running: `./venv/bin/python -m src.bot`
2. Verify Socket Mode is enabled in Slack App settings
3. Check `.env` file has all required tokens

---

## 📝 Code Style Guidelines

### Logging
- Use `logger.info()` for normal operations
- Use `logger.error()` for errors with stack traces
- Include context in log messages (e.g., counts, IDs)

### Error Handling
- Always handle API response data type variations
- Use try/except for type conversions
- Provide fallback values (e.g., `0` for missing quantities)

### API Calls
- Use pagination for list endpoints
- Log progress for long-running operations
- Respect rate limits (already well within bounds)

---

## 🚀 Recent Changes

### 2025-10-25: Token Rotation Fix (Critical)
- **Fixed refresh token rotation bug**: Bot now properly handles Fortnox token rotation
  - Fortnox issues NEW refresh tokens when refreshing (OAuth best practice)
  - Previous code only saved access token, causing old refresh token to become invalid
  - Now uses persistent file storage (`fortnox_tokens.json`) that survives restarts
  - Both access AND refresh tokens are saved on every refresh
  - **Migration**: Token file auto-initializes from environment variables on first run
  - This fixes the "invalid_grant" error that stopped the bot after ~50 minutes

### 2025-10-24: Rate Limit Protection & Price Lists
- **Rate limit handling**: Added `FortnoxRateLimitError` exception
  - All Slack commands now stop immediately on rate limit (HTTP 429)
  - All test scripts gracefully handle rate limits with clear messages
  - Prevents cascading failures that could ban access tokens
- **HoReCa price list integration**:
  - Dynamic lookup of HoReCa price list at startup
  - Beer keg prices now fetched from price list B (HoReCa)
  - Fallback to `SalesPrice` if price list entry not found
- **Token refresh automation**: Built into app startup and runs every 50 minutes

### 2025-10-21: Pagination Implementation
- Implemented automatic pagination in `get_articles()`
- Now retrieves all 519 articles instead of just first page (~43 articles)
- Fixed data type conversion bug for `QuantityInStock`
- Added detailed logging for pagination progress

---

## 📚 External Documentation

- [Slack Bolt Python](https://slack.dev/bolt-python/)
- [Fortnox API Documentation](https://developer.fortnox.se/)
- [Fortnox API Reference](https://apps.fortnox.se/apidocs/)

---

## 💡 Tips for Agents

1. **Always test changes**: Run `./venv/bin/python test_fortnox.py` after modifying API client
2. **Check logs**: Bot logs contain useful debugging information
3. **Environment variables**: Sensitive data is in `.env` (not committed to git)
4. **Pagination**: Remember that Fortnox API has limits - always implement pagination for lists
5. **Rate limits**: 
   - 300 requests/minute limit enforced by Fortnox
   - All code includes `FortnoxRateLimitError` handling
   - Testing multiple price lists can quickly hit the limit
   - **Best practice**: Test with small datasets first, then scale up
6. **Error handling**: Always catch `FortnoxRateLimitError` separately from generic exceptions

---

**Last Updated**: 2025-10-26
