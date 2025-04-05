# Application Monitoring Dashboard

This project implements a comprehensive monitoring solution for a REST API using:
- FastAPI for the REST API server
- Apache Kafka for log ingestion
- Prometheus for metrics collection
- Loki for log aggregation
- Grafana for visualization

## Project Structure

```
.
├── config/
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/
│   │       └── datasources/
│   ├── loki/
│   └── prometheus/
├── docker/
│   └── Dockerfile.api
├── src/
│   └── api/
│       ├── main.py
│       ├── models.py
│       └── load_generator.py
├── docker-compose.yml
└── requirements.txt
```

## Features

### API Endpoints
- Users: CRUD operations for users
- Products: CRUD operations for products
- Orders: CRUD operations for orders
- Analytics: System analytics
- Health: System health check
- Metrics: Prometheus metrics endpoint

### Monitoring Dashboards
1. Request Count per Endpoint
   - Track the number of requests made to each API endpoint
2. Response Time Trends
   - Display response time patterns over different time periods
3. Most Frequent Errors
   - Identify and highlight recurring errors
4. Real-Time Logs
   - Live feed of application logs

## Prerequisites

- Docker and Docker Compose
- Python 3.9 or higher (for local development)

## Setup and Running

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Start the services using Docker Compose:
```bash
docker-compose up --build
```

3. Access the services:
   - FastAPI Documentation: http://localhost:8000/docs
   - Grafana Dashboard: http://localhost:3000
   - Prometheus: http://localhost:9090
   - Loki: http://localhost:3100

4. Login to Grafana:
   - URL: http://localhost:3000
   - Username: admin
   - Password: admin

## Monitoring Components

### FastAPI Application
- REST API with built-in metrics endpoint
- Prometheus metrics integration
- Structured logging

### Prometheus
- Scrapes metrics from the API every 15 seconds
- Stores time-series data
- Provides query interface for metrics

### Loki
- Aggregates logs from all services
- Provides query interface for logs
- Integrates with Grafana for visualization

### Grafana
- Pre-configured dashboards for monitoring
- Multiple data sources (Prometheus + Loki)
- Real-time metrics visualization

## Development

To run the load generator separately:
```bash
python -m src.api.load_generator
```

This will simulate traffic to your API endpoints for testing the monitoring setup.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details
