# Railway Volume Setup for Token Persistence

## Problem

Railway containers are **ephemeral** - they're recreated on every deployment. This means:
- ❌ `fortnox_tokens.json` is lost on each redeploy
- ❌ Bot reinitializes from stale environment variables
- ❌ Token refresh fails with "invalid_grant" error

## Solution: Railway Volume

Railway Volumes provide **persistent storage** that survives redeployments.

### Step 1: Create a Volume

In Railway dashboard:

1. Go to your project
2. Click **"+ New"** → **"Volume"**
3. Set:
   - **Name**: `fortnox-tokens`
   - **Mount Path**: `/data`
4. Click **"Add Volume"**

### Step 2: Connect Volume to Service

1. Go to your bot service
2. Click **"Settings"** → **"Volumes"**
3. Click **"Mount Volume"**
4. Select `fortnox-tokens`
5. Mount path: `/data`
6. Save

### Step 3: Verify Volume Mount

Railway **automatically sets** `RAILWAY_VOLUME_MOUNT_PATH=/data` when you mount the volume.

You can verify it in **Variables** tab - you should see it listed (you didn't create it manually).

The bot will automatically detect this variable and use `/data/fortnox_tokens.json` for storage.

### Step 4: Initialize with Fresh Tokens

After setting up the volume, you need fresh tokens:

**Option A: From local machine**
```bash
./venv/bin/python get_fortnox_token.py
```

Then copy the tokens from `fortnox_tokens.json` to Railway environment variables:
- `FORTNOX_ACCESS_TOKEN`
- `FORTNOX_REFRESH_TOKEN`

**Option B: Use Railway console**
```bash
# In Railway service console
python get_fortnox_token.py
```

Note: This won't work on Railway because it requires a browser for OAuth.

### Step 5: Redeploy

Click **"Redeploy"** in Railway. You should see:
```
Using Railway volume for tokens: /data/fortnox_tokens.json
Initializing token file from environment variables...
✅ Tokens saved to /data/fortnox_tokens.json
```

## How It Works

1. **First deploy with volume**: Bot creates `/data/fortnox_tokens.json` from env vars
2. **Token refresh (50 min)**: New tokens saved to `/data/fortnox_tokens.json`
3. **Redeploy**: Volume persists → Bot loads existing tokens → No reinitialization needed! ✅

## Verification

Check Railway logs for:
```
✅ Using Railway volume for tokens: /data/fortnox_tokens.json
✅ Tokens loaded from file
```

If you see "Initializing token file from environment variables" on EVERY deploy, the volume isn't working.

## Without Volume (Current Situation)

If you don't set up a volume:
- ⚠️ Update Railway env vars EVERY time you get fresh tokens
- ⚠️ Bot will reinitialize on every deploy
- ⚠️ Eventually tokens in env vars will be too old → "invalid_grant"

## Recommended: Use Volume

✅ Set up the volume once
✅ Tokens persist across deployments
✅ No manual token updates needed
✅ Bot works reliably long-term
