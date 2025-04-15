# Application Monitoring System Documentation

## 1. System Overview

The Application Monitoring System is a comprehensive solution that provides real-time monitoring, logging, and observability for a REST API service. It combines modern tools and practices to deliver insights into application performance, request patterns, and system health.

### Key Features
- Real-time API request monitoring
- Centralized logging system
- Performance metrics collection
- Interactive dashboards
- Load testing capabilities

## 2. Architecture Components

### FastAPI Application
- Core REST API service handling user, product, and order management
- Built with Python FastAPI framework
- Includes middleware for metrics collection
- In-memory storage (configured for demo purposes)

### Message Queue (Kafka)
- Message broker for log aggregation
- Topics structured as `api-logs-{log_type}`
- Ensures reliable log delivery
- Handles high-throughput logging

### Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Loki**: Log aggregation system
- **Grafana**: Visualization and dashboards

## 3. Core Services

### API Service (FastAPI)
- **Location**: `src/api/main.py`
- **Features**:
  - RESTful endpoints for users, products, and orders
  - Request logging middleware
  - Prometheus metrics integration
  - Health check endpoint
- **Metrics Collected**:
  - Request count by method and endpoint
  - Request latency
  - Error rates

### Log Producer
- **Location**: `src/api/kafka_producer.py`
- **Purpose**: Sends application logs to Kafka
- **Features**:
  - Automatic timestamp addition
  - JSON serialization with datetime handling
  - Topic-based log routing
  - Error handling and retry logic

### Log Consumer
- **Location**: `src/api/kafka_consumer.py`
- **Purpose**: Processes logs from Kafka and forwards to Loki
- **Features**:
  - Subscribes to all api-logs topics
  - Formats logs for Loki ingestion
  - Reliable message processing
  - Error handling and recovery

### Load Generator
- **Location**: `src/api/load_generator.py`
- **Purpose**: Simulates API traffic for testing
- **Features**:
  - Configurable request rate
  - Mixed endpoint testing
  - Random data generation
  - Async request handling

## 4. Data Flow

### Request Flow
1. Client makes request to API
2. API middleware captures request metrics
3. Metrics sent to Prometheus
4. Request logs sent to Kafka
5. Log consumer processes messages
6. Logs forwarded to Loki
7. Grafana visualizes metrics and logs

### Log Flow
```mermaid
flowchart LR
    A[API Request] -->|Middleware| B[Kafka Producer]
    B -->|Topics| C[Kafka]
    C -->|Consumer| D[Log Consumer]
    D -->|Push API| E[Loki]
    E -->|Query| F[Grafana]
```

## 5. Monitoring & Observability

### Prometheus Configuration
- **Location**: `config/prometheus/prometheus.yml`
- **Scrape Interval**: 15s
- **Targets**:
  - API service (port 8000)
  - Prometheus itself

### Loki Configuration
- **Location**: `config/loki/local-config.yaml`
- **Features**:
  - Local storage mode
  - 7-day retention period
  - BoltDB indexing
  - In-memory ring

### Grafana Dashboard
- **Location**: `config/grafana/provisioning/dashboards/json/api_monitoring.json`
- **Panels**:
  1. Request Rate by HTTP Method
  2. Requests per Endpoint
  3. Error Rate (Non-2xx)
  4. Error Rate Percentage
  5. API Logs Stream

### Metrics Collected
- **Request Metrics**:
  ```python
  REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
  REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
  ```

## 6. API Endpoints

### User Management
```
GET /users - List all users
GET /users/{user_id} - Get specific user
POST /users - Create new user
```

### Product Management
```
GET /products - List all products
GET /products/{product_id} - Get specific product
POST /products - Create new product
```

### Order Management
```
GET /orders - List all orders
GET /orders/{order_id} - Get specific order
POST /orders - Create new order
```

### System Endpoints
```
GET /health - Health check
GET /metrics - Prometheus metrics
GET /analytics - System statistics
```

## 7. Load Testing

### Configuration
- Default request rate: 10 requests/second
- Mixed endpoint testing
- Randomized data generation

### Test Scenarios
1. **Users**
   - Random user creation
   - User listing
   - Individual user retrieval

2. **Products**
   - Product creation with random data
   - Product listing
   - Individual product retrieval

3. **Orders**
   - Order creation with random products
   - Order listing
   - Individual order retrieval

### Sample Data
```python
SAMPLE_USERS = [
    {"username": f"user{i}", "email": f"user{i}@example.com"}
    for i in range(1, 6)
]

SAMPLE_PRODUCTS = [
    {
        "name": f"Product {i}",
        "price": random.uniform(10.0, 1000.0),
        "description": f"Description for product {i}",
        "stock": random.randint(1, 100)
    }
    for i in range(1, 6)
]
```

## 8. Deployment

### Docker Services
- All components containerized
- Internal network: `monitoring_network`
- Volume persistence for Prometheus and Grafana data

### Service Dependencies
```mermaid
flowchart TD
    A[API] --> B[Kafka]
    B --> C[Zookeeper]
    D[Load Generator] --> A
    E[Log Consumer] --> B
    E --> F[Loki]
    G[Grafana] --> H[Prometheus]
    G --> F
```

### Access Points
- API: http://localhost:8000
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

## 9. Best Practices

### Logging
- Structured JSON logging
- Consistent timestamp format
- Log level differentiation
- Contextual information inclusion

### Monitoring
- Real-time metrics collection
- Error rate tracking
- Latency monitoring
- Resource utilization tracking

### Security
- Grafana authentication
- Network isolation
- Service-specific ports
- Error handling without exposure

This documentation provides a comprehensive overview of the Application Monitoring System. For specific implementation details, refer to the source code in the respective directories.
