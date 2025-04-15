from kafka import KafkaConsumer
from pymongo import MongoClient
import json
from datetime import datetime
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogConsumer:
    def __init__(self, bootstrap_servers='kafka:9092', mongo_uri='mongodb://mongodb:27017/'):
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            key_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='log_processor_group'
        )

        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['api_logs']

        # Create indexes for better query performance
        self.db.request_logs.create_index([('timestamp', -1)])
        self.db.request_logs.create_index([('method', 1)])
        self.db.request_logs.create_index([('path', 1)])
        self.db.request_logs.create_index([('status_code', 1)])

    def start_consuming(self):
        self.consumer.subscribe(pattern='api-logs-.*')
        logger.info("Started consuming messages...")

        try:
            for message in self.consumer:
                self._process_message(message)
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.close()

    def _process_message(self, message):
        try:
            topic = message.topic
            value = message.value
            
            # Insert into MongoDB
            result = self.db.request_logs.insert_one(value)
            mongo_id = result.inserted_id
            
            logger.info(f"Log stored in MongoDB with ID: {mongo_id}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())

    def close(self):
        self.consumer.close()
        self.mongo_client.close()
        logger.info("Closed connections")


if __name__ == "__main__":
    consumer = LogConsumer()
    consumer.start_consuming()
