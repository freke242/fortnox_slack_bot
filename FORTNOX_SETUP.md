# Fortnox Service Account Setup Guide

This guide explains how to set up a Fortnox service account for the Slack bot. Service accounts are the recommended approach for server-to-server integrations in company environments.

## 🎯 Why Use Service Accounts?

✅ **Not tied to a person** - The integration continues to work even if employees leave  
✅ **Dedicated permissions** - Specific permissions for the service, not user-based  
✅ **More secure** - System administrator control over authorization  
✅ **Best practice** - Recommended by Fortnox for automated integrations  

## 📋 Prerequisites

- System administrator access in your Fortnox account
- Access to the Fortnox Developer Portal

## 🚀 Quick Setup (Automated Script)

**NEW!** We provide an automated script that handles the OAuth flow for you:

```bash
# 1. Add your credentials to .env
cp .env.example .env
nano .env  # Add FORTNOX_CLIENT_ID and FORTNOX_CLIENT_SECRET

# 2. Run the automated script
python get_fortnox_token.py
```

The script will:
1. ✅ Read your CLIENT_ID and CLIENT_SECRET from .env
2. ✅ Start a local web server for the OAuth callback
3. ✅ Open your browser for authorization (system admin must approve)
4. ✅ Exchange the authorization code for tokens
5. ✅ Automatically save ACCESS_TOKEN and REFRESH_TOKEN to .env

**If you prefer to do it manually, continue with Step 1 below.**

---

## Step 1: Configure Your Integration in Developer Portal

### 1.1 Log in to Developer Portal

1. Go to https://developer.fortnox.se/
2. Sign in with your Fortnox credentials
3. Navigate to your integration (or create a new one)

### 1.2 Enable Service Account Option

1. In your integration settings, find **"Authorization settings"**
2. Select **"Only administrator"** option
3. This ensures only system administrators can authorize the service account
4. Save your changes

### 1.3 Note Your Credentials

Copy and save these values (you'll need them later):
- **Client ID** - Your application identifier
- **Client Secret** - Your application secret (keep this secure!)

## Step 2: Authorize the Service Account

You need to go through the OAuth flow with the special `account_type=service` parameter.

### 2.1 Build the Authorization URL

Create the authorization URL with this format:

```
https://apps.fortnox.se/oauth-v1/auth?
  client_id=YOUR_CLIENT_ID
  &redirect_uri=YOUR_REDIRECT_URI
  &scope=article
  &state=RANDOM_STRING
  &access_type=offline
  &account_type=service
  &response_type=code
```

**Parameters:**
- `client_id` - Your Client ID from Developer Portal
- `redirect_uri` - Your registered redirect URI (e.g., `http://localhost:3000/callback`)
- `scope` - API scopes needed (e.g., `article` for inventory)
- `state` - Random string for security (generate a UUID)
- `access_type` - Set to `offline` to get a refresh token
- `account_type` - **Set to `service`** (this is the key parameter!)
- `response_type` - Set to `code`

### 2.2 Complete Authorization

1. **System administrator** must open the authorization URL in a browser
2. Log in to Fortnox (if not already logged in)
3. Review the permissions requested
4. Click **"Authorize"**
5. You'll be redirected to your `redirect_uri` with an authorization code

Example redirect:
```
http://localhost:3000/callback?code=AUTHORIZATION_CODE&state=YOUR_STATE
```

Copy the **authorization code** from the URL.

## Step 3: Exchange Code for Access Token

### 3.1 Make Token Request

Use curl or a tool like Postman to exchange the authorization code for an access token:

```bash
curl -X POST https://apps.fortnox.se/oauth-v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

### 3.2 Response

You'll receive a JSON response like:

```json
{
  "access_token": "abc123...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "xyz789..."
}
```

**Important:** Save both tokens securely:
- `access_token` - Used for API calls (expires in 1 hour)
- `refresh_token` - Used to get new access tokens (doesn't expire)

## Step 4: Configure the Bot

### 4.1 Update .env File

Edit your `.env` file with the credentials:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

# Fortnox Service Account Configuration
FORTNOX_ACCESS_TOKEN=abc123...
FORTNOX_CLIENT_SECRET=your-client-secret

# Optional: Store refresh token for automatic renewal
FORTNOX_REFRESH_TOKEN=xyz789...
FORTNOX_CLIENT_ID=your-client-id
```

### 4.2 Test the Connection

Run the test script to verify everything works:

```bash
python test_fortnox.py
```

You should see:
```
✅ Successfully retrieved X articles
✅ All tests passed! Your Fortnox connection is working!
```

## Step 5: Handle Token Refresh (Optional but Recommended)

Access tokens expire after 1 hour. For production use, implement automatic token refresh.

### Create a Token Refresh Script

```python
# refresh_token.py
import os
import requests
from dotenv import load_dotenv, set_key

load_dotenv()

def refresh_access_token():
    """Refresh the Fortnox access token using the refresh token"""
    
    response = requests.post(
        "https://apps.fortnox.se/oauth-v1/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.getenv("FORTNOX_REFRESH_TOKEN"),
            "client_id": os.getenv("FORTNOX_CLIENT_ID"),
            "client_secret": os.getenv("FORTNOX_CLIENT_SECRET")
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Update .env file with new token
        set_key(".env", "FORTNOX_ACCESS_TOKEN", data["access_token"])
        print("✅ Access token refreshed successfully")
        return data["access_token"]
    else:
        print(f"❌ Failed to refresh token: {response.text}")
        return None

if __name__ == "__main__":
    refresh_access_token()
```

### Set Up Automatic Refresh

Add a cron job to refresh the token every 50 minutes:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths):
*/50 * * * * cd /home/frke/git/fortnox_slack_bot && /home/frke/git/fortnox_slack_bot/venv/bin/python refresh_token.py
```

## 🔒 Security Best Practices

1. **Never commit tokens** - Keep `.env` out of version control
2. **Secure file permissions:**
   ```bash
   chmod 600 .env
   ```
3. **Use refresh tokens** - Don't manually update access tokens
4. **Monitor access** - Review Fortnox audit logs regularly
5. **Rotate secrets** - Periodically regenerate client secrets

## 📚 Required Scopes

For the inventory bot, you need at least:

- `article` - Read articles/inventory data

If you want to add more features later, you might need:
- `customer` - Customer data
- `supplier` - Supplier data
- `order` - Order management
- `invoice` - Invoice data

Add scopes to the authorization URL: `scope=article customer supplier`

## 🔧 Troubleshooting

### "Invalid account_type parameter"

✅ **Solution:** Ensure you enabled "Only administrator" in Developer Portal settings

### "Unauthorized" errors

✅ **Solution:** Check that:
- Access token is valid (not expired)
- Client Secret is correct
- Service account has necessary permissions

### "Access token expired"

✅ **Solution:** Use the refresh token to get a new access token (see Step 5)

### "Insufficient permissions"

✅ **Solution:** The system administrator needs to re-authorize with additional scopes

## 📖 Additional Resources

- [Fortnox OAuth Documentation](https://www.fortnox.se/developer/authorization)
- [Service Accounts Blog Post](https://www.fortnox.se/developer/blog/service-accounts)
- [API Documentation](https://api.fortnox.se/apidocs)

## ✅ Verification Checklist

Before running the bot in production:

- [ ] Service account created and authorized by system administrator
- [ ] Access token and Client Secret stored in `.env`
- [ ] Token refresh mechanism implemented (recommended)
- [ ] Connection tested with `python test_fortnox.py`
- [ ] File permissions secured (`chmod 600 .env`)
- [ ] Documentation shared with your team

## 🎉 You're Done!

Your bot is now configured with a Fortnox service account. Start the bot:

```bash
python app.py
```

And test it in Slack:
```
/fortnox-stock
```

For deployment to production, see [DEPLOYMENT.md](DEPLOYMENT.md).
