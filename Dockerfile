FROM python:3.11-slim

# Install system dependencies for confluent-kafka (librdkafka)
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Default environment variables
ENV APP_MODE=PRODUCER
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ENV KAFKA_TOPIC=demo-topic
ENV PORT=8080

EXPOSE 8080

CMD ["python", "main.py"]
