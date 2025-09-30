# 📚 Documentation Overview

Complete documentation for the Fortnox Slack Bot project.

## 🎯 Documentation Structure

```
fortnox_slack_bot/
├── 📖 README.md                 # Main documentation & setup guide
├── ⚡ QUICKSTART.md             # 10-minute quick start guide  
├── 🏢 FORTNOX_SETUP.md          # Detailed Fortnox service account setup
├── 🚀 DEPLOYMENT.md             # Production deployment guide
├── 🤝 CONTRIBUTING.md           # Contribution guidelines
└── 📝 CHANGELOG.md              # Version history & roadmap
```

---

## 📋 Reading Order

### For New Users (Start Here!)

1. **[README.md](README.md)** - Understand what the bot does
2. **[QUICKSTART.md](QUICKSTART.md)** - Get it running in 10 minutes
3. **[FORTNOX_SETUP.md](FORTNOX_SETUP.md)** - Setup Fortnox service account (if needed)

### For Production Deployment

1. **[QUICKSTART.md](QUICKSTART.md)** - Initial setup
2. **[FORTNOX_SETUP.md](FORTNOX_SETUP.md)** - Configure service account
3. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deploy with systemd/Docker

### For Contributors

1. **[README.md](README.md)** - Understand the project
2. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Learn how to contribute
3. **[CHANGELOG.md](CHANGELOG.md)** - See what's planned

---

## 📖 Document Summaries

### [README.md](README.md)
**Main project documentation**
- Project overview and features
- Complete setup instructions
- Configuration details
- Usage examples
- Troubleshooting

### [QUICKSTART.md](QUICKSTART.md) ⚡
**10-minute setup guide**
- Step-by-step setup (5 steps)
- Slack App configuration
- Automated Fortnox token retrieval
- Quick testing and deployment
- Essential troubleshooting

### [FORTNOX_SETUP.md](FORTNOX_SETUP.md) 🏢
**Detailed Fortnox configuration**
- Service account explanation
- Manual and automated setup methods
- OAuth flow details
- Token refresh configuration
- Security best practices

### [DEPLOYMENT.md](DEPLOYMENT.md) 🚀
**Production deployment guide**
- Systemd service setup (Linux)
- Docker deployment
- Cloud platform deployment (AWS, Azure, GCP)
- Monitoring and maintenance
- Auto-restart configuration

### [CONTRIBUTING.md](CONTRIBUTING.md) 🤝
**Contribution guidelines**
- How to report bugs
- How to suggest features
- Pull request process
- Code style guidelines
- Development setup

### [CHANGELOG.md](CHANGELOG.md) 📝
**Version history**
- Current version features
- Planned enhancements
- Roadmap for future releases

---

## 🔧 Technical Documentation

### Scripts & Tools

| Script | Purpose | Documentation |
|--------|---------|---------------|
| `get_fortnox_token.py` | Automated OAuth token retrieval | See FORTNOX_SETUP.md |
| `refresh_token.py` | Auto-refresh access tokens | See FORTNOX_SETUP.md |
| `test_fortnox.py` | Test Fortnox API connection | See QUICKSTART.md |
| `validate_config.py` | Validate environment variables | See README.md |
| `check_setup.py` | Complete setup validation | See QUICKSTART.md |
| `setup.sh` | Automated project setup | See QUICKSTART.md |
| `info.sh` | Display project information | Run `./info.sh` |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (tokens, secrets) |
| `.env.example` | Environment template |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Docker container config |
| `docker-compose.yml` | Docker Compose setup |
| `fortnox-bot.service` | Systemd service file |

---

## 🆘 Getting Help

### Common Issues

1. **Setup Issues** → See [QUICKSTART.md](QUICKSTART.md) Troubleshooting section
2. **Fortnox Auth Issues** → See [FORTNOX_SETUP.md](FORTNOX_SETUP.md) Troubleshooting section
3. **Deployment Issues** → See [DEPLOYMENT.md](DEPLOYMENT.md) Troubleshooting section
4. **Bot not responding** → See [README.md](README.md) Troubleshooting section

### Support Resources

- 📖 Read the documentation (start with README.md)
- 🔍 Search existing issues in the repository
- 💬 Create a new issue with detailed information
- 📧 Include logs and error messages

---

## 🎯 Quick Links

### External Documentation

- [Slack API Documentation](https://api.slack.com/docs)
- [Slack Bolt Python](https://slack.dev/bolt-python/)
- [Fortnox API Documentation](https://developer.fortnox.se/)
- [Fortnox API Reference](https://api.fortnox.se/apidocs)
- [Service Accounts Guide](https://www.fortnox.se/developer/blog/service-accounts)

### Project Resources

- [GitHub Repository](#) - Source code
- [Issue Tracker](#) - Bug reports & features
- [Discussions](#) - Questions & ideas

---

## 📊 Documentation Stats

- **Total Documents**: 6 markdown files
- **Total Scripts**: 7 Python tools
- **Setup Time**: ~10 minutes
- **Last Updated**: 2025-09-30

---

**Start here:** [QUICKSTART.md](QUICKSTART.md) → Get your bot running in 10 minutes! ⚡
