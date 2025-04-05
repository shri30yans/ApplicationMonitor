from kafka import KafkaProducer
import json
from datetime import datetime

class LogProducer:
    def __init__(self, bootstrap_servers='kafka:9092'):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def send_log(self, log_type: str, message: dict):
        """
        Send log message to appropriate Kafka topic based on log type
        """
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.now().isoformat()
            
        # Add log type to message
        message['log_type'] = log_type
        
        # Send to appropriate topic
        topic = f'api-logs-{log_type}'
        
        try:
            self.producer.send(
                topic=topic,
                value=message,
                key=str(message.get('path', ''))  # Use endpoint path as key for partitioning
            )
            self.producer.flush()  # Ensure the message is sent
        except Exception as e:
            print(f"Error sending message to Kafka: {e}")

    def close(self):
        """
        Close the Kafka producer
        """
        self.producer.close()
