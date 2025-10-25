# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Copy deployment entrypoint
COPY deployment/entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Security: Start as root to fix volume permissions, then drop to non-root user
# The entrypoint script handles permission fixes and user switching
ENTRYPOINT ["/app/entrypoint.sh"]
