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

# Copy application files
COPY *.py .
COPY *.md .

# Note: Running as root for Railway volume compatibility
# Railway volumes are mounted with root ownership
# For local/other deployments, consider using a non-root user

# Run the application
CMD ["python", "app.py"]
