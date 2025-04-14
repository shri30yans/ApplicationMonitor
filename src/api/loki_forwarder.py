import time
import datetime
import requests
import json
from pymongo import MongoClient
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LokiForwarder:
    def __init__(self, mongo_uri=None, loki_url=None):
        # Get environment variables or use defaults
        mongo_uri = mongo_uri or os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
        loki_url = loki_url or os.environ.get('LOKI_URL', 'http://localhost:3100')
        
        logger.info(f"Connecting to MongoDB at {mongo_uri}")
        logger.info(f"Using Loki at {loki_url}")
        
        # Initialize MongoDB client
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['api_logs']
        self.collection = self.db['request_logs']
        
        # Loki URL
        self.loki_url = f"{loki_url}/loki/api/v1/push"
        
        # Track the last timestamp we processed
        self.last_timestamp = datetime.datetime.now() - datetime.timedelta(minutes=30)
        
    def start_forwarding(self):
        """
        Start forwarding logs from MongoDB to Loki
        """
        logger.info("Started forwarding logs from MongoDB to Loki...")
        
        while True:
            try:
                self._forward_logs()
                time.sleep(5)  # Check for new logs every 5 seconds
            except Exception as e:
                logger.error(f"Error forwarding logs: {e}")
                time.sleep(10)  # Wait a bit longer if there's an error
                
    def _forward_logs(self):
        """
        Forward logs from MongoDB to Loki
        """
        # Find logs newer than the last one we processed
        query = {"timestamp": {"$gt": self.last_timestamp.isoformat()}}
        logs = list(self.collection.find(query).sort("timestamp", 1).limit(100))
        
        if not logs:
            return
            
        logger.info(f"Found {len(logs)} new logs to forward to Loki")
        
        # Group logs by path (for better organization in Loki)
        grouped_logs = {}
        for log in logs:
            path = log.get('path', '/unknown')
            if path not in grouped_logs:
                grouped_logs[path] = []
            grouped_logs[path].append(log)
            
            # Update the last timestamp
            if 'timestamp' in log:
                try:
                    ts = datetime.datetime.fromisoformat(log['timestamp'])
                    if ts > self.last_timestamp:
                        self.last_timestamp = ts
                except (ValueError, TypeError):
                    pass
        
        # Send logs to Loki in batches by path
        for path, path_logs in grouped_logs.items():
            self._send_to_loki(path_logs, path)
            
    def _send_to_loki(self, logs, path):
        """
        Send logs to Loki
        """
        try:
            # Prepare Loki streams
            streams = []
            
            # Create stream for this path
            values = []
            for log in logs:
                # Convert to Loki format
                try:
                    timestamp_ns = int(datetime.datetime.fromisoformat(log['timestamp']).timestamp() * 1e9)
                    # Convert log to string, removing _id which is not JSON serializable
                    log_copy = log.copy()
                    if '_id' in log_copy:
                        del log_copy['_id']
                    log_line = json.dumps(log_copy)
                    values.append([str(timestamp_ns), log_line])
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Error formatting log for Loki: {e}")
                    continue
            
            if not values:
                return
                
            # Create stream for this path
            stream = {
                "stream": {
                    "job": "api",
                    "path": path,
                    "level": "info"
                },
                "values": values
            }
            streams.append(stream)
            
            # Create Loki payload
            payload = {
                "streams": streams
            }
            
            # Send to Loki
            response = requests.post(
                self.loki_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 204:
                logger.warning(f"Failed to send logs to Loki: {response.status_code} - {response.text}")
            else:
                logger.info(f"Successfully sent {len(values)} logs to Loki for path {path}")
                
        except Exception as e:
            logger.error(f"Error sending logs to Loki: {e}")
            
    def close(self):
        """
        Close connections
        """
        self.mongo_client.close()

if __name__ == "__main__":
    forwarder = LokiForwarder()
    try:
        forwarder.start_forwarding()
    except KeyboardInterrupt:
        logger.info("Stopping forwarder...")
    finally:
        forwarder.close() 