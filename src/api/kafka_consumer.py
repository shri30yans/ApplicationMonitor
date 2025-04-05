from kafka import KafkaConsumer
from pymongo import MongoClient
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogConsumer:
    def __init__(self, bootstrap_servers='kafka:9092', mongo_uri='mongodb://mongodb:27017/'):
        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            key_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='log_processor_group'
        )

        # Initialize MongoDB client
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['api_logs']
        
        # Create indexes for better query performance
        self.db.request_logs.create_index([('timestamp', -1)])
        self.db.request_logs.create_index([('method', 1)])
        self.db.request_logs.create_index([('path', 1)])
        self.db.request_logs.create_index([('status_code', 1)])

    def start_consuming(self):
        """
        Start consuming messages from Kafka topics
        """
        # Subscribe to all api-logs topics
        self.consumer.subscribe(pattern='api-logs-.*')
        
        logger.info("Started consuming messages...")
        
        try:
            for message in self.consumer:
                self._process_message(message)
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
        finally:
            self.close()

    def _process_message(self, message):
        """
        Process a message from Kafka and store it in MongoDB
        """
        try:
            # Extract topic name to determine collection
            topic = message.topic
            value = message.value
            
            # Store in MongoDB
            collection = self.db.request_logs
            result = collection.insert_one(value)
            
            logger.info(f"Stored message in MongoDB with ID: {result.inserted_id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def close(self):
        """
        Close connections
        """
        self.consumer.close()
        self.mongo_client.close()

if __name__ == "__main__":
    consumer = LogConsumer()
    consumer.start_consuming()
