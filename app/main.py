import os
import sys
import time
import uuid
import logging
import signal
from fastapi import FastAPI
import uvicorn
from confluent_kafka import Producer, Consumer, KafkaError

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("kafka-demo")

# Configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "demo-topic")
APP_MODE = os.getenv("APP_MODE", "PRODUCER").upper() # PRODUCER or CONSUMER
CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "demo-group")

# If UNIQUE_GROUP_ID is true, each instance gets its own group, effectively broadcasting
UNIQUE_GROUP_ID = os.getenv("UNIQUE_GROUP_ID", "false").lower() == "true"
if UNIQUE_GROUP_ID:
    CONSUMER_GROUP_ID = f"{CONSUMER_GROUP_ID}-{uuid.uuid4()}"
    logger.info(f"Using unique Consumer Group ID: {CONSUMER_GROUP_ID}")

# --- Producer Logic ---
def get_producer():
    conf = {'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS}
    return Producer(conf)

producer = None
if APP_MODE == "PRODUCER":
    producer = get_producer()

def delivery_report(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# --- FastAPI App (for Producer mode) ---
app = FastAPI(title="Kafka Producer Demo")

@app.get("/produce")
async def produce_message(message: str = "Hello Kafka!"):
    if APP_MODE != "PRODUCER":
        return {"error": "App is running in CONSUMER mode"}
    
    try:
        producer.produce(KAFKA_TOPIC, message.encode('utf-8'), callback=delivery_report)
        producer.flush()
        return {"status": "sent", "message": message, "topic": KAFKA_TOPIC}
    except Exception as e:
        logger.error(f"Error producing message: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/health")
async def health():
    return {"status": "ok"}

# --- Consumer Logic ---
def run_consumer():
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': CONSUMER_GROUP_ID,
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_TOPIC])

    logger.info(f"Starting Consumer on topic '{KAFKA_TOPIC}' with group '{CONSUMER_GROUP_ID}'...")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    break
            
            logger.info(f"Received message: {msg.value().decode('utf-8')} from {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

# --- Main Entry Point ---
if __name__ == "__main__":
    import sys
    
    logger.info(f"Starting application in {APP_MODE} mode...")
    
    if APP_MODE == "PRODUCER":
        port = int(os.getenv("PORT", "8080"))
        logger.info(f"Producer HTTP server listening on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    elif APP_MODE == "CONSUMER":
        run_consumer()
    else:
        logger.error(f"Unknown APP_MODE: {APP_MODE}. Use 'PRODUCER' or 'CONSUMER'.")
        sys.exit(1)
