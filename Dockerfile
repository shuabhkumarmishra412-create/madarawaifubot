FROM python:3.11-slim-bookworm

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# Install required system packages
RUN apt update && apt install -y --no-install-recommends \
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

# Set working directory
WORKDIR /app

# Copy your repo files
COPY . .

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install dependencies
RUN pip install -r requirements.txt

# Run bot
CMD ["python", "-m", "shivu"]
