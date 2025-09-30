# Deployment Guide

This guide covers different ways to deploy the Fortnox Slack Bot in production.

## Option 1: Run as a Systemd Service (Linux)

This is the recommended approach for running on a Linux server.

### Setup

1. **Edit the service file** to match your paths:
   ```bash
   nano fortnox-bot.service
   ```
   Update the `User`, `WorkingDirectory`, and paths as needed.

2. **Copy the service file:**
   ```bash
   sudo cp fortnox-bot.service /etc/systemd/system/
   ```

3. **Reload systemd:**
   ```bash
   sudo systemctl daemon-reload
   ```

4. **Enable the service** (start on boot):
   ```bash
   sudo systemctl enable fortnox-bot
   ```

5. **Start the service:**
   ```bash
   sudo systemctl start fortnox-bot
   ```

### Managing the Service

```bash
# Check status
sudo systemctl status fortnox-bot

# View logs
sudo journalctl -u fortnox-bot -f

# Restart
sudo systemctl restart fortnox-bot

# Stop
sudo systemctl stop fortnox-bot

# Disable (don't start on boot)
sudo systemctl disable fortnox-bot
```

## Option 2: Docker Deployment

Run the bot in a Docker container for easy deployment and isolation.

### Using Docker Compose (Recommended)

1. **Build and start:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop:**
   ```bash
   docker-compose down
   ```

4. **Rebuild after changes:**
   ```bash
   docker-compose up -d --build
   ```

### Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t fortnox-slack-bot .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name fortnox-bot \
     --env-file .env \
     --restart unless-stopped \
     fortnox-slack-bot
   ```

3. **View logs:**
   ```bash
   docker logs -f fortnox-bot
   ```

4. **Stop and remove:**
   ```bash
   docker stop fortnox-bot
   docker rm fortnox-bot
   ```

## Option 3: Screen/Tmux (Simple)

For quick deployments or development servers.

### Using Screen

```bash
# Start a screen session
screen -S fortnox-bot

# Activate virtual environment and run
source venv/bin/activate
python app.py

# Detach: Press Ctrl+A, then D

# Reattach later
screen -r fortnox-bot

# Kill session
screen -X -S fortnox-bot quit
```

### Using Tmux

```bash
# Start a tmux session
tmux new -s fortnox-bot

# Activate virtual environment and run
source venv/bin/activate
python app.py

# Detach: Press Ctrl+B, then D

# Reattach later
tmux attach -t fortnox-bot

# Kill session
tmux kill-session -t fortnox-bot
```

## Option 4: Cloud Platform Deployment

### Heroku

1. **Create `Procfile`:**
   ```
   worker: python app.py
   ```

2. **Deploy:**
   ```bash
   heroku create your-app-name
   heroku config:set SLACK_BOT_TOKEN=xxx
   heroku config:set SLACK_SIGNING_SECRET=xxx
   heroku config:set SLACK_APP_TOKEN=xxx
   heroku config:set FORTNOX_ACCESS_TOKEN=xxx
   heroku config:set FORTNOX_CLIENT_SECRET=xxx
   git push heroku main
   heroku ps:scale worker=1
   ```

### AWS EC2

1. **Launch an EC2 instance** (Ubuntu recommended)
2. **SSH into the instance**
3. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git
   ```
4. **Clone and setup:**
   ```bash
   git clone <your-repo>
   cd fortnox_slack_bot
   ./setup.sh
   ```
5. **Configure environment** (edit .env)
6. **Run as systemd service** (see Option 1)

### DigitalOcean Droplet

Same as AWS EC2 - use the systemd service approach.

## Environment Variables

Ensure these are set in your deployment:

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
FORTNOX_ACCESS_TOKEN=...
FORTNOX_CLIENT_SECRET=...
```

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use strong secrets** for all tokens
3. **Limit file permissions:**
   ```bash
   chmod 600 .env
   ```
4. **Run as non-root user** (systemd service already does this)
5. **Keep dependencies updated:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```
6. **Monitor logs** for suspicious activity
7. **Rotate tokens** periodically

## Monitoring

### Health Checks

Create a simple health check script:

```python
# health_check.py
import sys
import requests

try:
    # Check if bot process is running
    # Add your health check logic here
    sys.exit(0)
except:
    sys.exit(1)
```

### Set up Monitoring

- Use **Uptime Robot** or **Pingdom** for uptime monitoring
- Set up **log aggregation** (e.g., ELK stack, Datadog)
- Configure **alerts** for errors or downtime

## Backup and Recovery

1. **Backup `.env` file** securely (encrypted)
2. **Document your Slack app configuration**
3. **Keep a copy of your Fortnox API credentials**
4. **Version control** your code (excluding .env)

## Troubleshooting Production Issues

### Bot stops responding

```bash
# Check if running (systemd)
sudo systemctl status fortnox-bot

# Check logs
sudo journalctl -u fortnox-bot -n 100

# Restart
sudo systemctl restart fortnox-bot
```

### High memory usage

```bash
# Check resource usage
docker stats fortnox-bot  # For Docker
top -p $(pgrep -f app.py)  # For systemd
```

### Connection issues

- Verify internet connectivity
- Check Slack API status: https://status.slack.com/
- Check Fortnox API status
- Verify tokens haven't expired

## Scaling

For high-traffic deployments:

1. **Run multiple instances** behind a load balancer
2. **Use Redis** for shared state (if needed)
3. **Implement rate limiting**
4. **Cache Fortnox responses**
5. **Use async/await** for better concurrency

## Updates and Maintenance

```bash
# Pull latest changes
git pull

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart fortnox-bot  # systemd
# OR
docker-compose up -d --build  # Docker
```

## Support

For deployment issues:
- Check logs first
- Review this guide
- Consult the main README.md
- Check Slack and Fortnox API documentation
