FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend ./backend

# Create temp directory
RUN mkdir -p /app/backend/temp

# Render provides PORT
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}