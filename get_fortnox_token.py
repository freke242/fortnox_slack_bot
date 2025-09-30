#!/usr/bin/env python3
"""
Fortnox Service Account Token Generator

This script automates the OAuth flow to get access and refresh tokens
for a Fortnox service account. It will:
1. Read your CLIENT_ID and CLIENT_SECRET from .env
2. Start a local web server to receive the OAuth callback
3. Open your browser for authorization
4. Exchange the code for tokens
5. Save tokens to your .env file

Usage:
    python get_fortnox_token.py
"""

import os
import sys
import webbrowser
import secrets
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path

# Configuration
REDIRECT_URI = "http://localhost:33140/callback"
PORT = 33140

# Global variables to capture the authorization code
auth_code = None
auth_state = None
server_should_stop = False


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback"""
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass
    
    def do_GET(self):
        """Handle the OAuth redirect"""
        global auth_code, auth_state, server_should_stop
        
        # Parse the URL
        parsed = urlparse(self.path)
        
        if parsed.path == '/callback':
            # Extract query parameters
            params = parse_qs(parsed.query)
            
            if 'code' in params:
                auth_code = params['code'][0]
                auth_state = params.get('state', [None])[0]
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>Authorization Successful</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #4CAF50;">✅ Authorization Successful!</h1>
                    <p>You can close this window and return to your terminal.</p>
                    <p style="color: #666; font-size: 12px;">Authorization code received. Exchanging for tokens...</p>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
                server_should_stop = True
                
            elif 'error' in params:
                error = params['error'][0]
                error_desc = params.get('error_description', ['Unknown error'])[0]
                
                # Send error response
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = f"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: #f44336;">❌ Authorization Failed</h1>
                    <p><strong>Error:</strong> {error}</p>
                    <p>{error_desc}</p>
                    <p>Please return to your terminal and try again.</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
                server_should_stop = True
        else:
            # Send 404 for other paths
            self.send_response(404)
            self.end_headers()


def generate_authorization_url(client_id: str, state: str) -> str:
    """
    Generate the Fortnox OAuth authorization URL
    
    Args:
        client_id: Fortnox client ID
        state: Random state string for security
        
    Returns:
        Authorization URL
    """
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        # Scopes for warehouse: article, warehouse, warehousecustomdocument + companyinformation base
        'scope': 'companyinformation article warehouse warehousecustomdocument',
        'state': state,
        'access_type': 'offline',
        'account_type': 'service',  # Service account for production use
        'response_type': 'code'
    }
    
    base_url = 'https://apps.fortnox.se/oauth-v1/auth'
    return f"{base_url}?{urlencode(params)}"


def exchange_code_for_tokens(code: str, client_id: str, client_secret: str) -> dict:
    """
    Exchange authorization code for access and refresh tokens
    
    Args:
        code: Authorization code from OAuth callback
        client_id: Fortnox client ID
        client_secret: Fortnox client secret
        
    Returns:
        Dictionary with access_token and refresh_token
    """
    print("\n🔄 Exchanging authorization code for tokens...")
    print(f"   Using redirect_uri: {REDIRECT_URI}")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Client Secret: {client_secret[:5]}...{client_secret[-3:]}")
    print(f"   Code: {code[:20]}...")
    
    # Create Basic Auth credentials (Base64 of client_id:client_secret)
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    print(f"   Using Basic Auth")
    
    # Save curl command for manual testing
    curl_cmd = f'''curl -X POST https://apps.fortnox.se/oauth-v1/token \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -H "Authorization: Basic {encoded_credentials}" \\
  -d "grant_type=authorization_code" \\
  -d "code={code}" \\
  -d "redirect_uri={REDIRECT_URI}"'''
    
    with open('debug_curl_command.sh', 'w') as f:
        f.write(curl_cmd)
    print("   💾 Curl command saved to debug_curl_command.sh")
    
    try:
        response = requests.post(
            'https://apps.fortnox.se/oauth-v1/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {encoded_credentials}'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Token exchange failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error exchanging code: {e}")
        return None


def save_tokens_to_env(access_token: str, refresh_token: str):
    """
    Save tokens to .env file
    
    Args:
        access_token: Fortnox access token
        refresh_token: Fortnox refresh token
    """
    env_file = Path('.env')
    
    print("\n💾 Saving tokens to .env file...")
    
    try:
        set_key(env_file, 'FORTNOX_ACCESS_TOKEN', access_token)
        set_key(env_file, 'FORTNOX_REFRESH_TOKEN', refresh_token)
        print("✅ Tokens saved successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to save tokens: {e}")
        return False


def main():
    """Main function"""
    print("=" * 70)
    print("🔐 Fortnox Service Account Token Generator")
    print("=" * 70)
    print()
    
    # Load environment variables
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        print("   Please copy .env.example to .env first:")
        print("   cp .env.example .env")
        sys.exit(1)
    
    load_dotenv(env_file)
    
    # Get credentials from .env
    client_id = os.getenv('FORTNOX_CLIENT_ID')
    client_secret = os.getenv('FORTNOX_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing required credentials in .env file!")
        print()
        print("Please add the following to your .env file:")
        print("   FORTNOX_CLIENT_ID=your-client-id-here")
        print("   FORTNOX_CLIENT_SECRET=your-client-secret-here")
        print()
        print("Get these from: https://developer.fortnox.se/")
        sys.exit(1)
    
    print("✅ Credentials loaded from .env")
    print(f"   Client ID: {client_id[:10]}...")
    print()
    
    # Generate state for security
    state = secrets.token_urlsafe(32)
    
    # Generate authorization URL
    auth_url = generate_authorization_url(client_id, state)
    
    print("📋 Instructions:")
    print("   1. A browser window will open with Fortnox authorization page")
    print("   2. Log in as a SYSTEM ADMINISTRATOR")
    print("   3. Review and approve the permissions")
    print("   4. The browser will redirect back and tokens will be saved automatically")
    print()
    print("⚠️  Important: Only system administrators can authorize service accounts!")
    print()
    input("Press ENTER to open the authorization page in your browser...")
    
    # Start local web server
    print(f"\n🌐 Starting local callback server on port {PORT}...")
    server = HTTPServer(('localhost', PORT), OAuthCallbackHandler)
    
    # Display full URL for verification
    print(f"\n🔗 Full authorization URL:")
    print(f"   {auth_url}")
    print()
    print("   ⚠️  IMPORTANT: Check that the client_id in the URL above")
    print("   matches EXACTLY what's in your Fortnox Developer Portal!")
    print()
    
    # Open browser
    print(f"🌐 Opening browser...")
    webbrowser.open(auth_url)
    
    print("\n⏳ Waiting for authorization...")
    print("   (The browser should redirect back automatically)")
    print()
    
    # Wait for callback
    global auth_code, auth_state, server_should_stop
    while not server_should_stop:
        server.handle_request()
    
    server.server_close()
    
    # Check if we got the code
    if not auth_code:
        print("\n❌ Authorization failed or was cancelled")
        sys.exit(1)
    
    # Verify state (security check)
    if auth_state != state:
        print("\n❌ Security error: State mismatch")
        print("   This could indicate a CSRF attack. Aborting.")
        sys.exit(1)
    
    print("✅ Authorization code received")
    
    # Exchange code for tokens
    tokens = exchange_code_for_tokens(auth_code, client_id, client_secret)
    
    if not tokens:
        print("\n❌ Failed to get tokens")
        sys.exit(1)
    
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    expires_in = tokens.get('expires_in', 'unknown')
    
    if not access_token or not refresh_token:
        print("❌ Incomplete token response")
        print(f"   Response: {tokens}")
        sys.exit(1)
    
    print("✅ Tokens received successfully")
    print(f"   Access token: {access_token[:10]}...")
    print(f"   Refresh token: {refresh_token[:10]}...")
    print(f"   Expires in: {expires_in} seconds")
    
    # Save tokens to .env
    if save_tokens_to_env(access_token, refresh_token):
        print()
        print("=" * 70)
        print("🎉 Success! Your Fortnox service account is now configured")
        print("=" * 70)
        print()
        print("Next steps:")
        print("   1. Test the connection: python test_fortnox.py")
        print("   2. Start the bot: python app.py")
        print()
        print("💡 Tip: Set up automatic token refresh with:")
        print("   crontab -e")
        print("   # Add: */50 * * * * cd $(pwd) && $(pwd)/venv/bin/python refresh_token.py")
        print()
    else:
        print("\n⚠️  Tokens received but failed to save to .env")
        print("   Please manually add these to your .env file:")
        print(f"   FORTNOX_ACCESS_TOKEN={access_token}")
        print(f"   FORTNOX_REFRESH_TOKEN={refresh_token}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
