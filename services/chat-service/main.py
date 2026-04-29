from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
from typing import List, Dict
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chat Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_history: List[dict] = []
        self.max_history = 100

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        logger.info(f"User {username} connected. Total connections: {len(self.active_connections)}")

        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Welcome {username}! You are now connected.",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Send message history
        if self.message_history:
            await websocket.send_json({
                "type": "history",
                "messages": self.message_history[-50:]
            })

        # Broadcast user joined
        await self.broadcast_system_message(f"{username} joined the chat")

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
            logger.info(f"User {username} disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_message(self, message: str, username: str):
        msg_data = {
            "type": "message",
            "username": username,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.message_history.append(msg_data)

        # Keep only last 100 messages
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

        # Send to all connected users
        disconnected = []
        for user, connection in self.active_connections.items():
            try:
                await connection.send_json(msg_data)
            except:
                disconnected.append(user)

        # Clean up disconnected users
        for user in disconnected:
            self.disconnect(user)

    async def broadcast_system_message(self, message: str):
        msg_data = {
            "type": "system",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        disconnected = []
        for user, connection in self.active_connections.items():
            try:
                await connection.send_json(msg_data)
            except:
                disconnected.append(user)

        for user in disconnected:
            self.disconnect(user)

    def get_active_users(self):
        return list(self.active_connections.keys())

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Chat Service...")

@app.get("/")
async def root():
    return {
        "service": "Chat Service",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/users")
async def get_active_users():
    return {
        "active_users": manager.get_active_users(),
        "count": len(manager.active_connections)
    }

@app.get("/messages")
async def get_message_history(limit: int = 50):
    return {
        "messages": manager.message_history[-limit:],
        "total": len(manager.message_history)
    }

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()

            # Handle commands
            if data.startswith("/"):
                await handle_command(data, username, websocket)
            else:
                await manager.broadcast_message(data, username)
    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_system_message(f"{username} left the chat")
    except Exception as e:
        logger.error(f"WebSocket error for {username}: {str(e)}")
        manager.disconnect(username)

async def handle_command(command: str, username: str, websocket: WebSocket):
    parts = command.split()
    cmd = parts[0].lower()

    if cmd == "/help":
        help_text = {
            "type": "system",
            "message": "Available commands: /help, /users, /clear",
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket.send_json(help_text)

    elif cmd == "/users":
        users = manager.get_active_users()
        await websocket.send_json({
            "type": "system",
            "message": f"Active users: {', '.join(users)}",
            "timestamp": datetime.utcnow().isoformat()
        })

    elif cmd == "/clear":
        # Clear display (client-side only, send instruction)
        await websocket.send_json({
            "type": "command",
            "command": "clear",
            "timestamp": datetime.utcnow().isoformat()
        })

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "chat-service",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")