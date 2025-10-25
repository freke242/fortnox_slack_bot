"""
Fortnox Slack Bot
A Slack bot that integrates with Fortnox API to provide inventory information
"""
import os
import logging
import requests
import base64
import threading
import time
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from fortnox_client import FortnoxClient, FortnoxRateLimitError
from token_manager import TokenManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    
    Returns:
        bool: True if successful, False otherwise
    """
    global fortnox_client, current_access_token
    
    logger.info("Refreshing Fortnox access token...")
    
    # Get refresh token from token manager (persistent storage)
    refresh_token = token_manager.get_refresh_token()
    
    # Get credentials from environment
    client_id = os.environ.get("FORTNOX_CLIENT_ID")
    client_secret = os.environ.get("FORTNOX_CLIENT_SECRET")
    
    # Validate required variables
    if not all([refresh_token, client_id, client_secret]):
        logger.error("Missing required credentials for token refresh")
        if not refresh_token:
            logger.error("  - FORTNOX_REFRESH_TOKEN not found in token file")
            logger.error("    Run: ./venv/bin/python get_fortnox_token.py")
        if not client_id:
            logger.error("  - FORTNOX_CLIENT_ID not set")
        if not client_secret:
            logger.error("  - FORTNOX_CLIENT_SECRET not set")
        return False
    
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
        # 3-column layout: Finns, Beskrivning, Pris (mobile-friendly, max 27 chars)
        message_lines.extend([
            f"{'Finns':<5} {'Beskrivning':<10} {'ABV':<5} {'Pris':<4}",
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


@app.command("/fortnox-stock")
def handle_stock_command(ack, command, respond):
    """
    Handle the /fortnox-stock slash command
    Lists all articles in stock from Fortnox
    
    Usage:
        /fortnox-stock - Show all articles (default limit: 200)
        /fortnox-stock <minimum> - Show articles with minimum stock quantity
        /fortnox-stock <minimum> <limit> - Set both minimum stock and display limit
    """
    # Acknowledge the command request
    ack()
    
    try:
        logger.info(f"Stock command received from user {command['user_name']}")
        
        # Parse optional parameters: minimum stock and display limit
        text = command.get('text', '').strip()
        minimum_stock = 0
        display_limit = 200  # Default limit
        
        if text:
            parts = text.split()
            try:
                if len(parts) >= 1:
                    minimum_stock = int(parts[0])
                    logger.info(f"Filtering by minimum stock: {minimum_stock}")
                if len(parts) >= 2:
                    display_limit = int(parts[1])
                    logger.info(f"Display limit set to: {display_limit}")
            except ValueError:
                respond("⚠️ Invalid parameter. Usage: `/fortnox-stock [minimum_quantity] [display_limit]`")
                return
        
        # Fetch articles from Fortnox
        respond("🔄 Fetching articles from Fortnox...")
        articles = fortnox_client.get_articles_in_stock(minimum_stock=minimum_stock)
        
        # Format and send response
        message = format_articles_message(articles, limit=display_limit)
        respond(message)
        
    except FortnoxRateLimitError as e:
        logger.warning(f"Rate limit hit on stock command: {e}")
        respond("⚠️ **Fortnox API rate limit exceeded**\n\nWe've hit the maximum number of API requests. Please wait a few minutes and try again.")
    except Exception as e:
        logger.error(f"Error handling stock command: {e}", exc_info=True)
        respond(f"❌ Error fetching articles: {str(e)}\nPlease check your Fortnox API credentials.")


@app.command("/fortnox-article")
def handle_article_command(ack, command, respond):
    """
    Handle the /fortnox-article slash command
    Get details about a specific article by article number
    """
    # Acknowledge the command request
    ack()
    
    try:
        article_number = command.get('text', '').strip()
        
        if not article_number:
            respond("⚠️ Please provide an article number. Usage: `/fortnox-article <article_number>`")
            return
        
        logger.info(f"Article lookup requested for: {article_number}")
        
        # Fetch article from Fortnox
        respond(f"🔄 Looking up article {article_number}...")
        article = fortnox_client.get_article_by_number(article_number)
        
        if not article:
            respond(f"❌ Article {article_number} not found.")
            return
        
        # Format article details
        message = f"""
📦 *Article Details*

*Article Number:* {article.get('ArticleNumber', 'N/A')}
*Description:* {article.get('Description', 'No description')}
*Quantity in Stock:* {article.get('QuantityInStock', 0)} {article.get('Unit', 'pcs')}
*Stock Place:* {article.get('StockPlace', 'N/A')}
*Sales Price:* {float(article.get('SalesPrice', 0) or 0):.2f} {article.get('Currency', 'SEK')}
*Purchase Price:* {float(article.get('PurchasePrice', 0) or 0):.2f} {article.get('Currency', 'SEK')}
*Supplier:* {article.get('SupplierName', 'N/A')}
*EAN:* {article.get('EAN', 'N/A')}
*Manufacturer:* {article.get('Manufacturer', 'N/A')}
"""
        
        respond(message)
        
    except FortnoxRateLimitError as e:
        logger.warning(f"Rate limit hit on article command: {e}")
        respond("⚠️ **Fortnox API rate limit exceeded**\n\nWe've hit the maximum number of API requests. Please wait a few minutes and try again.")
    except Exception as e:
        logger.error(f"Error handling article command: {e}", exc_info=True)
        respond(f"❌ Error fetching article: {str(e)}\nPlease check the article number and try again.")


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

• `/fortnox-stock` - List all articles in stock (up to 200 items)
• `/fortnox-stock <minimum>` - List articles with at least the specified quantity
• `/fortnox-stock <minimum> <limit>` - Control minimum stock and display limit
• `/fortnox-article <number>` - Get details about a specific article
• `/fat` - List beer kegs in stock (mobile view)
• `/fat-detaljerat` - List beer kegs with full details

*Examples:*
`/fortnox-stock` - Show all articles in stock
`/fortnox-stock 10` - Show articles with at least 10 units in stock
`/fortnox-stock 0 500` - Show all articles, display up to 500 items
`/fortnox-article 12345` - Show details for article 12345
`/fat` - Show beer kegs (available quantity + description)
`/fat-detaljerat` - Show beer kegs with all columns (available, reserved, total)
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
