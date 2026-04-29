from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, EmailStr
from typing import Optional

app = FastAPI(title="User Service")
Instrumentator().instrument(app).expose(app)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "microservices")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")

class User(BaseModel):
    username: str
    email: str
    full_name: str
    role: Optional[str] = "user"

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
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/")
async def root():
    return {"service": "User Service", "status": "healthy"}

@app.get("/users")
async def get_users():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()
            return {"users": users}
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "healthy", "database": "disconnected"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)