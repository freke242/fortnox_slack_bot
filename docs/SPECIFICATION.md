# Fortnox Slack Bot - Complete Technical Specification

**Version:** 1.0  
**Last Updated:** October 25, 2025  
**Purpose:** Complete specification for reimplementation by AI agents or developers

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Authentication & Token Management](#authentication--token-management)
5. [Slack Commands Specification](#slack-commands-specification)
6. [Fortnox API Integration](#fortnox-api-integration)
7. [Error Handling](#error-handling)
8. [Logging](#logging)
9. [Deployment](#deployment)
10. [Environment Variables](#environment-variables)
11. [Testing](#testing)
12. [Security Considerations](#security-considerations)

---

## Overview

### Purpose
A Slack bot that integrates with Fortnox ERP API to provide real-time inventory and warehouse information directly in Slack workspace channels.

### Core Functionality
- List all articles in stock with filtering capabilities
- Search for specific articles by article number
- Display keg inventory with special pricing from HoReCa price list
- Automatic OAuth token refresh (every 50 minutes)
- Persistent token storage across restarts/deployments
- Rate limit handling (Fortnox: 300 requests/minute)

### Technology Stack
- **Language:** Python 3.11
- **Slack Framework:** slack-bolt (Socket Mode)
- **HTTP Client:** requests
- **Environment:** dotenv
- **Deployment:** Docker, Railway.app
- **Token Storage:** JSON file with file locking

---

## Architecture

### High-Level Design

```
┌─────────────┐
│   Slack     │
│  Workspace  │
└──────┬──────┘
       │ WebSocket (Socket Mode)
       │
┌──────▼──────────────────────────┐
│  Fortnox Slack Bot              │
│  ┌──────────────────────────┐  │
│  │  src/bot.py              │  │
│  │  - Slack command handlers│  │
│  │  - Token refresh thread  │  │
│  └────────┬─────────────────┘  │
│           │                     │
│  ┌────────▼─────────────────┐  │
│  │  src/fortnox_client.py   │  │
│  │  - API wrapper           │  │
│  │  - Pagination            │  │
│  │  - Rate limit handling   │  │
│  └────────┬─────────────────┘  │
│           │                     │
│  ┌────────▼─────────────────┐  │
│  │  src/token_manager.py    │  │
│  │  - Token persistence     │  │
│  │  - File locking          │  │
│  └──────────────────────────┘  │
└─────────────┬───────────────────┘
              │
    ┌─────────▼─────────┐
    │  Fortnox API      │
    │  (OAuth 2.0)      │
    └───────────────────┘
```

### Component Responsibilities

#### `src/bot.py`
- Slack app initialization (Socket Mode)
- Command handlers (`/fortnox-stock`, `/fortnox-article`, `/fortnox-kegs`)
- Token refresh background thread (runs every 50 minutes)
- Response formatting and pagination
- Global state management (fortnox_client, current_access_token)

#### `src/fortnox_client.py`
- Fortnox API HTTP client
- Automatic pagination for list endpoints
- Rate limit error detection and raising
- Article filtering and data transformation
- HoReCa price list lookup and caching

#### `src/token_manager.py`
- Token file I/O with thread-safe file locking
- Token initialization from environment variables
- Token persistence across restarts
- Railway volume support detection


---

## Project Structure

```
fortnox_slack_bot/
├── README.md                   # Project overview and quick start
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── .railwayignore             # Railway deployment exclusions
├── railway.json               # Railway configuration (points to deployment/Dockerfile)
│
├── src/                       # Source code package
│   ├── __init__.py           # Package marker
│   ├── bot.py                # Main application (Slack bot logic)
│   ├── fortnox_client.py     # Fortnox API client
│   └── token_manager.py      # Token persistence manager
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_fortnox.py       # API connection tests
│   ├── test_horeca_lookup.py # HoReCa price list tests
│   ├── test_price_cache.py   # Price caching tests
│   └── test_*.py             # Additional tests
│
├── scripts/                   # Utility scripts
│   ├── get_fortnox_token.py  # OAuth token generator (interactive)
│   ├── refresh_token.py      # Manual token refresh
│   ├── validate_config.py    # Configuration validator
│   ├── check_credentials.py  # Credential checker
│   └── setup.sh              # Initial setup script
│
├── docs/                      # Documentation
│   ├── QUICKSTART.md         # Getting started guide
│   ├── FORTNOX_SETUP.md      # Fortnox API setup instructions
│   ├── RAILWAY_DEPLOYMENT.md # Railway deployment guide
│   ├── RAILWAY_VOLUME_SETUP.md # Volume configuration
│   ├── DEPLOYMENT.md         # General deployment guide
│   ├── SPECIFICATION.md      # This file
│   ├── AGENTS.md             # AI agent context
│   └── *.md                  # Other documentation
│
└── deployment/                # Deployment configuration
    ├── Dockerfile            # Docker container definition
    ├── entrypoint.sh         # Container startup script
    ├── docker-compose.yml    # Local Docker setup
    └── fortnox-bot.service   # Systemd service file
```

### File Purposes

**Runtime Files (not in git):**
- `fortnox_tokens.json` - Persistent OAuth tokens (created automatically)
- `.env` - Environment variables (secrets)
- `venv/` - Python virtual environment

**Entry Point:**
- Run with: `python -m src.bot`


---

## Authentication & Token Management

### OAuth 2.0 Flow

#### Initial Token Generation
1. Use `scripts/get_fortnox_token.py` to generate initial tokens
2. Opens authorization URL in browser
3. User authorizes application (Fortnox service account)
4. Receives authorization code via redirect
5. Exchanges code for access_token + refresh_token
6. Saves to `fortnox_tokens.json`

#### Token Properties
- **Access Token:** Valid for ~1 hour
- **Refresh Token:** Single-use, rotates on each refresh
- **Rotation:** Fortnox issues NEW refresh token when you refresh
- **Storage:** `fortnox_tokens.json` (JSON format)

### Token Refresh Strategy

#### Automatic Refresh (Background Thread)
```python
# Runs in background thread
def token_refresh_thread():
    while True:
        time.sleep(50 * 60)  # Sleep 50 minutes
        success = refresh_fortnox_token()
        if not success:
            logger.error("Token refresh failed in background thread")
```

#### Refresh Process
1. Read refresh_token from `fortnox_tokens.json`
2. POST to `https://apps.fortnox.se/oauth-v1/token`
3. Data: `grant_type=refresh_token&refresh_token=<token>`
4. Headers: `Authorization: Basic <base64(client_id:client_secret)>`
5. Response includes NEW access_token AND NEW refresh_token
6. **CRITICAL:** Save BOTH tokens to file immediately
7. Update in-memory fortnox_client with new access_token

#### Fallback Mechanism
If refresh fails with `invalid_grant` error:
1. Attempt to use refresh_token from environment variable
2. If successful, save new tokens to file
3. This provides recovery from expired file tokens

### Token Persistence

#### File Format (`fortnox_tokens.json`)
```json
{
  "access_token": "abc123...",
  "refresh_token": "def456..."
}
```

#### Thread-Safe File Operations
```python
import fcntl

def save_tokens(access_token, refresh_token):
    with open('fortnox_tokens.json', 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        json.dump({"access_token": access_token, 
                   "refresh_token": refresh_token}, f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
```

### Railway Volume Support

#### Detection
- Check for `RAILWAY_VOLUME_MOUNT_PATH` environment variable
- If set, use `$RAILWAY_VOLUME_MOUNT_PATH/fortnox_tokens.json`
- Else use `./fortnox_tokens.json` (local directory)

#### Initialization
- On first run, if token file doesn't exist:
  - Read tokens from environment variables
  - Save to token file
  - Subsequent runs use file (survives redeploys)

### Authorization Headers

**All Fortnox API requests:**
```python
headers = {
    "Content-Type": "application/json",
    "Access-Token": current_access_token,
    "Client-Secret": client_secret
}
```


---

## Slack Commands Specification

### Command: `/fortnox-stock`

**Purpose:** List all articles in stock with optional filtering and display limit

**Syntax:**
```
/fortnox-stock [minimum_quantity] [display_limit]
```

**Parameters:**
- `minimum_quantity` (optional, default: 0) - Only show articles with stock >= this value
- `display_limit` (optional, default: 50) - Maximum number of articles to display

**Examples:**
```
/fortnox-stock              # Show all articles in stock (limit 50)
/fortnox-stock 10           # Show articles with stock >= 10
/fortnox-stock 5 100        # Show articles with stock >= 5, display up to 100
```

**Response Format (Desktop/Wide):**
```
📦 Articles in Stock (Minimum: 0, Showing: 10/139)

Finns  Artikelnummer  Beskrivning           Pris      Reserv  Tot
-----  --------------  --------------------  --------  ------  -----
10     12345          Product Name          1,234 kr  5       15
25     67890          Another Product       567 kr    0       25
...
```

**Response Format (Mobile/Narrow):**
```
📦 Articles in Stock (10/139)

Finns  Namn           ABV    Pris
-----  -------------  -----  ------
10     Product A      5.0%   1,234
25     Product B      4.5%   567
...
```

**Mobile Detection:**
- Desktop: Lines > 70 characters
- Mobile: Lines <= 70 characters

**Implementation:**
```python
@app.command("/fortnox-stock")
def handle_stock_command(ack, command, respond):
    ack()  # Acknowledge immediately
    
    # Parse parameters
    text = command.get('text', '').strip()
    parts = text.split()
    minimum_stock = int(parts[0]) if len(parts) >= 1 else 0
    display_limit = int(parts[1]) if len(parts) >= 2 else 50
    
    # Fetch and respond
    articles = fortnox_client.get_articles_in_stock(minimum_stock)
    message = format_articles_message(articles, limit=display_limit)
    respond(message)
```

---

### Command: `/fortnox-article`

**Purpose:** Get detailed information about a specific article by article number

**Syntax:**
```
/fortnox-article <article_number>
```

**Parameters:**
- `article_number` (required) - The Fortnox article number

**Examples:**
```
/fortnox-article 12345
/fortnox-article ABC-001
```

**Response Format:**
```
📦 Article: 12345

**Description:** Product Name Here
**Available Stock:** 25
**Reserved:** 5
**Total:** 30
**Price:** 1,234 kr
**Unit:** st (pieces)
**Supplier:** Supplier Name AB
```

**Error Cases:**
```
❌ Article 99999 not found
⚠️ Please provide an article number. Usage: `/fortnox-article <article_number>`
```

**Implementation:**
```python
@app.command("/fortnox-article")
def handle_article_command(ack, command, respond):
    ack()
    
    article_number = command.get('text', '').strip()
    
    if not article_number:
        respond("⚠️ Please provide an article number...")
        return
    
    article = fortnox_client.get_article_by_number(article_number)
    
    if not article:
        respond(f"❌ Article {article_number} not found")
        return
    
    message = format_article_details(article)
    respond(message)
```

---

### Command: `/fortnox-kegs`

**Purpose:** Display beer kegs in stock with prices from HoReCa price list

**Syntax:**
```
/fortnox-kegs
```

**Parameters:** None

**Response Format:**
```
🍺 Beer Kegs in Stock (8)

Finns  Namn                   ABV    HoReCa Pris  Total
-----  ---------------------  -----  -----------  -----
10     Carlsberg 30L          5.0%   1,850 kr     15
5      Tuborg 50L             4.6%   2,400 kr     8
...
```

**Price Logic:**
1. Find "HoReCa" price list (case-insensitive search)
2. Look up article in price list B (HoReCa)
3. If found in price list, use that price
4. Else fallback to article.SalesPrice
5. Cache price list ID for performance

**Implementation:**
```python
@app.command("/fortnox-kegs")
def handle_kegs_command(ack, command, respond):
    ack()
    
    # Get all articles
    all_articles = fortnox_client.get_articles()
    
    # Filter for kegs (Description contains "Fustage" or similar)
    kegs = [a for a in all_articles if is_keg(a)]
    
    # Filter in stock
    kegs_in_stock = [k for k in kegs if k.get('QuantityInStock', 0) > 0]
    
    message = format_kegs_message(kegs_in_stock)
    respond(message)
```


---

## Fortnox API Integration

### Base Configuration

**API Base URL:** `https://api.fortnox.se/3`

**Authentication:**
- Access-Token header (OAuth access token)
- Client-Secret header (from app registration)

### Pagination

All list endpoints support pagination:

**Parameters:**
- `limit` - Results per page (max: 500, recommended: 500)
- `offset` - Number of results to skip

**Implementation:**
```python
def get_all_articles_paginated():
    all_articles = []
    offset = 0
    limit = 500
    
    while True:
        response = requests.get(
            f"{BASE_URL}/articles",
            params={"limit": limit, "offset": offset},
            headers=headers
        )
        
        data = response.json()
        articles = data.get('Articles', [])
        
        if not articles:
            break
        
        all_articles.extend(articles)
        offset += len(articles)
        
        # Check if we got less than limit (last page)
        if len(articles) < limit:
            break
    
    return all_articles
```

### Rate Limiting

**Fortnox Limit:** 300 requests per minute per access token

**Detection:**
```python
if response.status_code == 429:
    raise FortnoxRateLimitError("Rate limit exceeded")
```

**Handling:**
- Immediately stop processing
- Return user-friendly error message
- Do NOT retry automatically
- Log warning

**Custom Exception:**
```python
class FortnoxRateLimitError(Exception):
    """Raised when Fortnox API rate limit is hit"""
    pass
```

### API Endpoints Used

#### GET /articles
**Purpose:** List all articles

**Parameters:**
- `limit` (default: 500)
- `offset` (default: 0)

**Response:**
```json
{
  "Articles": [
    {
      "ArticleNumber": "12345",
      "Description": "Product Name",
      "QuantityInStock": "25",
      "SalesPrice": "1234.50",
      "Unit": "st",
      "Manufacturer": "Supplier AB",
      ...
    }
  ]
}
```

**Notes:**
- `QuantityInStock` may be string or number - always convert to float
- Use pagination to fetch all articles

#### GET /articles/{ArticleNumber}
**Purpose:** Get single article details

**Response:** Same as above, but single article object

#### GET /pricelists
**Purpose:** List all price lists

**Response:**
```json
{
  "PriceLists": [
    {
      "Code": "A",
      "Description": "Standard Price List",
      ...
    },
    {
      "Code": "B",
      "Description": "HoReCa",
      ...
    }
  ]
}
```

**Usage:** Find HoReCa price list by case-insensitive description match

#### GET /pricelists/{Code}/{ArticleNumber}
**Purpose:** Get article price in specific price list

**Response:**
```json
{
  "Price": "1850.00"
}
```

### Data Type Handling

**Always handle type variations:**
```python
def safe_float(value, default=0.0):
    """Convert to float, handling string/number/None"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

quantity = safe_float(article.get('QuantityInStock'))
```

### HoReCa Price List Logic

**Initialization (on startup):**
```python
def initialize_price_lists():
    """Find and cache HoReCa price list ID"""
    pricelists = self.get_pricelists()
    
    for pl in pricelists:
        desc = pl.get('Description', '').lower()
        if 'horeca' in desc:
            self.horeca_pricelist_code = pl.get('Code')
            logger.info(f"Found HoReCa price list: {pl.get('Code')}")
            return
    
    logger.warning("HoReCa price list not found")
```

**Price Lookup (per article):**
```python
def get_horeca_price(article_number):
    """Get HoReCa price for article, with fallback"""
    if not self.horeca_pricelist_code:
        return None
    
    try:
        response = requests.get(
            f"{BASE_URL}/pricelists/{self.horeca_pricelist_code}/{article_number}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json().get('Price')
    except Exception as e:
        logger.debug(f"No HoReCa price for {article_number}: {e}")
    
    return None
```

**Caching:**
- Cache price list code (not individual prices)
- Refresh on each bot restart
- Individual prices fetched on demand


---

## Error Handling

### Error Categories

#### 1. Rate Limit Errors (HTTP 429)
```python
try:
    articles = fortnox_client.get_articles()
except FortnoxRateLimitError:
    respond("⚠️ **Fortnox API rate limit exceeded**\n\n"
            "We've hit the maximum number of API requests. "
            "Please wait a few minutes and try again.")
    return
```

**User Message:** Friendly explanation, no technical details

#### 2. Authentication Errors (HTTP 401, 403)
```python
if response.status_code in [401, 403]:
    logger.error(f"Authentication failed: {response.status_code}")
    return None
```

**Handling:** Log error, trigger token refresh, return empty result

#### 3. Not Found Errors (HTTP 404)
```python
article = fortnox_client.get_article_by_number(article_number)
if not article:
    respond(f"❌ Article {article_number} not found")
    return
```

**User Message:** Clear "not found" message

#### 4. Network Errors
```python
try:
    response = requests.get(url, timeout=10)
except requests.exceptions.RequestException as e:
    logger.error(f"Network error: {e}")
    respond("❌ Failed to connect to Fortnox API. Please try again.")
    return
```

**Timeout:** 10 seconds for all requests

#### 5. Unexpected Errors
```python
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    respond(f"❌ An unexpected error occurred: {str(e)}")
```

**Always:** Include stack trace in logs (`exc_info=True`)

### Error Response Format

**Pattern:**
- ❌ for critical errors
- ⚠️ for warnings/rate limits
- 📋 for informational messages
- Clear, actionable message
- No technical jargon for users

---

## Logging

### Configuration

**Log Levels:**
- `INFO` - Normal operations
- `WARNING` - Rate limits, missing data
- `ERROR` - Failures, exceptions
- `DEBUG` - Detailed debugging (not used by default)

**Stream Routing (Railway-optimized):**
```python
# INFO/DEBUG → stdout (blue in Railway)
# WARNING/ERROR/CRITICAL → stderr (red in Railway)

class StdoutFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.WARNING

class StderrFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.WARNING

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.addFilter(StdoutFilter())

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.addFilter(StderrFilter())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[stdout_handler, stderr_handler]
)
```

### Log Messages

**Startup:**
```
Starting Fortnox Slack Bot...
✅ Fortnox Slack Bot is running\!
```

**Token Management:**
```
INFO - Refreshing Fortnox access token...
INFO - 🔄 Fortnox issued a new refresh token (rotation)
INFO - ✅ Access token refreshed successfully
ERROR - ❌ Failed to refresh token: HTTP 400
WARNING - ⚠️ Token from file is expired, trying environment variable fallback...
```

**API Calls:**
```
INFO - Fetching articles from Fortnox (offset: 0, limit: 500)...
INFO - Fetched 500 articles (page 1)
INFO - Fetched 19 articles (page 2)
INFO - Total articles retrieved: 519
INFO - Articles in stock: 139
```

**Commands:**
```
INFO - Stock command received: minimum=0, limit=50
INFO - Article lookup requested for: 12345
INFO - Kegs command received
WARNING - Rate limit hit on stock command
ERROR - Error handling stock command: <exception>
```

**Format Rules:**
- Use emojis for important status (✅ ❌ ⚠️ 🔄)
- Include relevant context (counts, IDs, parameters)
- Keep messages concise but informative
- Avoid duplicate information


---

## Deployment

### Docker Configuration

#### Dockerfile (`deployment/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Copy deployment entrypoint
COPY deployment/entrypoint.sh .
RUN chmod +x entrypoint.sh

# Security: Start as root to fix volume permissions, then drop to non-root user
# The entrypoint script handles permission fixes and user switching
ENTRYPOINT ["/app/entrypoint.sh"]
```

#### Entrypoint Script (`deployment/entrypoint.sh`)

**Purpose:** Fix Railway volume permissions, then drop to non-root user

**Flow:**
1. Check if running as root
2. Create `botuser` (uid 1000) if doesn't exist
3. Fix permissions on `/app` directory
4. Fix permissions on Railway volume (if exists)
5. Switch to `botuser` using `su`
6. Execute `python -m src.bot` as botuser

**Key Commands:**
```bash
# Create user
useradd -m -u 1000 -s /bin/bash botuser

# Fix permissions
chown -R botuser:botuser /app
chown -R botuser:botuser $RAILWAY_VOLUME_MOUNT_PATH

# Switch user and run
exec su -s /bin/sh botuser -c "cd /app && exec python -m src.bot"
```

**Logging:** All echo to stdout (not stderr) for clean Railway logs

### Railway Deployment

#### Configuration (`railway.json`)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "deployment/Dockerfile"
  }
}
```

**Purpose:** Tell Railway to use Dockerfile in deployment/ folder

#### Volume Setup

**Create Volume:**
1. Railway dashboard → New → Volume
2. Name: `fortnox-tokens`
3. Mount path: `/data`
4. Connect to service

**Environment Variable:**
- Railway automatically sets `RAILWAY_VOLUME_MOUNT_PATH=/data`
- Bot detects this and uses `/data/fortnox_tokens.json`

**Permissions:**
- Volume mounted as root
- Entrypoint script fixes permissions before switching to botuser
- This allows non-root app to write to volume

#### Deployment Exclusions (`.railwayignore`)

```
# Exclude from Railway deployment
.env
.env.example
venv/
__pycache__/
*.pyc
.git/
.gitignore
tests/
*.md
\!docs/RAILWAY_DEPLOYMENT.md
.vscode/
.idea/
```

**Purpose:** Reduce deploy size, exclude dev files

#### Build Process

1. Railway detects push to main branch
2. Reads `railway.json` → finds `deployment/Dockerfile`
3. Builds Docker image
4. Creates container with volume mounted
5. Runs entrypoint.sh
6. Bot starts

**Expected Logs:**
```
========================================
🚀 ENTRYPOINT: Starting Fortnox Slack Bot...
   Current user: root (uid=0)
========================================
ENTRYPOINT: Running as root, setting up secure environment...
✅ Created botuser (uid 1000)
✅ Fixed /app permissions
📁 ENTRYPOINT: Railway volume detected at: /data
✅ ENTRYPOINT: Fixed volume permissions
========================================
🔒 ENTRYPOINT: Dropping to non-root user (botuser)...
========================================
Starting Fortnox Slack Bot...
Checking token storage...
Using Railway volume for tokens: /data/fortnox_tokens.json
Tokens loaded from file
Initializing Fortnox connection...
Refreshing Fortnox access token...
✅ Access token refreshed successfully
✅ Fortnox Slack Bot is running\!
```

### Local Development

#### Setup
```bash
# Clone repository
git clone <repo_url>
cd fortnox_slack_bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Generate tokens
python scripts/get_fortnox_token.py

# Run bot
python -m src.bot
```

#### Docker Compose (`deployment/docker-compose.yml`)

```yaml
version: '3.8'
services:
  bot:
    build:
      context: ..
      dockerfile: deployment/Dockerfile
    env_file:
      - ../.env
    volumes:
      - token-data:/data
    restart: unless-stopped

volumes:
  token-data:
```

**Usage:**
```bash
docker-compose -f deployment/docker-compose.yml up -d
```

### System Service (`deployment/fortnox-bot.service`)

For running on Linux servers:

```ini
[Unit]
Description=Fortnox Slack Bot
After=network.target

[Service]
Type=simple
User=<your-user>
WorkingDirectory=/path/to/fortnox_slack_bot
ExecStart=/path/to/venv/bin/python -m src.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Install:**
```bash
sudo cp deployment/fortnox-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fortnox-bot
sudo systemctl start fortnox-bot
```


---

## Environment Variables

### Required Variables

#### Slack Configuration

**SLACK_BOT_TOKEN**
- Format: `xoxb-...`
- Source: Slack App → OAuth & Permissions → Bot User OAuth Token
- Purpose: Authenticate bot with Slack API
- Required: Yes

**SLACK_SIGNING_SECRET**
- Format: 32-character hex string
- Source: Slack App → Basic Information → Signing Secret
- Purpose: Verify requests from Slack
- Required: Yes

**SLACK_APP_TOKEN**
- Format: `xapp-...`
- Source: Slack App → Basic Information → App-Level Tokens
- Scope: `connections:write`
- Purpose: Enable Socket Mode (WebSocket connection)
- Required: Yes

#### Fortnox Configuration

**FORTNOX_CLIENT_ID**
- Format: UUID string
- Source: Fortnox Developer Portal → Integration settings
- Purpose: OAuth client identification
- Required: Yes

**FORTNOX_CLIENT_SECRET**
- Format: Base64-like string
- Source: Fortnox Developer Portal → Integration settings
- Purpose: OAuth authentication + API requests
- Required: Yes

**FORTNOX_ACCESS_TOKEN**
- Format: Long alphanumeric string
- Source: Generated by `scripts/get_fortnox_token.py`
- Purpose: API authentication (initial value)
- Required: Yes (initial setup only)
- Note: Updated in `fortnox_tokens.json` after first run

**FORTNOX_REFRESH_TOKEN**
- Format: Long alphanumeric string
- Source: Generated by `scripts/get_fortnox_token.py`
- Purpose: Token refresh (initial value + fallback)
- Required: Yes (initial setup + fallback recovery)
- Note: Updated in `fortnox_tokens.json` after first run

### Optional Variables

**RAILWAY_VOLUME_MOUNT_PATH**
- Format: `/data` (or custom path)
- Source: Automatically set by Railway when volume is mounted
- Purpose: Detect Railway volume for persistent storage
- Default: If not set, uses `./fortnox_tokens.json` in current directory

### Environment File Format (`.env`)

```bash
# Slack Bot Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_APP_TOKEN=xapp-your-app-level-token-here

# Fortnox API Configuration
FORTNOX_CLIENT_ID=your-client-id-uuid-here
FORTNOX_CLIENT_SECRET=your-client-secret-here
FORTNOX_ACCESS_TOKEN=your-access-token-here
FORTNOX_REFRESH_TOKEN=your-refresh-token-here
```

### Security Best Practices

1. **Never commit `.env`** - Add to `.gitignore`
2. **Use `.env.example`** - Template without actual secrets
3. **Railway secrets** - Set as environment variables in Railway dashboard
4. **Token rotation** - Refresh tokens auto-update, access tokens rotate hourly
5. **Principle of least privilege** - Only required Slack scopes


---

## Testing

### Test Structure

All tests located in `tests/` directory. Each test is a standalone script.

#### Run Tests

```bash
# Run individual test
python tests/test_fortnox.py

# Run all tests
for test in tests/test_*.py; do python "$test"; done
```

### Test Files

#### `tests/test_fortnox.py`
**Purpose:** Test basic Fortnox API connection

**Checks:**
- Environment variables are set
- Can connect to Fortnox API
- Can fetch articles with pagination
- Can filter articles in stock
- Data types are handled correctly

**Expected Output:**
```
🧪 Testing Fortnox API Connection
==================================================
✅ Environment variables loaded
✅ Fortnox client initialized
✅ Successfully retrieved 519 total articles
✅ Found 139 articles in stock
✅ Sample articles displayed correctly
```

#### `tests/test_horeca_lookup.py`
**Purpose:** Test HoReCa price list integration

**Checks:**
- Can find HoReCa price list
- Can look up prices for articles
- Fallback to SalesPrice works
- Caching works correctly

#### `tests/test_pricelists.py`
**Purpose:** Test price list API endpoints

**Checks:**
- Can list all price lists
- Can get article prices from specific lists
- Error handling for missing articles

#### `tests/test_price_cache.py`
**Purpose:** Test price caching mechanism

**Checks:**
- Price list code is cached
- Cache survives multiple lookups
- Cache invalidation works

### Manual Testing Checklist

**Slack Commands:**
- [ ] `/fortnox-stock` returns articles
- [ ] `/fortnox-stock 10` filters by quantity
- [ ] `/fortnox-stock 5 100` respects display limit
- [ ] `/fortnox-article 12345` returns specific article
- [ ] `/fortnox-article invalid` shows not found error
- [ ] `/fortnox-kegs` returns kegs with HoReCa prices

**Token Management:**
- [ ] Bot starts with tokens from environment variables
- [ ] Tokens are saved to file on first run
- [ ] Bot starts with tokens from file on restart
- [ ] Token refresh works (check logs after 50 min)
- [ ] New refresh token is saved after refresh

**Error Handling:**
- [ ] Rate limit error shows friendly message
- [ ] Network error shows retry message
- [ ] Invalid credentials show error
- [ ] Missing article shows not found

**Deployment:**
- [ ] Docker build succeeds
- [ ] Container starts without errors
- [ ] Railway deployment succeeds
- [ ] Railway volume persists tokens
- [ ] Logs are properly colored (blue/red)


---

## Security Considerations

### Authentication Security

#### OAuth Token Storage
- **File location:** `fortnox_tokens.json` (not in git)
- **File permissions:** Read/write for bot user only
- **Thread safety:** File locking (fcntl) prevents corruption
- **Railway:** Stored in persistent volume (not ephemeral container)
- **Fallback:** Environment variables act as recovery mechanism

#### Token Rotation
- **Access tokens:** Expire after ~1 hour
- **Refresh tokens:** Single-use, rotate on each refresh
- **Critical:** ALWAYS save new refresh token immediately
- **Failure mode:** If refresh token not saved, must regenerate from scratch

#### Secrets Management
- **Never commit:** `.env`, `fortnox_tokens.json`
- **Railway:** Use environment variable UI (encrypted at rest)
- **Local dev:** `.env` file with restricted permissions (chmod 600)
- **Docker:** Mount secrets as files or env vars, never bake into image

### Container Security

#### Non-Root Execution
- **Build:** Starts as root (required for volume permissions)
- **Runtime:** Drops to `botuser` (uid 1000) before running app
- **Why:** Limits damage if container is compromised

#### Minimal Image
- **Base:** `python:3.11-slim` (smaller attack surface)
- **No dev tools:** Only production dependencies
- **No shell access:** No bash/ssh in production

### Network Security

#### Slack Connection
- **Protocol:** WebSocket (Socket Mode) over TLS
- **Authentication:** App-level token + signing secret
- **No webhooks:** No inbound HTTP required (firewall-friendly)

#### Fortnox API
- **Protocol:** HTTPS only
- **Authentication:** OAuth 2.0 with client secret
- **Rate limiting:** Enforced by Fortnox (300 req/min)

### Input Validation

#### Slack Commands
```python
# Validate article number (prevent injection)
article_number = command.get('text', '').strip()
if not article_number.isalnum():
    return error_message

# Validate numeric inputs
try:
    minimum_stock = int(parts[0])
except ValueError:
    return error_message
```

#### API Responses
```python
# Always validate data types
quantity = safe_float(article.get('QuantityInStock'), default=0.0)

# Check for None/missing keys
description = article.get('Description', 'N/A')
```

### Error Handling Security

#### Don't Leak Secrets
```python
# ❌ BAD - Exposes token in logs
logger.error(f"Failed with token: {access_token}")

# ✅ GOOD - Generic message
logger.error("Authentication failed")
```

#### Don't Expose Internal Errors
```python
# ❌ BAD - Shows stack trace to user
respond(f"Error: {traceback.format_exc()}")

# ✅ GOOD - Generic user message, detailed logs
logger.error(f"Error: {e}", exc_info=True)
respond("An error occurred. Please try again.")
```

### Logging Security

#### No Sensitive Data
- Never log tokens, secrets, passwords
- Truncate tokens in logs: `token[:10]...`
- Log relevant context without exposing credentials

#### Audit Trail
- Log all command invocations
- Log authentication events
- Log rate limit hits
- Include timestamps, user IDs (Slack), action types

### Deployment Security

#### Railway Platform
- **Isolation:** Container sandboxing
- **Secrets:** Encrypted environment variables
- **HTTPS:** All traffic encrypted
- **Volumes:** Persistent storage with access control

#### Container Hardening
```dockerfile
# Read-only root filesystem (except /data volume)
# Non-root user execution
# Minimal dependencies
# No unnecessary capabilities
```

### Monitoring & Alerts

#### What to Monitor
- Token refresh failures (indicates auth issues)
- Rate limit hits (indicates usage patterns)
- API errors (indicates service issues)
- Container restarts (indicates crashes)

#### Recommended Alerts
- Token refresh failed > 3 times in 1 hour
- Rate limit hit > 5 times in 1 hour
- Container crashed > 2 times in 10 minutes
- No successful API calls in 1 hour

### Incident Response

#### Token Compromise
1. Revoke tokens in Fortnox Developer Portal
2. Generate new tokens with `scripts/get_fortnox_token.py`
3. Update Railway environment variables
4. Redeploy service
5. Monitor logs for suspicious activity

#### Container Breach
1. Check Railway logs for unauthorized access
2. Rotate all secrets (Slack + Fortnox)
3. Review access logs in Slack workspace
4. Update container image with security patches
5. Redeploy with new credentials


---

## Dependencies

### Python Requirements (`requirements.txt`)

```
slack-bolt==1.18.0    # Slack Bot framework (Socket Mode)
python-dotenv==1.0.0  # Environment variable management
requests==2.31.0      # HTTP client for Fortnox API
```

### Dependency Notes

**slack-bolt**
- Provides Socket Mode support (no webhooks needed)
- Handles Slack API authentication
- Command handler decorators (`@app.command`)

**python-dotenv**
- Loads `.env` file into `os.environ`
- Development convenience (Railway uses native env vars)

**requests**
- Simple HTTP client for REST APIs
- Built-in timeout support
- JSON handling

### System Requirements

**Python:** 3.11 or higher
**OS:** Linux (tested), macOS, Windows (with WSL)
**Memory:** ~100MB runtime
**Disk:** ~50MB (app + dependencies)

---

## Implementation Notes

### Critical Implementation Details

#### 1. Token Rotation Must Save Both Tokens
```python
# ❌ WRONG - Only saves access token
if new_access_token:
    token_manager.save_tokens(new_access_token, old_refresh_token)

# ✅ CORRECT - Saves new refresh token if provided
if new_refresh_token:
    token_manager.save_tokens(new_access_token, new_refresh_token)
else:
    token_manager.save_tokens(new_access_token, old_refresh_token)
```

**Why:** Fortnox rotates refresh tokens. If you don't save the new one, the old one becomes invalid.

#### 2. QuantityInStock Type Handling
```python
# ❌ WRONG - Assumes number
stock = article['QuantityInStock']
if stock > 0:  # May fail if string

# ✅ CORRECT - Always convert
stock = float(article.get('QuantityInStock', 0))
if stock > 0:
```

**Why:** Fortnox API sometimes returns strings, sometimes numbers.

#### 3. Pagination Must Check Length
```python
# ❌ WRONG - Infinite loop if API returns empty on error
while True:
    articles = fetch_page(offset)
    all_articles.extend(articles)
    offset += 500

# ✅ CORRECT - Break on empty or short page
while True:
    articles = fetch_page(offset)
    if not articles:
        break
    all_articles.extend(articles)
    if len(articles) < 500:
        break  # Last page
    offset += 500
```

**Why:** Prevents infinite loops and detects end of results.

#### 4. File Locking for Thread Safety
```python
# ❌ WRONG - Race condition between read/write
def save_tokens(access, refresh):
    with open('tokens.json', 'w') as f:
        json.dump({...}, f)

# ✅ CORRECT - Exclusive lock
def save_tokens(access, refresh):
    with open('tokens.json', 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        json.dump({...}, f)
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**Why:** Token refresh thread and main thread may access file simultaneously.

#### 5. Railway Volume Detection
```python
# Check for Railway volume
volume_path = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
if volume_path:
    token_file = os.path.join(volume_path, 'fortnox_tokens.json')
else:
    token_file = './fortnox_tokens.json'
```

**Why:** Railway volumes have a specific mount path, local dev uses current directory.

### Performance Considerations

**Article Fetching:**
- First command: ~2-3 seconds (fetches all ~519 articles)
- Subsequent commands: Instant (cached in memory)
- Restart: Must re-fetch (no persistent cache)

**Price List Lookups:**
- Find HoReCa list: Once on startup
- Lookup price: Per article, per request (~50-100ms each)
- Consider implementing price cache if performance issues

**Token Refresh:**
- Happens every 50 minutes
- Non-blocking (background thread)
- Takes ~200ms per refresh

### Slack-Specific Implementation

**Socket Mode:**
- Maintains persistent WebSocket connection
- Slack sends commands over WebSocket
- No need for public URL/webhooks
- Automatic reconnection on disconnect

**Command Acknowledgment:**
```python
@app.command("/fortnox-stock")
def handle_stock_command(ack, command, respond):
    ack()  # MUST call within 3 seconds
    # ... rest of logic ...
    respond(message)  # Can take longer
```

**Why:** Slack requires acknowledgment within 3 seconds or command fails.

### Mobile Formatting Detection

```python
def is_mobile_view(text_width):
    """Detect if response should use mobile format"""
    return text_width <= 70  # Characters per line
```

**Desktop Format:**
- More columns
- Longer descriptions
- More detailed info

**Mobile Format:**
- Fewer columns
- Truncated text
- Essential info only

---

## Reimplementation Checklist

When reimplementing this application, ensure:

### Core Functionality
- [ ] Slack Socket Mode integration
- [ ] Three commands: `/fortnox-stock`, `/fortnox-article`, `/fortnox-kegs`
- [ ] Fortnox API pagination (500 per page)
- [ ] Rate limit detection and handling
- [ ] HoReCa price list lookup

### Token Management
- [ ] Token file with fcntl locking
- [ ] Save BOTH access and refresh tokens
- [ ] Background thread refreshes every 50 minutes
- [ ] Environment variable fallback
- [ ] Railway volume detection

### Error Handling
- [ ] FortnoxRateLimitError custom exception
- [ ] User-friendly error messages
- [ ] Detailed logging with exc_info
- [ ] Timeout on all HTTP requests (10s)

### Formatting
- [ ] Mobile vs desktop detection
- [ ] Emoji status indicators
- [ ] Aligned columns (monospace formatting)
- [ ] Swedish currency format (1,234 kr)

### Deployment
- [ ] Dockerfile with non-root user
- [ ] Entrypoint script for permission fixing
- [ ] railway.json configuration
- [ ] .railwayignore exclusions
- [ ] Volume support for token persistence

### Logging
- [ ] Split streams: stdout (INFO/DEBUG), stderr (WARNING/ERROR)
- [ ] Structured log format with timestamps
- [ ] No sensitive data in logs
- [ ] Emoji indicators for key events

### Security
- [ ] No secrets in git
- [ ] Input validation
- [ ] Non-root container execution
- [ ] Token truncation in logs

---

## Conclusion

This specification document provides complete details for reimplementing the Fortnox Slack Bot. Key design principles:

1. **Resilience** - Token fallback, error recovery, automatic retry
2. **Security** - Non-root execution, secret management, input validation
3. **Usability** - Clear commands, mobile-friendly, helpful errors
4. **Maintainability** - Clean structure, comprehensive logging, good docs
5. **Performance** - Pagination, caching, background refresh

For additional context, refer to:
- `docs/QUICKSTART.md` - Step-by-step setup
- `docs/FORTNOX_SETUP.md` - Fortnox OAuth details
- `docs/RAILWAY_DEPLOYMENT.md` - Railway platform specifics
- `docs/AGENTS.md` - AI agent development notes

**Version:** 1.0  
**Last Updated:** October 25, 2025  
**Maintained by:** Project contributors
