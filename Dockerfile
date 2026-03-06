FROM python:3.11-slim

WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY apify_server.py ./

# Environment variables (optional)
ENV FRED_API_KEY=""

# Expose MCP port for Apify
EXPOSE 8080

CMD ["python3", "apify_server.py"]
