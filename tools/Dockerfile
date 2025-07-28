# Bloomberg Gateway API - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bloomberg-gateway-enhanced.py .
COPY central_bloomberg_ticker_repository_v3.json .

# Environment variables (can be overridden)
ENV BLOOMBERG_API_URL="http://20.172.249.92:8080"
ENV ENABLE_CACHE="false"
ENV PORT="8000"

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health').raise_for_status()"

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "bloomberg-gateway-enhanced.py"]