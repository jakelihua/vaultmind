FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV HOST=0.0.0.0
ENV VAULTMIND_DATA_DIR=/data

VOLUME ["/data"]

EXPOSE 8080

CMD ["python", "-m", "vaultmind.api.server"]
