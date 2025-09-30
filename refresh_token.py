#!/usr/bin/env python3
"""
Fortnox Access Token Refresh Script

Automatically refreshes the Fortnox access token using the refresh token.
This script should be run periodically (e.g., every 50 minutes via cron) to ensure
the access token doesn't expire.

For service accounts, tokens expire after 1 hour.
"""
import os
import sys
import requests
import logging
from dotenv import load_dotenv, set_key
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def refresh_access_token():
    """
    Refresh the Fortnox access token using the refresh token
    
    Returns:
        str: New access token if successful, None otherwise
    """
    # Load environment variables
    env_file = Path(".env")
    load_dotenv(env_file)
    
    # Get credentials
    refresh_token = os.getenv("FORTNOX_REFRESH_TOKEN")
    client_id = os.getenv("FORTNOX_CLIENT_ID")
    client_secret = os.getenv("FORTNOX_CLIENT_SECRET")
    
    # Validate required variables
    if not all([refresh_token, client_id, client_secret]):
        logger.error("Missing required environment variables:")
        if not refresh_token:
            logger.error("  - FORTNOX_REFRESH_TOKEN not set")
        if not client_id:
            logger.error("  - FORTNOX_CLIENT_ID not set")
        if not client_secret:
            logger.error("  - FORTNOX_CLIENT_SECRET not set")
        logger.error("Please update your .env file")
        return None
    
    logger.info("Refreshing Fortnox access token...")
    
    try:
        # Make token refresh request
        response = requests.post(
            "https://apps.fortnox.se/oauth-v1/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")  # Fortnox may issue a new one
            
            if not new_access_token:
                logger.error("No access token in response")
                return None
            
            # Update .env file with new access token
            logger.info("Updating .env file with new access token...")
            set_key(env_file, "FORTNOX_ACCESS_TOKEN", new_access_token)
            
            # Update refresh token if a new one was issued
            if new_refresh_token and new_refresh_token != refresh_token:
                logger.info("Updating refresh token (new token issued)...")
                set_key(env_file, "FORTNOX_REFRESH_TOKEN", new_refresh_token)
            
            logger.info("✅ Access token refreshed successfully")
            logger.info(f"   New token: {new_access_token[:10]}...")
            logger.info(f"   Expires in: {data.get('expires_in', 'unknown')} seconds")
            
            return new_access_token
            
        else:
            logger.error(f"❌ Failed to refresh token: HTTP {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while refreshing token: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return None


def verify_new_token(access_token: str) -> bool:
    """
    Verify the new access token works by making a test API call
    
    Args:
        access_token: The access token to verify
        
    Returns:
        bool: True if token works, False otherwise
    """
    client_secret = os.getenv("FORTNOX_CLIENT_SECRET")
    
    try:
        logger.info("Verifying new token...")
        response = requests.get(
            "https://api.fortnox.se/3/articles",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Client-Secret": client_secret,
                "Content-Type": "application/json"
            },
            params={"limit": 1},  # Just fetch 1 article to test
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("✅ Token verified successfully")
            return True
        else:
            logger.warning(f"⚠️  Token verification returned HTTP {response.status_code}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  Token verification failed: {e}")
        return False


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("Fortnox Token Refresh Script")
    logger.info("=" * 60)
    
    # Refresh the token
    new_token = refresh_access_token()
    
    if new_token:
        # Verify it works
        if verify_new_token(new_token):
            logger.info("=" * 60)
            logger.info("✅ Token refresh completed successfully")
            logger.info("=" * 60)
            sys.exit(0)
        else:
            logger.warning("Token refreshed but verification failed")
            sys.exit(1)
    else:
        logger.error("=" * 60)
        logger.error("❌ Token refresh failed")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
