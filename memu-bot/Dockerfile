FROM python:3.13-slim

# Install build dependencies for maturin (Rust-based Python extension) + Playwright browser deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl build-essential pkg-config libssl-dev \
        # Playwright Chromium dependencies
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
        libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
        fonts-liberation libappindicator3-1 xdg-utils && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Install memU from local source first
COPY memu-src /tmp/memu-src
RUN pip install --no-cache-dir /tmp/memu-src && rm -rf /tmp/memu-src

# Install bot dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium

# Copy bot code
COPY bot.py .

# Create data directory for SQLite
RUN mkdir -p /data

CMD ["python", "bot.py"]
