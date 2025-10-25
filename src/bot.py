"""
Fortnox Slack Bot
A Slack bot that integrates with Fortnox API to provide inventory information
"""
import os
import sys
import logging
import requests
import base64
import threading
import time
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from src.fortnox_client import FortnoxClient, FortnoxRateLimitError
from src.token_manager import TokenManager

# Load environment variables
load_dotenv()

# Configure logging with split streams for Railway
# INFO/DEBUG → stdout (blue), ERROR/WARNING/CRITICAL → stderr (red)

class StdoutFilter(logging.Filter):
    """Only allow INFO and DEBUG to stdout"""
    def filter(self, record):
        return record.levelno < logging.WARNING

class StderrFilter(logging.Filter):
    """Only allow WARNING, ERROR, and CRITICAL to stderr"""
    def filter(self, record):
        return record.levelno >= logging.WARNING

# Create handlers
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.addFilter(StdoutFilter())

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)
stderr_handler.addFilter(StderrFilter())

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[stdout_handler, stderr_handler]
)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Global variable for Fortnox client (will be initialized after token refresh)
fortnox_client = None
current_access_token = None
token_manager = TokenManager()  # Manages persistent token storage


def refresh_fortnox_token():
    """
    Refresh the Fortnox access token using the refresh token.
    Updates the global fortnox_client with the new token.
    Also saves the new refresh token if Fortnox issues one (token rotation).
    
    Fallback behavior: If token from file is expired, tries environment variables.
    
    Returns:
        bool: True if successful, False otherwise
    """
    global fortnox_client, current_access_token
    
    logger.info("Refreshing Fortnox access token...")
    
    # Get refresh token from token manager (persistent storage)
    refresh_token = token_manager.get_refresh_token()
    token_source = "file"
    
    # Get credentials from environment
    client_id = os.environ.get("FORTNOX_CLIENT_ID")
    client_secret = os.environ.get("FORTNOX_CLIENT_SECRET")
    env_refresh_token = os.environ.get("FORTNOX_REFRESH_TOKEN")
    
    # Validate we have at least one refresh token source
    if not refresh_token and not env_refresh_token:
        logger.error("Missing required credentials for token refresh")
        logger.error("  - No FORTNOX_REFRESH_TOKEN in file or environment variables")
        logger.error("    Run: ./venv/bin/python get_fortnox_token.py")
        return False
    
    if not client_id or not client_secret:
        logger.error("Missing required credentials for token refresh")
        if not client_id:
            logger.error("  - FORTNOX_CLIENT_ID not set")
        if not client_secret:
            logger.error("  - FORTNOX_CLIENT_SECRET not set")
        return False
    
    # Use file token if available, otherwise fall back to env
    if not refresh_token:
        logger.warning("⚠️  No token in file, using environment variable")
        refresh_token = env_refresh_token
        token_source = "environment"
    
    # Create Basic Auth credentials
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    try:
        # Make token refresh request
        response = requests.post(
            "https://apps.fortnox.se/oauth-v1/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_credentials}"
            },
            timeout=10
        )
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")  # May be rotated by Fortnox
            
            if not new_access_token:
                logger.error("No access token in response")
                return False
            
            # CRITICAL: Save the new refresh token if Fortnox issued one
            # This is the fix for the "invalid_grant" error - tokens must be persisted
            if new_refresh_token:
                if new_refresh_token != refresh_token:
                    logger.info("🔄 Fortnox issued a new refresh token (rotation)")
                token_manager.save_tokens(new_access_token, new_refresh_token)
            else:
                # No new refresh token, just update access token
                token_manager.save_tokens(new_access_token, refresh_token)
            
            # Update in-memory access token
            current_access_token = new_access_token
            
            # Reinitialize Fortnox client with new token
            fortnox_client = FortnoxClient(
                access_token=current_access_token,
                client_secret=client_secret
            )
            
            # Initialize price lists (find HoReCa and load cache)
            try:
                fortnox_client.initialize_price_lists()
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize price lists: {e}")
                logger.warning("Bot will use SalesPrice as fallback for kegs")
                # Don't fail startup - we can still function without price list
            
            logger.info("✅ Access token refreshed successfully")
            logger.info(f"   New token: {new_access_token[:10]}...")
            logger.info(f"   Expires in: {data.get('expires_in', 3600)} seconds")
            
            return True
        else:
            # Check if this is an expired token error and we have a fallback
            if response.status_code == 400 and env_refresh_token and token_source == "file":
                response_data = response.json() if response.text else {}
                if response_data.get("error") == "invalid_grant":
                    logger.warning("⚠️  Token from file is expired, trying environment variable fallback...")
                    # Retry with environment variable token
                    try:
                        fallback_response = requests.post(
                            "https://apps.fortnox.se/oauth-v1/token",
                            data={
                                "grant_type": "refresh_token",
                                "refresh_token": env_refresh_token
                            },
                            headers={
                                "Content-Type": "application/x-www-form-urlencoded",
                                "Authorization": f"Basic {encoded_credentials}"
                            },
                            timeout=10
                        )
                        
                        if fallback_response.status_code == 200:
                            logger.info("✅ Successfully refreshed using environment variable fallback")
                            data = fallback_response.json()
                            new_access_token = data.get("access_token")
                            new_refresh_token = data.get("refresh_token")
                            
                            if not new_access_token:
                                logger.error("No access token in fallback response")
                                return False
                            
                            # Save tokens to file for future use
                            if new_refresh_token:
                                token_manager.save_tokens(new_access_token, new_refresh_token)
                                logger.info("💾 Saved refreshed tokens to file")
                            else:
                                token_manager.save_tokens(new_access_token, env_refresh_token)
                            
                            # Update in-memory token
                            current_access_token = new_access_token
                            
                            # Reinitialize Fortnox client
                            fortnox_client = FortnoxClient(
                                access_token=current_access_token,
                                client_secret=client_secret
                            )
                            
                            # Initialize price lists
                            try:
                                fortnox_client.initialize_price_lists()
                            except Exception as e:
                                logger.warning(f"⚠️  Could not initialize price lists: {e}")
                                logger.warning("Bot will use SalesPrice as fallback for kegs")
                            
                            logger.info("✅ Access token refreshed successfully (via fallback)")
                            logger.info(f"   New token: {new_access_token[:10]}...")
                            logger.info(f"   Expires in: {data.get('expires_in', 3600)} seconds")
                            
                            return True
                        else:
                            logger.error(f"❌ Fallback also failed: HTTP {fallback_response.status_code}")
                            logger.error(f"   Response: {fallback_response.text}")
                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback attempt failed: {fallback_error}")
            
            logger.error(f"❌ Failed to refresh token: HTTP {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error while refreshing token: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during token refresh: {e}", exc_info=True)
        return False


def token_refresh_scheduler():
    """
    Background thread that refreshes the token every 50 minutes.
    Also refreshes the HoReCa price list cache to get latest prices.
    """
    while True:
        time.sleep(50 * 60)  # Sleep for 50 minutes
        logger.info("⏰ Scheduled token refresh triggered (includes price cache refresh)")
        refresh_fortnox_token()


def format_articles_message(articles: list, limit: int = 200) -> str:
    """
    Format articles list into a readable Slack message
    
    Args:
        articles: List of article dictionaries
        limit: Maximum number of articles to display
        
    Returns:
        Formatted message string
    """
    if not articles:
        return "❌ No articles found in stock."
    
    total_articles = len(articles)
    display_articles = articles[:limit]
    
    message_lines = [
        f"📦 *Articles in Stock* ({total_articles} total)\n",
        "```",
        f"{'Article #':<15} {'Description':<40} {'Quantity':<10} {'Unit':<8} {'Price':<10}",
        "-" * 90
    ]
    
    for article in display_articles:
        article_num = str(article.get('ArticleNumber', 'N/A'))[:14]
        description = str(article.get('Description', 'No description'))[:39]
        quantity = str(article.get('QuantityInStock', 0))
        unit = str(article.get('Unit', 'pcs'))[:7]
        # Convert SalesPrice to float (Fortnox returns it as string)
        try:
            price_value = float(article.get('SalesPrice', 0))
            price = f"{price_value:.2f}"
        except (ValueError, TypeError):
            price = "0.00"
        
        message_lines.append(
            f"{article_num:<15} {description:<40} {quantity:<10} {unit:<8} {price:<10}"
        )
    
    message_lines.append("```")
    
    if total_articles > limit:
        message_lines.append(f"\n_Showing {limit} of {total_articles} articles_")
    
    return "\n".join(message_lines)


def format_kegs_message(kegs: list, show_all: bool = False) -> str:
    """
    Format beer kegs list into a readable Slack message
    
    Args:
        kegs: List of keg dictionaries with name, abv, volume, quantity, reserved, and available
        show_all: If True, show 4 columns. If False, show 2 columns (default, mobile-friendly)
        
    Returns:
        Formatted message string
    """
    if not kegs:
        return "❌ No beer kegs found in stock."
    
    # Sort alphabetically by name
    sorted_kegs = sorted(kegs, key=lambda k: k['name'])
    
    total_kegs = len(sorted_kegs)
    total_quantity = sum(keg['quantity'] for keg in sorted_kegs)
    total_reserved = sum(keg['reserved'] for keg in sorted_kegs)
    
    # Get current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Common header for both layouts
    message_lines = [
        f"🍺 *Antal fat i lager* ({total_kegs} sorter, {total_quantity} fat totalt, {total_reserved} reserverade)",
        f"_{current_time}_\n",
        "```"
    ]
    
    if show_all:
        # 5-column layout: Finns, Beskrivning, Pris, Reserverat, Totalt
        message_lines.extend([
            f"{'Finns':<5} {'Beskrivning':<14} {'ABV':<5} {'Pris':<6} {'Reserv.':<7} {'Totalt':<6}",
            "-" * 48
        ])
        
        for keg in sorted_kegs:
            available = f"{keg['available']}x{keg['volume']}"[:5]
            name = f"{keg['name']}"[:14]
            abv = f"{keg['abv']}"[:5]
            price = f"{int(keg['price'])}"[:6]
            reserved = f"{keg['reserved']}x{keg['volume']}"[:7]
            total = f"{keg['quantity']}x{keg['volume']}"[:6]
            
            message_lines.append(
                f"{available:<5} {name:<14} {abv:<5} {price:<6} {reserved:<7} {total:<6}"
            )
    else:
        # 3-column layout: Finns, Namn, Pris (mobile-friendly, max 27 chars)
        message_lines.extend([
            f"{'Finns':<5} {'Namn':<10} {'ABV':<5} {'Pris':<4}",
            "-" * 27
        ])
        
        for keg in sorted_kegs:
            available = f"{keg['available']}x{keg['volume']}"[:5]
            name = f"{keg['name']}"[:10]
            abv = f"{keg['abv']}"[:5]
            price = f"{int(keg['price'])}"[:4]
            
            message_lines.append(
                f"{available:<5} {name:<10} {abv:<5} {price:<4}"
            )
    
    message_lines.append("```")
    
    return "\n".join(message_lines)


def format_cans_message(cans: list, show_all: bool = False) -> str:
    """
    Format beer cans list into a readable Slack message
    
    Args:
        cans: List of can dictionaries with name, abv, volume, boxes, and quantity
        show_all: If True, show 4 columns. If False, show 2 columns (default, mobile-friendly)
        
    Returns:
        Formatted message string
    """
    if not cans:
        return "❌ No beer cans found in stock."
    
    # Sort alphabetically by name
    sorted_cans = sorted(cans, key=lambda c: c['name'])
    
    total_cans = len(sorted_cans)
    total_boxes = sum(can['boxes'] for can in sorted_cans)
    total_reserved_boxes = sum(can['reserved_boxes'] for can in sorted_cans)
    
    # Get current timestamp
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Common header for both layouts
    message_lines = [
        f"🥫 *Antal burkar i lager* ({total_cans} sorter, {total_boxes} kartonger totalt, {total_reserved_boxes} reserverade)",
        f"_{current_time}_\n",
        "```"
    ]
    
    if show_all:
        # 5-column layout: Finns, Beskrivning, ABV, Pris, Reserv., Totalt
        message_lines.extend([
            f"{'Finns':<6} {'Beskrivning':<14} {'ABV':<5} {'Pris':<6} {'Reserv.':<7} {'Totalt':<6}",
            "-" * 49
        ])
        
        for can in sorted_cans:
            available = f"{can['available_boxes']}"[:6]
            name = f"{can['name']}"[:14]
            abv = f"{can['abv']}"[:5]
            price = f"{int(can['price'])}"[:6]
            reserved = f"{can['reserved_boxes']}"[:7]
            total = f"{can['boxes']}"[:6]
            
            message_lines.append(
                f"{available:<6} {name:<14} {abv:<5} {price:<6} {reserved:<7} {total:<6}"
            )
    else:
        # 3-column layout: Finns, Namn, ABV, Pris (mobile-friendly)
        message_lines.extend([
            f"{'Finns':<6} {'Namn':<10} {'ABV':<5} {'Pris':<4}",
            "-" * 28
        ])
        
        for can in sorted_cans:
            available = f"{can['available_boxes']}"[:6]
            name = f"{can['name']}"[:10]
            abv = f"{can['abv']}"[:5]
            price = f"{int(can['price'])}"[:4]
            
            message_lines.append(
                f"{available:<6} {name:<10} {abv:<5} {price:<4}"
            )
    
    message_lines.append("```")
    message_lines.append("\n_Antal i kartonger (1 kartong = 24 burkar)_")
    
    return "\n".join(message_lines)


@app.command("/fat")
def handle_fat_command(ack, command, respond):
    """
    Handle the /fat slash command
    Lists all beer kegs in stock from Fortnox (2 columns, mobile-friendly)
    
    Usage:
        /fat - Show beer kegs (Finns, Beskrivning)
    """
    # Acknowledge the command request
    ack()
    
    try:
        logger.info(f"Fat command received from user {command['user_name']}")
        
        # Fetch kegs from Fortnox
        respond("🔄 Fetching beer kegs from Fortnox...")
        kegs = fortnox_client.get_beer_kegs_in_stock()
        
        # Format and send response (2 columns)
        message = format_kegs_message(kegs, show_all=False)
        respond(message)
        
    except FortnoxRateLimitError as e:
        logger.warning(f"Rate limit hit on fat command: {e}")
        respond("⚠️ **Fortnox API rate limit exceeded**\n\nWe've hit the maximum number of API requests. Please wait a few minutes and try again.")
    except Exception as e:
        logger.error(f"Error handling fat command: {e}", exc_info=True)
        respond(f"❌ Error fetching beer kegs: {str(e)}\nPlease check your Fortnox API credentials.")


@app.command("/fat-detaljerat")
def handle_fat_detaljerat_command(ack, command, respond):
    """
    Handle the /fat-detaljerat slash command
    Lists all beer kegs in stock from Fortnox with full details (4 columns)
    
    Usage:
        /fat-detaljerat - Show beer kegs with all columns
    """
    # Acknowledge the command request
    ack()
    
    try:
        logger.info(f"Fat-detaljerat command received from user {command['user_name']}")
        
        # Fetch kegs from Fortnox
        respond("🔄 Fetching beer kegs from Fortnox...")
        kegs = fortnox_client.get_beer_kegs_in_stock()
        
        # Format and send response (4 columns)
        message = format_kegs_message(kegs, show_all=True)
        respond(message)
        
    except FortnoxRateLimitError as e:
        logger.warning(f"Rate limit hit on fat-detaljerat command: {e}")
        respond("⚠️ **Fortnox API rate limit exceeded**\n\nWe've hit the maximum number of API requests. Please wait a few minutes and try again.")
    except Exception as e:
        logger.error(f"Error handling fat-detaljerat command: {e}", exc_info=True)
        respond(f"❌ Error fetching beer kegs: {str(e)}\nPlease check your Fortnox API credentials.")


@app.command("/burk")
def handle_burk_command(ack, command, respond):
    """
    Handle the /burk slash command
    Lists all beer cans in stock from Fortnox (2 columns, mobile-friendly)
    
    Usage:
        /burk - Show beer cans (Finns, Beskrivning)
    """
    # Acknowledge the command request
    ack()
    
    try:
        logger.info(f"Burk command received from user {command['user_name']}")
        
        # Fetch cans from Fortnox
        respond("🔄 Fetching beer cans from Fortnox...")
        cans = fortnox_client.get_beer_cans_in_stock()
        
        # Format and send response (2 columns)
        message = format_cans_message(cans, show_all=False)
        respond(message)
        
    except FortnoxRateLimitError as e:
        logger.warning(f"Rate limit hit on burk command: {e}")
        respond("⚠️ **Fortnox API rate limit exceeded**\n\nWe've hit the maximum number of API requests. Please wait a few minutes and try again.")
    except Exception as e:
        logger.error(f"Error handling burk command: {e}", exc_info=True)
        respond(f"❌ Error fetching beer cans: {str(e)}\nPlease check your Fortnox API credentials.")


@app.command("/burk-detaljerat")
def handle_burk_detaljerat_command(ack, command, respond):
    """
    Handle the /burk-detaljerat slash command
    Lists all beer cans in stock from Fortnox with full details (4 columns)
    
    Usage:
        /burk-detaljerat - Show beer cans with all columns
    """
    # Acknowledge the command request
    ack()
    
    try:
        logger.info(f"Burk-detaljerat command received from user {command['user_name']}")
        
        # Fetch cans from Fortnox
        respond("🔄 Fetching beer cans from Fortnox...")
        cans = fortnox_client.get_beer_cans_in_stock()
        
        # Format and send response (4 columns)
        message = format_cans_message(cans, show_all=True)
        respond(message)
        
    except FortnoxRateLimitError as e:
        logger.warning(f"Rate limit hit on burk-detaljerat command: {e}")
        respond("⚠️ **Fortnox API rate limit exceeded**\n\nWe've hit the maximum number of API requests. Please wait a few minutes and try again.")
    except Exception as e:
        logger.error(f"Error handling burk-detaljerat command: {e}", exc_info=True)
        respond(f"❌ Error fetching beer cans: {str(e)}\nPlease check your Fortnox API credentials.")


@app.command("/bot")
def handle_bot_command(ack, command, respond):
    """
    Handle the /bot slash command
    Display help information with available commands
    """
    # Acknowledge the command request
    ack()
    
    logger.info(f"Bot help command received from user {command['user_name']}")
    
    help_message = """
🤖 *Fortnox Inventory Bot - Available Commands*

*Beer Kegs (Fat):*
• `/fat` - List beer kegs in stock (simple view)
• `/fat-detaljerat` - List beer kegs with full details (available, reserved, total)

*Beer Cans (Burkar):*
• `/burk` - List beer cans in stock (simple view)
• `/burk-detaljerat` - List beer cans with full details (available, reserved, total)

*Help:*
• `/bot` - Show this help message

_Note: Quantities for cans are shown in boxes (1 box = 24 cans)_
"""
    
    respond(help_message)


@app.event("app_mention")
def handle_app_mention(event, say):
    """
    Handle when the bot is mentioned in a channel
    """
    user = event['user']
    text = event.get('text', '')
    
    logger.info(f"Bot mentioned by user {user}: {text}")
    
    help_message = f"""
👋 Hi <@{user}>! I'm the Fortnox Inventory Bot.

*Available Commands:*

*Beer Kegs (Fat):*
• `/fat` - List beer kegs in stock (simple view)
• `/fat-detaljerat` - List beer kegs with full details

*Beer Cans (Burkar):*
• `/burk` - List beer cans in stock (simple view)
• `/burk-detaljerat` - List beer cans with full details

*Help:*
• `/bot` - Show this help message

_Note: Quantities for cans are shown in boxes (1 box = 24 cans)_
"""
    
    say(help_message)


@app.event("message")
def handle_message_events(body, logger):
    """
    Handle generic message events (logged but not responded to)
    """
    logger.debug(f"Message event received: {body}")


# Start the app
if __name__ == "__main__":
    try:
        logger.info("Starting Fortnox Slack Bot...")
        
        # Verify environment variables
        required_vars = [
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET",
            "SLACK_APP_TOKEN",
            "FORTNOX_REFRESH_TOKEN",
            "FORTNOX_CLIENT_ID",
            "FORTNOX_CLIENT_SECRET"
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please check your .env file")
            exit(1)
        
        # Initialize token file from environment variables if it doesn't exist
        # This migrates from env-based tokens to file-based tokens
        logger.info("Checking token storage...")
        if not token_manager.initialize_from_env():
            logger.warning("⚠️  Could not initialize token file from environment")
            logger.warning("    Attempting to use existing token file...")
        
        # Refresh Fortnox token at startup
        logger.info("Initializing Fortnox connection...")
        if not refresh_fortnox_token():
            logger.error("=" * 70)
            logger.error("❌ CRITICAL: Failed to refresh Fortnox token at startup")
            logger.error("=" * 70)
            logger.error("This usually means:")
            logger.error("  1. FORTNOX_REFRESH_TOKEN is invalid or expired")
            logger.error("  2. Environment variables have quotes around them (remove quotes!)")
            logger.error("  3. Token was revoked in Fortnox Developer Portal")
            logger.error("")
            logger.error("To fix:")
            logger.error("  1. Run: ./venv/bin/python get_fortnox_token.py")
            logger.error("  2. Get fresh tokens")
            logger.error("  3. Update Railway environment variables (without quotes)")
            logger.error("=" * 70)
            logger.error("Bot will sleep for 1 hour to avoid hammering Fortnox API...")
            logger.error("(This prevents Railway from restarting the bot repeatedly)")
            logger.error("=" * 70)
            # Sleep for 1 hour instead of exiting to prevent rapid restart loop
            time.sleep(3600)
            exit(1)
        
        # Start background token refresh scheduler
        logger.info("Starting token refresh scheduler (every 50 minutes)...")
        refresh_thread = threading.Thread(target=token_refresh_scheduler, daemon=True)
        refresh_thread.start()
        
        # Start the bot using Socket Mode
        handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
        logger.info("✅ Fortnox Slack Bot is running!")
        handler.start()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        exit(1)
