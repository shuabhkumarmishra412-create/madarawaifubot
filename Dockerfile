FROM python:3.11-slim-bookworm

# Environment settings
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (only what's actually useful)
RUN apt update && apt install -y --no-install-recommends \
    git \
    curl \
    ffmpeg \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    libwebp-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip tools
RUN pip install --upgrade pip setuptools wheel

# Create app directory
WORKDIR /app

# Clone your repo
RUN git clone https://github.com/Mynameishekhar/ptb .

# Install Python dependencies
RUN pip install -r requirements.txt

# Start your bot
CMD ["python", "-m", "shivu"]
