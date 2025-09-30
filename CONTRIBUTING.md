# Contributing to Fortnox Slack Bot

Thank you for considering contributing to the Fortnox Slack Bot! This document provides guidelines and instructions for contributing.

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check the [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md) for common issues
2. Search existing issues to avoid duplicates
3. Make sure you're using the latest version

When creating a bug report, include:
- **Description**: Clear description of the bug
- **Steps to reproduce**: Detailed steps to reproduce the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, dependency versions
- **Logs**: Relevant error messages and stack traces
- **Screenshots**: If applicable

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:
- **Use case**: Why is this enhancement needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other solutions you've considered
- **Examples**: Similar features in other tools

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/fortnox_slack_bot.git
   cd fortnox_slack_bot
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Write clean, readable code
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   ```bash
   # Run the configuration validator
   python validate_config.py
   
   # Test Fortnox connection
   python test_fortnox.py
   
   # Run the bot locally
   python app.py
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```
   
   Use clear, descriptive commit messages:
   - ✨ `feat: Add stock alert notifications`
   - 🐛 `fix: Handle missing article descriptions`
   - 📝 `docs: Update installation instructions`
   - 🎨 `style: Format code with black`
   - ♻️ `refactor: Simplify API client logic`
   - ✅ `test: Add unit tests for FortnoxClient`
   - 🔧 `chore: Update dependencies`

6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots/examples if applicable
   - Ensure all checks pass

## Code Style Guidelines

### Python Code Style

Follow PEP 8 style guide:

```python
# Good: Clear function names, type hints, docstrings
def get_articles_in_stock(self, minimum_stock: int = 0) -> List[Dict]:
    """
    Retrieve articles that are in stock
    
    Args:
        minimum_stock: Minimum stock quantity to filter by
        
    Returns:
        List of articles with stock information
    """
    pass

# Bad: Unclear names, no documentation
def get(self, m=0):
    pass
```

### Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters
- Use blank lines to separate logical sections
- Add trailing commas in multi-line collections

### Imports

```python
# Standard library imports first
import os
import logging
from typing import Dict, List, Optional

# Third-party imports
import requests
from slack_bolt import App

# Local imports
from fortnox_client import FortnoxClient
```

### Error Handling

```python
# Good: Specific exception handling with logging
try:
    article = self.get_article_by_number(number)
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP error fetching article: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise

# Bad: Bare except that swallows errors
try:
    article = self.get_article_by_number(number)
except:
    pass
```

### Logging

Use appropriate log levels:
```python
logger.debug("Detailed debugging information")
logger.info("General informational messages")
logger.warning("Warning messages for potential issues")
logger.error("Error messages for failures")
```

## Development Setup

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd fortnox_slack_bot
   ./setup.sh
   ```

2. **Activate virtual environment**
   ```bash
   source venv/bin/activate
   ```

3. **Install development dependencies** (if any)
   ```bash
   pip install -r requirements-dev.txt  # if exists
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Validate configuration**
   ```bash
   python validate_config.py
   ```

## Testing

### Manual Testing

1. **Test Fortnox connection**
   ```bash
   python test_fortnox.py
   ```

2. **Run the bot**
   ```bash
   python app.py
   ```

3. **Test in Slack**
   - `/fortnox-stock`
   - `/fortnox-stock 10`
   - `/fortnox-article <number>`
   - `@Bot help`

### Adding Tests

If you add new features, consider adding tests:

```python
# test_fortnox_client.py (example)
import unittest
from fortnox_client import FortnoxClient

class TestFortnoxClient(unittest.TestCase):
    def setUp(self):
        self.client = FortnoxClient("token", "secret")
    
    def test_get_articles(self):
        articles = self.client.get_articles()
        self.assertIsInstance(articles, list)
```

## Documentation

Update documentation when:
- Adding new features
- Changing existing behavior
- Fixing bugs that affect usage
- Adding new configuration options

Documentation files to update:
- `README.md` - Main documentation
- `QUICKSTART.md` - Quick setup guide
- `DEPLOYMENT.md` - Deployment instructions
- `CHANGELOG.md` - Version history
- Code comments and docstrings

## Project Structure

```
fortnox_slack_bot/
├── app.py                    # Main application
├── fortnox_client.py         # Fortnox API client
├── validate_config.py        # Configuration validator
├── test_fortnox.py          # Connection test
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
├── README.md                # Main documentation
├── QUICKSTART.md            # Quick start guide
├── DEPLOYMENT.md            # Deployment guide
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # This file
├── setup.sh                 # Setup script
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose config
└── fortnox-bot.service      # Systemd service file
```

## Code Review Process

All contributions go through code review:

1. **Automated checks** - Ensure code quality
2. **Functionality review** - Verify the feature works
3. **Code quality** - Check readability and maintainability
4. **Documentation** - Ensure proper documentation
5. **Testing** - Verify adequate testing

## Feature Requests

Have an idea? Great! Here's how to propose it:

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with the "enhancement" label
3. **Describe the feature** in detail
4. **Explain the use case** and benefits
5. **Discuss implementation** if you have ideas

Popular requested features:
- Stock alerts and notifications
- Multiple warehouse support
- Advanced search and filtering
- Automated reports
- Integration with other systems

## Community

- Be respectful and constructive
- Help others when you can
- Share your use cases and experiences
- Provide feedback on proposed changes

## Questions?

- Check the [README.md](README.md)
- Search existing issues
- Create a new issue with the "question" label

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing! 🎉
