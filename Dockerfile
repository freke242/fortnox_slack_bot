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

# Create non-root user and prepare data directory for Railway volume
RUN useradd -m -u 1000 botuser && \
    mkdir -p /data && \
    chown -R botuser:botuser /app /data

# Switch to non-root user
USER botuser

# Run the application
CMD ["python", "app.py"]
