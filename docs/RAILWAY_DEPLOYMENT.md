# Railway.app Deployment Guide

## Prerequisites
- GitHub account
- Railway.app account (free tier works)
- This repository pushed to GitHub

## Step-by-Step Deployment

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Create New Project on Railway

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `fortnox_slack_bot` repository

### 3. Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

**Required Variables:**
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
FORTNOX_REFRESH_TOKEN=your-refresh-token
FORTNOX_CLIENT_ID=your-client-id
FORTNOX_CLIENT_SECRET=your-client-secret
```

**Important:** 
- Get these values from your local `.env` file
- Don't commit `.env` to GitHub!
- Railway will use these environment variables instead

### 4. Deploy

Railway will automatically:
- Detect Python project
- Install dependencies from `requirements.txt`
- Run `python -m src.bot` (from Procfile)

### 5. Verify Deployment

Check the **Logs** tab in Railway dashboard. You should see:
```
Starting Fortnox Slack Bot...
Initializing Fortnox connection...
Refreshing Fortnox access token...
✅ Found HoReCa price list with code: B
🔄 Refreshing price cache from price list B...
✅ Cached XX prices from HoReCa price list
✅ Fortnox Slack Bot is running!
```

## Features on Railway

✅ **Auto-refresh token**: Runs every 50 minutes automatically
✅ **Token rotation handling**: NEW - Bot saves refresh tokens to file (fixes invalid_grant error)
✅ **Always-on bot**: No server to manage
✅ **Auto-restart**: If bot crashes, Railway restarts it
✅ **Logs**: View all bot activity in Railway dashboard
✅ **Free tier**: Includes 500 hours/month (enough for 24/7 operation)

## Token Management (NEW - 2025-10-25)

The bot uses persistent file storage for tokens (`fortnox_tokens.json`) to handle Fortnox's token rotation.

### ⚠️ CRITICAL: Railway Volumes Required

**Railway containers are ephemeral** - the token file is lost on every deployment!

Without a volume:
- ❌ Bot reinitializes from environment variables on EVERY deploy
- ❌ If env vars have old tokens → "invalid_grant" error
- ❌ You must update env vars with fresh tokens after each deployment

**SOLUTION**: Set up a Railway Volume for persistent storage.

👉 **See [RAILWAY_VOLUME_SETUP.md](./RAILWAY_VOLUME_SETUP.md) for step-by-step instructions**

### How Token Management Works

With volume:
- ✅ **First deploy**: Bot creates `fortnox_tokens.json` from environment variables
- ✅ **Token rotation**: New refresh tokens saved to volume (survives redeploys)
- ✅ **Redeploys**: Bot loads existing tokens from volume
- ✅ **No manual updates**: Tokens persist automatically

Without volume:
- ⚠️ Token file recreated on every deploy from (potentially stale) env vars
- ⚠️ Must update env vars manually when tokens change

## Troubleshooting

### Bot not responding
- Check Railway logs for errors
- Verify all environment variables are set
- Make sure SLACK_APP_TOKEN is correct (Socket Mode)

### Token refresh fails (invalid_grant error)
**This should no longer happen with the new token file system!**

If you still see this:
1. Run `./venv/bin/python scripts/get_fortnox_token.py` locally to get fresh tokens
2. Update FORTNOX_REFRESH_TOKEN in Railway environment variables
3. Redeploy (Railway will recreate `fortnox_tokens.json` from env vars)
4. Check logs for "Checking token storage..." and "Tokens loaded from file"

### Rate limit errors
- Bot automatically handles rate limits
- Wait 3-5 minutes and try again
- Check logs for "Rate limit exceeded" messages

## Manual Redeploy

To trigger a redeploy after code changes:
1. Push to GitHub
2. Railway auto-deploys on push, or
3. Click **"Deploy"** button in Railway dashboard

## Monitoring

Check Railway dashboard regularly:
- **Metrics**: CPU/Memory usage
- **Logs**: Bot activity and errors
- **Deployments**: History of all deploys
