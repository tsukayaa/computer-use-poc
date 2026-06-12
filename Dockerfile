# Playwright official image: Chromium + semua dependency OS udah preinstalled.
# Tag samain dengan playwright==1.55.0 di requirements biar versi browser cocok.
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

WORKDIR /app

# Install dependency Python dulu (layer cache: cuma rebuild kalau requirements berubah)
COPY computer-use-preview/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy kode. .env & shots/ dikecualiin lewat .dockerignore.
COPY computer-use-preview/ ./computer-use-preview/
COPY poc/ ./poc/

# GKE = headless wajib (ga ada layar)
ENV PLAYWRIGHT_HEADLESS=true

WORKDIR /app/poc

# Default jalanin user 1. Override pas kubectl run kalau perlu.
CMD ["python", "orchestrator.py", "--user", "1"]
