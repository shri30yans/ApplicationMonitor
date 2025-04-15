from kafka import KafkaConsumer
import json
from datetime import datetime
import logging
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogConsumer:
    def __init__(self, bootstrap_servers='kafka:9092', loki_url='http://loki:3100'):
        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            key_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='log_processor_group'
        )
        
        self.loki_url = f"{loki_url}/loki/api/v1/push"

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
        Process a message from Kafka and send it to Loki
        """
        try:
            value = message.value
            
            # Format for Loki
            loki_payload = {
                "streams": [{
                    "stream": {
                        "service": "api",
                        "topic": message.topic
                    },
                    "values": [
                        # Use the timestamp from the message if available, otherwise current time
                        [
                            str(int(datetime.fromisoformat(value.get('timestamp', datetime.now().isoformat())).timestamp() * 1e9)),
                            json.dumps(value, ensure_ascii=False)
                        ]
                    ]
                }]
            }
            
            # Send to Loki
            response = requests.post(
                self.loki_url,
                json=loki_payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            logger.info(f"Sent log to Loki: {value}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def close(self):
        """
        Close connections
        """
        self.consumer.close()

if __name__ == "__main__":
    consumer = LogConsumer()
    consumer.start_consuming()
