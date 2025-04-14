from fastapi import FastAPI, Query, Request, Response
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
import os
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# MongoDB connection
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://mongodb:27017/")
client = MongoClient(MONGODB_URI)
db = client["api_logs"]
collection = db["request_logs"]

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Grafana Simple JSON Datasource API implementation
@app.post("/search")
async def search(request: Request):
    """Endpoint for Grafana to query available metrics"""
    return ["logs", "stats"]

@app.post("/query")
async def query(request: Request):
    """Endpoint for Grafana to query data"""
    payload = await request.json()
    targets = payload.get("targets", [])
    
    result = []
    
    for target in targets:
        target_type = target.get("target", "")
        
        if target_type == "logs":
            # Return the most recent logs
            logs = list(collection.find().sort("timestamp", -1).limit(100))
            for log in logs:
                log["_id"] = str(log["_id"])
            
            # Format data as a table for Grafana
            table_data = {
                "columns": [
                    {"text": "timestamp", "type": "time"},
                    {"text": "method", "type": "string"},
                    {"text": "path", "type": "string"},
                    {"text": "status_code", "type": "number"},
                    {"text": "duration", "type": "number"},
                    {"text": "log_type", "type": "string"}
                ],
                "rows": [],
                "type": "table"
            }
            
            for log in logs:
                table_data["rows"].append([
                    log.get("timestamp", ""),
                    log.get("method", ""),
                    log.get("path", ""),
                    log.get("status_code", 0),
                    log.get("duration", 0),
                    log.get("log_type", "")
                ])
            
            result.append(table_data)
            
        elif target_type == "stats":
            # Generate stats from MongoDB data
            stats = {}
            
            # Total requests
            stats["total_requests"] = collection.count_documents({})
            
            # Average duration
            pipeline = [
                {"$group": {"_id": None, "avg_duration": {"$avg": "$duration"}}}
            ]
            avg_duration = list(collection.aggregate(pipeline))
            stats["avg_duration"] = avg_duration[0]["avg_duration"] if avg_duration else 0
            
            # Error rate
            total = stats["total_requests"]
            error_count = collection.count_documents({"status_code": {"$gte": 400}})
            stats["error_rate"] = (error_count / total) * 100 if total > 0 else 0
            
            # Success rate
            success_count = collection.count_documents({"status_code": {"$gte": 200, "$lt": 300}})
            stats["success_rate"] = (success_count / total) * 100 if total > 0 else 0
            
            # Requests by method
            pipeline = [
                {"$group": {"_id": "$method", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            requests_by_method = list(collection.aggregate(pipeline))
            stats["requests_by_method"] = requests_by_method
            
            # Requests by path
            pipeline = [
                {"$group": {"_id": "$path", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            requests_by_path = list(collection.aggregate(pipeline))
            stats["requests_by_path"] = requests_by_path
            
            # Slowest endpoints
            pipeline = [
                {"$group": {
                    "_id": {"method": "$method", "path": "$path"},
                    "avg_duration": {"$avg": "$duration"},
                    "count": {"$sum": 1},
                    "max_duration": {"$max": "$duration"}
                }},
                {"$sort": {"avg_duration": -1}},
                {"$limit": 10}
            ]
            stats["slowest_endpoints"] = list(collection.aggregate(pipeline))
            
            # Format each stat as a separate time series for Grafana
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # Total requests
            result.append({
                "target": "total_requests",
                "datapoints": [[stats["total_requests"], timestamp]]
            })
            
            # Average duration
            result.append({
                "target": "avg_duration",
                "datapoints": [[stats["avg_duration"], timestamp]]
            })
            
            # Error rate
            result.append({
                "target": "error_rate",
                "datapoints": [[stats["error_rate"], timestamp]]
            })
            
            # Success rate
            result.append({
                "target": "success_rate",
                "datapoints": [[stats["success_rate"], timestamp]]
            })
            
            # Requests by method as table
            method_table = {
                "columns": [
                    {"text": "method", "type": "string"},
                    {"text": "count", "type": "number"}
                ],
                "rows": [],
                "type": "table",
                "target": "requests_by_method"
            }
            
            for item in stats["requests_by_method"]:
                method_table["rows"].append([item["_id"], item["count"]])
            
            result.append(method_table)
            
            # Requests by path as table
            path_table = {
                "columns": [
                    {"text": "path", "type": "string"},
                    {"text": "count", "type": "number"}
                ],
                "rows": [],
                "type": "table",
                "target": "requests_by_path"
            }
            
            for item in stats["requests_by_path"]:
                path_table["rows"].append([item["_id"], item["count"]])
            
            result.append(path_table)
            
            # Slowest endpoints as table
            slowest_table = {
                "columns": [
                    {"text": "method", "type": "string"},
                    {"text": "path", "type": "string"},
                    {"text": "avg_duration", "type": "number"},
                    {"text": "count", "type": "number"},
                    {"text": "max_duration", "type": "number"}
                ],
                "rows": [],
                "type": "table",
                "target": "slowest_endpoints"
            }
            
            for item in stats["slowest_endpoints"]:
                slowest_table["rows"].append([
                    item["_id"]["method"],
                    item["_id"]["path"],
                    item["avg_duration"],
                    item["count"],
                    item["max_duration"]
                ])
            
            result.append(slowest_table)
            
    return result

@app.post("/annotations")
async def annotations(request: Request):
    """Endpoint for Grafana to query annotations"""
    return []

@app.get("/tag-keys")
async def tag_keys():
    """Endpoint for Grafana to query tag keys"""
    return []

@app.get("/tag-values")
async def tag_values():
    """Endpoint for Grafana to query tag values"""
    return []

@app.get("/logs")
def get_logs(
    limit: int = Query(100, gt=0, le=1000),
    skip: int = Query(0, ge=0),
    method: Optional[str] = None,
    path: Optional[str] = None,
    min_status: Optional[int] = None,
    max_status: Optional[int] = None,
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
):
    """Get logs from MongoDB with filtering options"""
    query = {}
    
    # Apply filters if provided
    if method:
        query["method"] = method
    
    if path:
        query["path"] = {"$regex": path}
    
    if min_status is not None or max_status is not None:
        query["status_code"] = {}
        if min_status is not None:
            query["status_code"]["$gte"] = min_status
        if max_status is not None:
            query["status_code"]["$lte"] = max_status
    
    if from_time or to_time:
        query["timestamp"] = {}
        if from_time:
            query["timestamp"]["$gte"] = from_time
        if to_time:
            query["timestamp"]["$lte"] = to_time
    
    logger.info(f"Query: {query}")
    
    # Execute query
    logs = list(collection.find(query).sort("timestamp", -1).skip(skip).limit(limit))
    
    # Convert ObjectId to string
    for log in logs:
        log["_id"] = str(log["_id"])
    
    return logs

@app.get("/stats")
def get_stats():
    """Get statistical data for dashboard metrics"""
    stats = {}
    
    # Total requests
    stats["total_requests"] = collection.count_documents({})
    
    # Count by method
    pipeline = [
        {"$group": {"_id": "$method", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    stats["requests_by_method"] = list(collection.aggregate(pipeline))
    
    # Count by path
    pipeline = [
        {"$group": {"_id": "$path", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    stats["requests_by_path"] = list(collection.aggregate(pipeline))
    
    # Count by status code
    pipeline = [
        {"$group": {"_id": "$status_code", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    stats["requests_by_status"] = list(collection.aggregate(pipeline))
    
    # Average duration
    pipeline = [
        {"$group": {"_id": None, "avg_duration": {"$avg": "$duration"}}}
    ]
    avg_duration = list(collection.aggregate(pipeline))
    stats["avg_duration"] = avg_duration[0]["avg_duration"] if avg_duration else 0
    
    # Error rate
    total = stats["total_requests"]
    error_count = collection.count_documents({"status_code": {"$gte": 400}})
    stats["error_rate"] = (error_count / total) * 100 if total > 0 else 0
    
    # Success rate
    success_count = collection.count_documents({"status_code": {"$gte": 200, "$lt": 300}})
    stats["success_rate"] = (success_count / total) * 100 if total > 0 else 0
    
    # Slowest endpoints
    pipeline = [
        {"$group": {
            "_id": {"method": "$method", "path": "$path"},
            "avg_duration": {"$avg": "$duration"},
            "count": {"$sum": 1},
            "max_duration": {"$max": "$duration"}
        }},
        {"$sort": {"avg_duration": -1}},
        {"$limit": 10}
    ]
    stats["slowest_endpoints"] = list(collection.aggregate(pipeline))
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 