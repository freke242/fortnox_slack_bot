"""
Fortnox Slack Bot
A Slack bot that integrates with Fortnox API to provide inventory information
"""
import os
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from fortnox_client import FortnoxClient

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

# Initialize Fortnox client
fortnox_client = FortnoxClient(
    access_token=os.environ.get("FORTNOX_ACCESS_TOKEN"),
    client_secret=os.environ.get("FORTNOX_CLIENT_SECRET")
)


def format_articles_message(articles: list, limit: int = 50) -> str:
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


@app.command("/fortnox-stock")
def handle_stock_command(ack, command, respond):
    """
    Handle the /fortnox-stock slash command
    Lists all articles in stock from Fortnox
    """
    # Acknowledge the command request
    ack()
    
    try:
        logger.info(f"Stock command received from user {command['user_name']}")
        
        # Parse optional minimum stock parameter
        text = command.get('text', '').strip()
        minimum_stock = 0
        
        if text:
            try:
                minimum_stock = int(text)
                logger.info(f"Filtering by minimum stock: {minimum_stock}")
            except ValueError:
                respond("⚠️ Invalid parameter. Usage: `/fortnox-stock [minimum_quantity]`")
                return
        
        # Fetch articles from Fortnox
        respond("🔄 Fetching articles from Fortnox...")
        articles = fortnox_client.get_articles_in_stock(minimum_stock=minimum_stock)
        
        # Format and send response
        message = format_articles_message(articles)
        respond(message)
        
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
        
    except Exception as e:
        logger.error(f"Error handling article command: {e}", exc_info=True)
        respond(f"❌ Error fetching article: {str(e)}\nPlease check the article number and try again.")


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

• `/fortnox-stock` - List all articles in stock
• `/fortnox-stock <minimum>` - List articles with at least the specified quantity
• `/fortnox-article <number>` - Get details about a specific article

*Example:*
`/fortnox-stock 10` - Show articles with at least 10 units in stock
`/fortnox-article 12345` - Show details for article 12345
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
            "FORTNOX_ACCESS_TOKEN",
            "FORTNOX_CLIENT_SECRET"
        ]
        
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please check your .env file")
            exit(1)
        
        # Start the bot using Socket Mode
        handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
        logger.info("✅ Fortnox Slack Bot is running!")
        handler.start()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        exit(1)
