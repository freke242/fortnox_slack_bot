# Fortnox Slack Bot

A Slack bot for a **craft brewery** that integrates with the Fortnox API to provide real-time inventory and warehouse information directly in Slack.

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 10 minutes ⚡
- **[FORTNOX_SETUP.md](docs/FORTNOX_SETUP.md)** - Detailed Fortnox service account setup
- **[RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md)** - Deploy to Railway (recommended)
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - General deployment guide
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - How to contribute
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history
- **[AGENTS.md](docs/AGENTS.md)** - AI agent context & development notes

## Features

- 🍺 List beer kegs in stock with HoReCa pricing
- 🥫 List beer cans in stock (shown in boxes of 24)
- 📊 Simple and detailed views for both kegs and cans
- 💬 Interactive Slack interface with formatted responses
- 🔄 Automatic OAuth token refresh every 50 minutes
- 💾 Persistent token storage across restarts

## Prerequisites

- Python 3.8 or higher
- A Slack workspace where you can install apps
- A Fortnox account with API access

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fortnox_slack_bot
```

### 2. Install Dependencies

```bash
# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps) and click **Create New App**
2. Choose **From scratch**
3. Enter an app name (e.g., "Fortnox Inventory Bot") and select your workspace
4. Click **Create App**

#### Configure OAuth & Permissions

1. Navigate to **OAuth & Permissions** in the left sidebar
2. Under **Bot Token Scopes**, add the following scopes:
   - `chat:write` - Send messages as the bot
   - `commands` - Add slash commands
   - `app_mentions:read` - Respond to @mentions

3. Scroll up and click **Install to Workspace**
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

#### Enable Socket Mode

1. Navigate to **Socket Mode** in the left sidebar
2. Enable Socket Mode
3. Under **App-Level Tokens**, click **Generate Token and Scopes**
4. Name it (e.g., "socket-token") and add the `connections:write` scope
5. Click **Generate**
6. Copy the **App-Level Token** (starts with `xapp-`)

#### Add Slash Commands

1. Navigate to **Slash Commands** in the left sidebar
2. Click **Create New Command**
3. Add the following commands:

   **Command 1: /fat**
   - Command: `/fat`
   - Request URL: `https://your-app-url.com/slack/events` (can be anything for Socket Mode)
   - Short Description: "List beer kegs in stock"
   - Usage Hint: (leave empty)

   **Command 2: /fat-detaljerat**
   - Command: `/fat-detaljerat`
   - Request URL: `https://your-app-url.com/slack/events`
   - Short Description: "List beer kegs with full details"
   - Usage Hint: (leave empty)

   **Command 3: /burk**
   - Command: `/burk`
   - Request URL: `https://your-app-url.com/slack/events`
   - Short Description: "List beer cans in stock"
   - Usage Hint: (leave empty)

   **Command 4: /burk-detaljerat**
   - Command: `/burk-detaljerat`
   - Request URL: `https://your-app-url.com/slack/events`
   - Short Description: "List beer cans with full details"
   - Usage Hint: (leave empty)

   **Command 5: /bot**
   - Command: `/bot`
   - Request URL: `https://your-app-url.com/slack/events`
   - Short Description: "Show help and available commands"
   - Usage Hint: (leave empty)

4. Click **Save**

#### Get Signing Secret

1. Navigate to **Basic Information** in the left sidebar
2. Under **App Credentials**, copy the **Signing Secret**

### 4. Configure Fortnox API

**For Company/Production Use (Recommended):**

Use a **Fortnox Service Account** - this is the best practice for server-to-server integrations:

📖 **See [FORTNOX_SETUP.md](FORTNOX_SETUP.md) for complete instructions**

Service accounts:
- ✅ Not tied to individual users
- ✅ System administrator controlled
- ✅ Secure and production-ready
- ✅ Recommended by Fortnox

**For Development/Testing:**

1. Log in to your Fortnox account
2. Navigate to the [Fortnox Developer Portal](https://developer.fortnox.se/)
3. Create a new integration
4. Complete the OAuth flow to get an access token

### 5. Set Up Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and fill in your credentials:
   ```bash
   # Slack Bot Configuration
   SLACK_BOT_TOKEN=xoxb-your-bot-token-here
   SLACK_SIGNING_SECRET=your-signing-secret-here
   SLACK_APP_TOKEN=xapp-your-app-token-here

   # Fortnox API Configuration
   FORTNOX_ACCESS_TOKEN=your-fortnox-access-token-here
   FORTNOX_CLIENT_SECRET=your-fortnox-client-secret-here
   ```

## Project Structure

```
fortnox_slack_bot/
├── src/                    # Source code
│   ├── bot.py             # Main bot application
│   ├── fortnox_client.py  # Fortnox API client
│   └── token_manager.py   # Token persistence
├── tests/                  # Test files
├── scripts/                # Utility scripts
│   ├── get_fortnox_token.py
│   └── setup.sh
├── docs/                   # Documentation
├── deployment/             # Docker & deployment config
│   ├── Dockerfile
│   └── entrypoint.sh
└── requirements.txt        # Dependencies
```

## Usage

### Starting the Bot

```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the bot
python -m src.bot
```

You should see:
```
✅ Fortnox Slack Bot is running!
```

### Available Commands

#### Beer Kegs (Fat)

```
/fat
```
Lists all beer kegs in stock (simple view: available quantity, name, ABV, price).

```
/fat-detaljerat
```
Lists beer kegs with full details (available, reserved, total quantities).

#### Beer Cans (Burkar)

```
/burk
```
Lists all beer cans in stock (simple view, quantities shown in boxes where 1 box = 24 cans).

```
/burk-detaljerat
```
Lists beer cans with full details (available, reserved, total boxes).

#### Help

```
/bot
```
Displays help information and available commands.

```
@Fortnox Inventory Bot
```
Mentioning the bot also displays help information.

## Project Structure

```
fortnox_slack_bot/
├── app.py                 # Main Slack bot application
├── fortnox_client.py      # Fortnox API client
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .env                  # Your environment variables (not in git)
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## API Reference

### FortnoxClient

The `FortnoxClient` class provides methods to interact with the Fortnox API:

#### Methods

- `get_articles(filter_params=None)` - Retrieve all articles
- `get_article_by_number(article_number)` - Get a specific article
- `get_articles_in_stock(minimum_stock=0)` - Get articles with stock

### Slack Bot Commands

All commands are defined in `app.py` using the `@app.command()` decorator.

## Troubleshooting

### Bot doesn't respond to commands

1. Make sure the bot is running (`python app.py`)
2. Check that Socket Mode is enabled in your Slack app settings
3. Verify all environment variables are set correctly
4. Check the logs for error messages

### Authentication errors with Fortnox

1. Verify your Fortnox Access Token is valid
2. Check that your Client Secret is correct
3. Ensure your Fortnox API integration is active
4. Check the Fortnox API rate limits

### Missing dependencies

```bash
pip install -r requirements.txt
```

## Development

### Running in Development Mode

```bash
# Set log level to DEBUG for more verbose output
export LOG_LEVEL=DEBUG
python app.py
```

### Testing the Fortnox Client

You can test the Fortnox client directly:

```python
from fortnox_client import FortnoxClient
import os
from dotenv import load_dotenv

load_dotenv()

client = FortnoxClient(
    access_token=os.getenv("FORTNOX_ACCESS_TOKEN"),
    client_secret=os.getenv("FORTNOX_CLIENT_SECRET")
)

# Test fetching articles
articles = client.get_articles_in_stock()
print(f"Found {len(articles)} articles in stock")
```

## Security Considerations

- **Never commit `.env` file** - It contains sensitive credentials
- **Use environment variables** for all secrets
- **Rotate tokens regularly** - Especially in production
- **Limit API scopes** - Only request permissions you need
- **Monitor API usage** - Watch for unusual patterns

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is provided as-is for integration purposes.

## Support

For issues related to:
- **Slack API**: [Slack API Documentation](https://api.slack.com/)
- **Fortnox API**: [Fortnox API Documentation](https://developer.fortnox.se/)
- **This Bot**: Open an issue in the repository

## Acknowledgments

- Built with [Slack Bolt for Python](https://slack.dev/bolt-python/)
- Integrates with [Fortnox API v3](https://developer.fortnox.se/)

## Future Enhancements

Potential features to add:
- 📈 Stock level alerts and notifications
- 🔔 Low stock warnings
- 📝 Create and update articles
- 📊 Stock movement history
- 🏷️ Search by multiple criteria
- 📸 Article image display
- 📤 Export data to CSV
- 🤖 Automated inventory reports
