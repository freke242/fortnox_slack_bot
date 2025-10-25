#!/bin/sh
set -e

# Railway Volume Permission Fix + Security
# This script runs as root, fixes volume permissions, then drops to non-root user

echo "========================================"
echo "🚀 ENTRYPOINT: Starting Fortnox Slack Bot..."
echo "   Current user: $(whoami) (uid=$(id -u))"
echo "========================================"

# Check if we're running as root
if [ "$(id -u)" = "0" ]; then
    echo "ENTRYPOINT: Running as root, setting up secure environment..."
    
    # Create botuser if it doesn't exist
    if ! id -u botuser > /dev/null 2>&1; then
        useradd -m -u 1000 -s /bin/bash botuser
        echo "✅ Created botuser (uid 1000)"
    fi
    
    # Fix permissions for app directory
    chown -R botuser:botuser /app
    echo "✅ Fixed /app permissions"
    
    # Fix Railway volume permissions if volume is mounted
    if [ -n "$RAILWAY_VOLUME_MOUNT_PATH" ] && [ -d "$RAILWAY_VOLUME_MOUNT_PATH" ]; then
        echo "📁 ENTRYPOINT: Railway volume detected at: $RAILWAY_VOLUME_MOUNT_PATH"
        chown -R botuser:botuser "$RAILWAY_VOLUME_MOUNT_PATH"
        echo "✅ ENTRYPOINT: Fixed volume permissions"
    fi
    
    echo "========================================"
    echo "🔒 ENTRYPOINT: Dropping to non-root user (botuser)..."
    echo "========================================"
    # Use su to switch to botuser and run the app
    exec su -s /bin/sh botuser -c "cd /app && exec python -m src.bot"
else
    echo "ENTRYPOINT: Already running as non-root user"
    exec python -m src.bot
fi
