from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import os
import redis
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

REDIS_HOST = os.getenv("REDIS_HOST", "10.215.18.155")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

class RedisPubSub:
    def __init__(self):
        self.redis_client = None
        self.pubsub = None
        self.active_connections: Dict[str, WebSocket] = {}
        self.channel = "chat_messages"
        
    def connect_redis(self):
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe(self.channel)
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    def publish_message(self, message: dict):
        if self.redis_client:
            try:
                self.redis_client.publish(self.channel, json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to publish: {e}")
        return False
    
    async def listen_for_messages(self):
        if not self.pubsub:
            return
        while True:
            try:
                message = self.pubsub.get_message(timeout=1)
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    await self.broadcast_to_local(data)
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Pub/sub error: {e}")
                await asyncio.sleep(1)
    
    async def broadcast_to_local(self, message: dict):
        disconnected = []
        for username, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except:
                disconnected.append(username)
        for username in disconnected:
            if username in self.active_connections:
                del self.active_connections[username]

redis_pubsub = RedisPubSub()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Notification Service with Redis Pub/Sub...")
    redis_pubsub.connect_redis()
    asyncio.create_task(redis_pubsub.listen_for_messages())

@app.get("/")
async def root():
    return {
        "service": "Notification Service",
        "status": "healthy",
        "version": "1.0.0",
        "websocket": "enabled",
        "redis": redis_pubsub.redis_client is not None
    }

@app.get("/health")
async def health_check():
    redis_status = "connected" if redis_pubsub.redis_client else "disconnected"
    return {
        "status": "healthy",
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat(),
        "redis": redis_status,
        "active_connections": len(redis_pubsub.active_connections)
    }

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    
    # Ensure Redis is connected
    if not redis_pubsub.redis_client:
        redis_pubsub.connect_redis()
        if not redis_pubsub.redis_client:
            await websocket.send_json({
                "type": "system",
                "message": "Chat service unavailable - Redis not connected",
                "timestamp": datetime.utcnow().isoformat()
            })
            await websocket.close()
            return
    
    # Store connection
    redis_pubsub.active_connections[username] = websocket
    logger.info(f"User {username} connected. Total: {len(redis_pubsub.active_connections)}")
    
    # Send welcome message
    await websocket.send_json({
        "type": "system",
        "message": f"Welcome {username}!",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Notify others via Redis
    redis_pubsub.publish_message({
        "type": "system",
        "message": f"{username} joined the chat",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from {username}: {data}")
            
            if data.startswith("/"):
                if data == "/users":
                    users = list(redis_pubsub.active_connections.keys())
                    await websocket.send_json({
                        "type": "system",
                        "message": f"Active users in this instance: {', '.join(users)}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif data == "/help":
                    await websocket.send_json({
                        "type": "system",
                        "message": "Commands: /users - list active users in this instance, /help - this message",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            else:
                # Broadcast to all instances via Redis
                redis_pubsub.publish_message({
                    "type": "message",
                    "username": username,
                    "message": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
    except WebSocketDisconnect:
        if username in redis_pubsub.active_connections:
            del redis_pubsub.active_connections[username]
        logger.info(f"User {username} disconnected. Total: {len(redis_pubsub.active_connections)}")
        redis_pubsub.publish_message({
            "type": "system",
            "message": f"{username} left the chat",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"WebSocket error for {username}: {e}")
        if username in redis_pubsub.active_connections:
            del redis_pubsub.active_connections[username]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
