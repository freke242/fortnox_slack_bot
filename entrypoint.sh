#!/bin/sh
set -e

# Railway Volume Permission Fix + Security
# This script runs as root, fixes volume permissions, then drops to non-root user

echo "🚀 Starting Fortnox Slack Bot..."

# Check if we're running as root
if [ "$(id -u)" = "0" ]; then
    echo "Running as root, setting up secure environment..."
    
    # Create botuser if it doesn't exist
    if ! id -u botuser > /dev/null 2>&1; then
        adduser -D -u 1000 botuser
        echo "✅ Created botuser (uid 1000)"
    fi
    
    # Fix permissions for app directory
    chown -R botuser:botuser /app
    echo "✅ Fixed /app permissions"
    
    # Fix Railway volume permissions if volume is mounted
    if [ -n "$RAILWAY_VOLUME_MOUNT_PATH" ] && [ -d "$RAILWAY_VOLUME_MOUNT_PATH" ]; then
        echo "📁 Railway volume detected at: $RAILWAY_VOLUME_MOUNT_PATH"
        chown -R botuser:botuser "$RAILWAY_VOLUME_MOUNT_PATH"
        echo "✅ Fixed volume permissions"
    fi
    
    echo "🔒 Dropping to non-root user (botuser)..."
    # Use su to switch to botuser and run the app
    exec su botuser -c "python /app/app.py"
else
    echo "Already running as non-root user"
    exec python /app/app.py
fi
