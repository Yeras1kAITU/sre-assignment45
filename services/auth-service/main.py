from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import secrets
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from jose import jwt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Authentication Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Security
security = HTTPBasic()

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "microservices")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# In-memory user store (for demo purposes)
USERS = {
    "admin": {"password": "admin123", "role": "admin", "email": "admin@example.com"},
    "user1": {"password": "user123", "role": "user", "email": "user1@example.com"},
    "testuser": {"password": "test123", "role": "user", "email": "test@example.com"}
}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Authentication Service...")
    logger.info(f"Database host: {DB_HOST}")

@app.get("/")
async def root():
    return {
        "service": "Authentication Service",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/login")
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    logger.info(f"Login attempt for user: {username}")

    if username in USERS and USERS[username]["password"] == password:
        token_data = {
            "sub": username,
            "role": USERS[username]["role"],
            "email": USERS[username]["email"],
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(token_data, JWT_SECRET, algorithm="HS256")

        return {
            "access_token": token,
            "token_type": "bearer",
            "username": username,
            "role": USERS[username]["role"],
            "expires_in": 86400
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.post("/register")
async def register(username: str, password: str, email: str):
    if username in USERS:
        raise HTTPException(status_code=400, detail="Username already exists")

    USERS[username] = {
        "password": password,
        "role": "user",
        "email": email
    }

    return {"message": "User registered successfully", "username": username}

@app.get("/verify")
async def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {
            "valid": True,
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "expires": datetime.fromtimestamp(payload.get("exp")).isoformat()
        }
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except jwt.JWTError:
        return {"valid": False, "error": "Invalid token"}

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        conn = get_db_connection()
        conn.close()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = f"disconnected: {str(e)}"

    return health_status

@app.get("/metrics")
async def metrics():
    return {"message": "Metrics endpoint active"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")