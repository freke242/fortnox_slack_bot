# ⚡ Quick Start Guide

Get your Fortnox Slack Bot running in **10 minutes**!

## 📋 Prerequisites

- Python 3.8+ installed
- Slack workspace (admin access to install apps)
- Fortnox account (system administrator access for service account)
- Git installed

---

## 🚀 Step 1: Setup (2 minutes)

```bash
# Clone and setup
git clone <your-repo-url>
cd fortnox_slack_bot
./setup.sh
```

This creates a virtual environment and installs all dependencies.

---

## 🔑 Step 2: Configure Slack App (3 minutes)

### 2.1 Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it **"Fortnox Bot"** and select your workspace

### 2.2 Enable Socket Mode

1. **Settings** → **Socket Mode** → Toggle **ON**
2. Click **"Generate App-Level Token"**
3. Name it "socket-token", add scope `connections:write`
4. **Copy the token** (starts with `xapp-`)

### 2.3 Add Bot Scopes

1. **OAuth & Permissions** → **Bot Token Scopes**
2. Add these scopes:
   - `chat:write`
   - `commands`
   - `app_mentions:read`

### 2.4 Install App

1. **OAuth & Permissions** → **Install to Workspace**
2. Click **"Allow"**
3. **Copy Bot Token** (starts with `xoxb-`)

### 2.5 Get Signing Secret

1. **Basic Information** → **App Credentials**
2. **Copy Signing Secret**

### 2.6 Create Slash Commands

1. **Slash Commands** → **Create New Command**

Create these two commands (Request URL can be blank):

| Command | Description | Usage Hint |
|---------|-------------|------------|
| `/fortnox-stock` | List articles in stock | `[minimum quantity]` |
| `/fortnox-article` | Get article details | `[article number]` |

---

## 🏢 Step 3: Configure Fortnox (3 minutes)

### 3.1 Get Fortnox Credentials

1. Go to https://developer.fortnox.se/
2. Create or select your integration
3. **Important:** Enable **"Only administrator"** (for service accounts)
4. Add redirect URI: `http://localhost:33140/callback`
5. Enable scopes: `companyinformation`, `article`, `warehouse`, `warehousecustomdocument`
6. Copy **Client ID** and **Client Secret**

### 3.2 Setup Environment File

```bash
cp .env.example .env
nano .env
```

Add your credentials:
```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_APP_TOKEN=xapp-your-app-token-here

# Fortnox Configuration
FORTNOX_CLIENT_ID=your-client-id-here
FORTNOX_CLIENT_SECRET=your-client-secret-here
```

### 3.3 Get Fortnox Tokens (Automated!)

```bash
source venv/bin/activate
python get_fortnox_token.py
```

**What happens:**
1. ✅ Opens browser for authorization
2. ✅ Log in as **system administrator**
3. ✅ Approve the permissions
4. ✅ Tokens automatically saved to `.env`

---

## ✅ Step 4: Test & Run (2 minutes)

### 4.1 Test Fortnox Connection

```bash
python test_fortnox.py
```

You should see your articles listed.

### 4.2 Start the Bot

```bash
python app.py
```

You should see:
```
✅ Fortnox Slack Bot is running!
⚡️ Bolt app is running!
```

### 4.3 Test in Slack

In any Slack channel:
```
/fortnox-stock
```

You should see your inventory! 🎉

---

## 🔄 Step 5: Setup Token Auto-Refresh (1 minute)

Access tokens expire after 1 hour. Setup automatic refresh:

```bash
crontab -e
```

Add this line:
```bash
*/50 * * * * cd /home/frke/git/fortnox_slack_bot && /home/frke/git/fortnox_slack_bot/venv/bin/python refresh_token.py >> /tmp/fortnox_refresh.log 2>&1
```

(Adjust the path to match your installation directory)

---

## 🎯 Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/fortnox-stock` | List all articles in stock | `/fortnox-stock` |
| `/fortnox-stock [min]` | Filter by minimum quantity | `/fortnox-stock 10` |
| `/fortnox-article [num]` | Get article details | `/fortnox-article 12345` |
| `@Bot help` | Show help message | `@Fortnox Bot help` |

---

## 🚀 Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Systemd service setup
- Docker deployment
- Cloud platform deployment

---

## ❓ Troubleshooting

### Bot not responding in Slack

1. Check bot is running: Look for "⚡️ Bolt app is running!" message
2. Verify slash commands are created in Slack App settings
3. Check Socket Mode is enabled
4. Reinstall the app to workspace

### Fortnox connection errors

1. Check tokens: `python test_fortnox.py`
2. Verify scopes are enabled in Developer Portal
3. Check token hasn't expired (refresh if needed)
4. Ensure service account is properly authorized

### "Invalid grant" error

This usually means:
- Client Secret is incorrect
- Redirect URI doesn't match
- Authorization code already used or expired

Solution: Regenerate Client Secret and run `python get_fortnox_token.py` again

---

## 📚 More Documentation

- [README.md](README.md) - Complete documentation
- [FORTNOX_SERVICE_ACCOUNT_SETUP.md](FORTNOX_SERVICE_ACCOUNT_SETUP.md) - Detailed Fortnox setup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines

---

## 🎉 You're Done!

Your Fortnox Slack Bot is now running! Enjoy managing your inventory from Slack! 🚀

For questions or issues, check the troubleshooting section or create an issue in the repository.
