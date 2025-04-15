from kafka import KafkaProducer
import json
from datetime import datetime
from json import JSONEncoder

class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class LogProducer:
    def __init__(self, bootstrap_servers='kafka:9092'):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, cls=DateTimeEncoder).encode('utf-8'),
            key_serializer=lambda v: json.dumps(v, cls=DateTimeEncoder).encode('utf-8')
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
        
        print(f"[DEBUG] Attempting to send log to topic {topic}")
        print(f"[DEBUG] Message content: {message}")
        
        try:
            # Try serializing first to catch any JSON errors
            try:
                json_str = json.dumps(message, cls=DateTimeEncoder)
                print(f"[DEBUG] Successfully serialized message to JSON")
            except Exception as json_error:
                print(f"[ERROR] JSON serialization failed: {json_error}")
                print(f"[ERROR] Message that failed: {message}")
                return
            
            # Send to Kafka
            future = self.producer.send(
                topic=topic,
                value=message,
                key=str(message.get('path', ''))  # Use endpoint path as key for partitioning
            )
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            print(f"[DEBUG] Log sent successfully to {record_metadata.topic}, partition {record_metadata.partition}")
            
            self.producer.flush()  # Ensure the message is sent
            print("[DEBUG] Producer flushed successfully")
            
        except Exception as e:
            print(f"[ERROR] Failed to send message to Kafka: {str(e)}")
            print(f"[ERROR] Topic: {topic}")
            print(f"[ERROR] Message: {message}")

    def close(self):
        """
        Close the Kafka producer
        """
        self.producer.close()
