# Changelog

All notable changes to the Fortnox Slack Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-30

### Added
- Initial release of Fortnox Slack Bot
- Slack bot integration using Socket Mode
- Fortnox API client implementation
- `/fortnox-stock` command to list all articles in stock
- `/fortnox-stock [minimum]` command to filter by minimum quantity
- `/fortnox-article <number>` command to get article details
- Bot mention handler for help information
- Comprehensive documentation (README, QUICKSTART, DEPLOYMENT)
- Configuration validation script
- Test script for Fortnox API connection
- Docker support with Dockerfile and docker-compose.yml
- Systemd service file for Linux deployment
- Setup script for easy installation
- Environment variable configuration with .env.example
- Logging configuration for debugging

### Features
- 📦 Real-time inventory tracking
- 🔍 Article search by number
- 📊 Stock filtering by quantity
- 💬 Interactive Slack responses
- 🔐 Secure credential management
- 🐳 Docker deployment support
- 🔄 Auto-restart on failure (systemd)
- 📝 Comprehensive error handling
- 🎨 Formatted table output for stock lists

### Security
- Environment-based credential management
- No hardcoded secrets
- Secure token handling
- Non-root Docker user
- Private temp directory in systemd

### Documentation
- Complete README with setup instructions
- Quick start guide for 5-minute setup
- Deployment guide covering multiple platforms
- API reference documentation
- Troubleshooting guide
- Contributing guidelines

## [Unreleased]

### Planned Features
- Stock level alerts and notifications
- Low stock warnings
- Create and update articles via Slack
- Stock movement history
- Search by multiple criteria (EAN, supplier, etc.)
- Article image display in Slack
- Export data to CSV
- Automated inventory reports
- Scheduled stock reports
- Interactive buttons for common actions
- Multi-language support
- Custom stock location filtering
- Integration with other warehouse systems

### Ideas for Future Releases
- Web dashboard for configuration
- Analytics and reporting
- Stock forecasting
- Barcode scanning integration
- Mobile app notifications
- Integration with shopping carts
- Supplier order automation
- Price tracking and alerts

## Contributing

See [README.md](README.md) for contribution guidelines.

## Support

For issues and questions:
- Check the documentation first
- Search existing issues
- Create a new issue with detailed information
- Include logs and error messages

## License

See [LICENSE](LICENSE) file for details.
