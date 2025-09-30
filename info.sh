#!/bin/bash

# Project Information Display Script

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           🤖 Fortnox Slack Bot - Project Information          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Version: 1.0.0"
echo "🏷️  Status: Production Ready"
echo "📅 Created: 2025-09-30"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Quick Commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Setup & Validation:"
echo "    ./setup.sh                    # Run automated setup"
echo "    python check_setup.py         # Validate complete setup"
echo "    python validate_config.py     # Check environment variables"
echo "    python test_fortnox.py        # Test Fortnox API connection"
echo ""
echo "  Running the Bot:"
echo "    python app.py                 # Start the bot"
echo "    docker-compose up -d          # Run with Docker"
echo "    sudo systemctl start fortnox-bot  # Start as service"
echo ""
echo "  Monitoring:"
echo "    sudo systemctl status fortnox-bot     # Check service status"
echo "    sudo journalctl -u fortnox-bot -f     # View logs"
echo "    docker-compose logs -f                # Docker logs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📖 README.md              Complete setup and usage guide"
echo "  ⚡ QUICKSTART.md          Get started in 10 minutes"
echo "  🏢 FORTNOX_SETUP.md       Detailed Fortnox service account setup"
echo "  🚀 DEPLOYMENT.md          Production deployment guide"
echo "  🤝 CONTRIBUTING.md        How to contribute"
echo "  📝 CHANGELOG.md           Version history"
echo "  📚 DOCUMENTATION.md       Documentation overview"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Available Slack Commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  /fortnox-stock              List all articles in stock"
echo "  /fortnox-stock [min]        Filter by minimum quantity"
echo "  /fortnox-article [number]   Get article details"
echo "  @bot help                   Show help message"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Project Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Count Python files
py_files=$(find . -name "*.py" -not -path "./venv/*" | wc -l)
# Count markdown files
md_files=$(find . -name "*.md" | wc -l)
# Count total lines of Python code
if [ -d "venv" ]; then
    py_lines=$(find . -name "*.py" -not -path "./venv/*" -exec wc -l {} + 2>/dev/null | tail -n 1 | awk '{print $1}')
else
    py_lines=$(find . -name "*.py" -exec wc -l {} + 2>/dev/null | tail -n 1 | awk '{print $1}')
fi

echo "  Python files:     $py_files"
echo "  Documentation:    $md_files files"
echo "  Lines of code:    ${py_lines:-N/A}"
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo "  ✅ Configuration:  .env file found"
else
    echo "  ⚠️  Configuration:  .env file not found (run: cp .env.example .env)"
fi

# Check if venv exists
if [ -d "venv" ]; then
    echo "  ✅ Environment:    Virtual environment ready"
else
    echo "  ⚠️  Environment:    Virtual environment not found (run: ./setup.sh)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 Useful Links"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Slack API:        https://api.slack.com/apps"
echo "  Fortnox API:      https://developer.fortnox.se/"
echo "  Slack Docs:       https://docs.slack.dev/"
echo "  Fortnox Docs:     https://api.fortnox.se/apidocs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Getting Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  First time setup:"
echo "    1. ./setup.sh"
echo "    2. cp .env.example .env"
echo "    3. Edit .env with your credentials"
echo "    4. python validate_config.py"
echo "    5. python app.py"
echo ""
echo "  Need help? Read QUICKSTART.md or README.md"
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Ready to start? Run: python app.py                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
