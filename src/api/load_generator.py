import asyncio
import aiohttp
import random
import json
from datetime import datetime

# Configuration
BASE_URL = "http://api:8000"
REQUEST_RATE = 10  # requests per second
ENDPOINTS = [
    ("GET", "/users"),
    ("GET", "/products"),
    ("GET", "/orders"),
    ("GET", "/analytics"),
    ("GET", "/health"),
    ("POST", "/users"),
    ("POST", "/products"),
    ("POST", "/orders"),
    ("GET", "/non-existent")
    
]

# Sample data for POST requests
SAMPLE_USERS = [
    {"username": f"user{i}", "email": f"user{i}@example.com"} for i in range(1, 6)
]

SAMPLE_PRODUCTS = [
    {"name": f"Product {i}", "price": random.uniform(10.0, 1000.0), 
     "description": f"Description for product {i}", "stock": random.randint(1, 100)}
    for i in range(1, 6)
]

async def generate_load(session):
    """Generate a single request to a random endpoint"""
    method, endpoint = random.choice(ENDPOINTS)
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            async with session.get(url) as response:
                await response.text()
                print(f"{datetime.now().isoformat()} - {method} {endpoint} - Status: {response.status}")
        
        elif method == "POST":
            payload=None
            # Prepare payload based on endpoint
            if endpoint == "/users":
                payload = random.choice(SAMPLE_USERS)
            elif endpoint == "/products":
                payload = random.choice(SAMPLE_PRODUCTS)
            elif endpoint == "/orders":
                # For orders, we need existing user and product IDs
                payload = {
                    "user_id": random.randint(1, 5),
                    "product_id": random.randint(1, 5),
                    "quantity": random.randint(1, 10),
                    "total_price": random.uniform(10.0, 1000.0),
                    "status": random.choice(["pending", "completed", "cancelled"])
                }
            
            async with session.post(url, json=payload) as response:
                await response.text()
                print(f"{datetime.now().isoformat()} - {method} {endpoint} - Status: {response.status}")
                
    except Exception as e:
        print(f"Error: {e}")

async def main():
    """Main load generation loop"""
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = []
            for _ in range(REQUEST_RATE):
                tasks.append(generate_load(session))
            
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)  # Wait for 1 second before next batch

if __name__ == "__main__":
    print("Starting load generator...")
    asyncio.run(main())
