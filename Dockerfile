FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    APP_PORT=8003

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

RUN mkdir -p /app/data

EXPOSE 8003

CMD ["python", "-m", "src.webapp"]
