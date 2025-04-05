from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import List, Dict
import logging
import json
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from .kafka_producer import LogProducer
from fastapi import FastAPI, HTTPException
from datetime import datetime
from typing import List, Dict
from fastapi.responses import Response
from .models import User, Product, Order
import time

# Initialize FastAPI app
app = FastAPI(title="Monitoring Dashboard Demo API")

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# In-memory storage (replace with actual database in production)
db = {
    "users": {},
    "products": {},
    "orders": {}
}

# Initialize Kafka producer
log_producer = LogProducer()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Middleware for logging and metrics
@app.middleware("http")
async def logging_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    status_code = response.status_code
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration": duration
    }
    
    # Send to Kafka
    log_producer.send_log("request", log_data)
    
    # Also log locally
    logger.info(json.dumps(log_data))
    
    return response

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# User endpoints
@app.post("/users")
async def create_user(user: User):
    user_id = len(db["users"]) + 1
    user.id = user_id
    user.created_at = datetime.now()
    db["users"][user_id] = user
    return user

@app.get("/users")
async def get_users() -> List[User]:
    return list(db["users"].values())

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> User:
    if user_id not in db["users"]:
        raise HTTPException(status_code=404, detail="User not found")
    return db["users"][user_id]

# Product endpoints
@app.post("/products")
async def create_product(product: Product):
    product_id = len(db["products"]) + 1
    product.id = product_id
    db["products"][product_id] = product
    return product

@app.get("/products")
async def get_products() -> List[Product]:
    return list(db["products"].values())

@app.get("/products/{product_id}")
async def get_product(product_id: int) -> Product:
    if product_id not in db["products"]:
        raise HTTPException(status_code=404, detail="Product not found")
    return db["products"][product_id]

# Order endpoints
@app.post("/orders")
async def create_order(order: Order):
    # Validate user and product exist
    if order.user_id not in db["users"]:
        raise HTTPException(status_code=404, detail="User not found")
    if order.product_id not in db["products"]:
        raise HTTPException(status_code=404, detail="Product not found")
    
    order_id = len(db["orders"]) + 1
    order.id = order_id
    order.created_at = datetime.now()
    db["orders"][order_id] = order
    return order

@app.get("/orders")
async def get_orders() -> List[Order]:
    return list(db["orders"].values())

@app.get("/orders/{order_id}")
async def get_order(order_id: int) -> Order:
    if order_id not in db["orders"]:
        raise HTTPException(status_code=404, detail="Order not found")
    return db["orders"][order_id]

# Analytics endpoint
@app.get("/analytics")
async def get_analytics() -> Dict:
    return {
        "total_users": len(db["users"]),
        "total_products": len(db["products"]),
        "total_orders": len(db["orders"]),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
