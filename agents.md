# 🤖 Agent Documentation

This file contains important context and commands for AI coding agents working on this project. It helps maintain consistency across sessions and provides quick reference for common tasks.

---

## 🔧 Development Environment

### Virtual Environment
This project uses a Python virtual environment located at `./venv/`

**Important**: Always use the venv Python interpreter when running scripts:
```bash
./venv/bin/python <script_name>.py
```

**Do NOT use**:
- `python` (not installed on this system)
- `python3` (uses system Python, missing dependencies)

### Required Dependencies
All Python dependencies are installed in the virtual environment. If you need to install new packages:
```bash
./venv/bin/pip install <package_name>
./venv/bin/pip freeze > requirements.txt  # Update requirements
```

---

## 🧪 Testing

### Test Fortnox API Connection
To test the Fortnox API integration:
```bash
./venv/bin/python test_fortnox.py
```

**Expected Output**:
- ✅ Successfully retrieves all articles from Fortnox (with pagination)
- ✅ Filters articles that are in stock
- ✅ Displays sample articles

### Run the Bot
To start the Slack bot:
```bash
./venv/bin/python app.py
```

The bot must be running for Slack commands to work.

---

## 📁 Project Structure

```
fortnox_slack_bot/
├── app.py                      # Main Slack bot application
├── fortnox_client.py           # Fortnox API client (with pagination)
├── test_fortnox.py             # API connection test script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example               # Environment template
└── venv/                       # Virtual environment (not in git)
```

---

## 🔑 Key Implementation Details

### Fortnox API Pagination
The `fortnox_client.py` implements automatic pagination:
- **Limit**: 500 articles per request (maximum allowed by API)
- **Method**: Uses `offset` parameter to fetch all pages
- **Total articles**: 519 (as of last test)
- **Articles in stock**: 139 (as of last test)

### Rate Limits
- **Fortnox API**: 300 requests/minute per access token
- **Current usage**: ~2 requests per full article fetch (well within limits)

### Data Type Handling
- `QuantityInStock` may be returned as string or number - code handles both
- Always convert to float before comparison

---

## 🐛 Common Issues

### "Command 'python' not found"
**Solution**: Use `./venv/bin/python` instead of `python`

### "ModuleNotFoundError: No module named 'X'"
**Solution**: 
1. Ensure venv is activated or use `./venv/bin/python`
2. Check that module is in `requirements.txt`
3. Reinstall if needed: `./venv/bin/pip install -r requirements.txt`

### Bot not responding in Slack
**Solution**:
1. Check bot is running: `./venv/bin/python app.py`
2. Verify Socket Mode is enabled in Slack App settings
3. Check `.env` file has all required tokens

---

## 📝 Code Style Guidelines

### Logging
- Use `logger.info()` for normal operations
- Use `logger.error()` for errors with stack traces
- Include context in log messages (e.g., counts, IDs)

### Error Handling
- Always handle API response data type variations
- Use try/except for type conversions
- Provide fallback values (e.g., `0` for missing quantities)

### API Calls
- Use pagination for list endpoints
- Log progress for long-running operations
- Respect rate limits (already well within bounds)

---

## 🚀 Recent Changes

### 2025-10-21: Pagination Implementation
- Implemented automatic pagination in `get_articles()`
- Now retrieves all 519 articles instead of just first page (~43 articles)
- Fixed data type conversion bug for `QuantityInStock`
- Added detailed logging for pagination progress

---

## 📚 External Documentation

- [Slack Bolt Python](https://slack.dev/bolt-python/)
- [Fortnox API Documentation](https://developer.fortnox.se/)
- [Fortnox API Reference](https://apps.fortnox.se/apidocs/)

---

## 💡 Tips for Agents

1. **Always test changes**: Run `./venv/bin/python test_fortnox.py` after modifying API client
2. **Check logs**: Bot logs contain useful debugging information
3. **Environment variables**: Sensitive data is in `.env` (not committed to git)
4. **Pagination**: Remember that Fortnox API has limits - always implement pagination for lists
5. **Rate limits**: 300 req/min is generous - caching not critical for current usage

---

**Last Updated**: 2025-10-21
