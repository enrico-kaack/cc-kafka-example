# Kafka Producer-Consumer Kubernetes Demo

This repository demonstrates a Python application interacting with Kafka, containerized and ready for Kubernetes.

## Core Concepts

- **Producer**: A Python app (FastAPI) that accepts HTTP requests and sends them to a Kafka topic.
- **Consumer (Load Balanced)**: Multiple instances sharing a single consumer group. Kafka ensures each message is processed by only one instance in the group.
- **Consumer (Broadcast)**: Each instance uses a unique consumer group ID, so every instance receives every message.

## Application Modes

The application (`app/main.py`) behavior is defined by environment variables:

- `APP_MODE`: `PRODUCER` (exposes HTTP port 8080) or `CONSUMER` (listens to Kafka).
- `KAFKA_BOOTSTRAP_SERVERS`: Address of the Kafka broker.
- `KAFKA_TOPIC`: Topic name (default: `demo-topic`).
- `UNIQUE_GROUP_ID`: Set to `true` in Consumer mode to enable broadcast behavior (each pod gets its own UUID-suffixed group).

## Kubernetes Manifests (`k8s/`)

- `kafka-topic.yaml`: A basic Kafka Topic definition that will create a topic in Kafka.
- `producer.yaml`: The HTTP-to-Kafka gateway.
- `consumer-group.yaml`: Deployment with 2 replicas sharing `shared-group`.
- `consumer-broadcast.yaml`: Deployment with 2 replicas where each gets every message.

## Deployment

1. **Build the Docker Image**:
   ```bash
   docker build -t kafka-demo-app:latest .
   ```

2. **Deploy Components**:
   ```bash
   kubectl apply -f k8s/kafka.yaml
   kubectl apply -f k8s/producer.yaml
   kubectl apply -f k8s/consumer-group.yaml
   kubectl apply -f k8s/consumer-broadcast.yaml
   ```

## Testing the Demo

1. **Expose the Producer**:
   ```bash
   kubectl port-forward service/producer 8080:80
   ```

2. **Send a Message**:
   ```bash
   curl "http://localhost:8080/produce?message=HelloKafka"
   ```

3. **Check the Logs**:
   - **Load Balanced**: `kubectl logs -l app=consumer-group` (Only one pod will show the message).
   - **Broadcast**: `kubectl logs -l app=consumer-broadcast` (Both pods will show the message).
