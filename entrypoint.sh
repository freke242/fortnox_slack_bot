#!/bin/sh
set -e

# Railway Volume Permission Fix + Security
# This script runs as root, fixes volume permissions, then drops to non-root user

echo "========================================" >&2
echo "🚀 ENTRYPOINT: Starting Fortnox Slack Bot..." >&2
echo "   Current user: $(whoami) (uid=$(id -u))" >&2
echo "========================================" >&2

# Check if we're running as root
if [ "$(id -u)" = "0" ]; then
    echo "ENTRYPOINT: Running as root, setting up secure environment..." >&2
    
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
        echo "📁 ENTRYPOINT: Railway volume detected at: $RAILWAY_VOLUME_MOUNT_PATH" >&2
        chown -R botuser:botuser "$RAILWAY_VOLUME_MOUNT_PATH"
        echo "✅ ENTRYPOINT: Fixed volume permissions" >&2
    fi
    
    echo "========================================" >&2
    echo "🔒 ENTRYPOINT: Dropping to non-root user (botuser)..." >&2
    echo "========================================" >&2
    # Use su to switch to botuser and run the app
    exec su -s /bin/sh botuser -c "cd /app && exec python app.py"
else
    echo "ENTRYPOINT: Already running as non-root user" >&2
    exec python /app/app.py
fi
