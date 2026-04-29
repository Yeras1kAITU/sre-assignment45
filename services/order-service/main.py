from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "microservices")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")

class OrderItem(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderCreate(BaseModel):
    user_id: str
    items: List[OrderItem]
    total_amount: float

class OrderStatus(BaseModel):
    status: str

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=5
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@app.on_event("startup")
async def startup():
    logger.info("Order Service starting...")
    logger.info(f"Database host: {DB_HOST}")

@app.get("/")
async def root():
    return {
        "service": "Order Service",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/orders")
async def create_order(order: OrderCreate):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            items_json = json.dumps([item.dict() for item in order.items])
            cur.execute(
                "INSERT INTO orders (user_id, items, total_amount, status, created_at) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (order.user_id, items_json, order.total_amount, 'pending', datetime.utcnow())
            )
            order_id = cur.fetchone()['id']
            conn.commit()
            logger.info(f"Order created: {order_id}")
            return {
                "order_id": order_id,
                "status": "created",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
    finally:
        conn.close()

@app.get("/orders")
async def get_orders(user_id: Optional[str] = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_id:
                cur.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            else:
                cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
            orders = cur.fetchall()
            return {"orders": orders, "count": len(orders)}
    finally:
        conn.close()

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cur.fetchone()
            if order:
                return {"order": order}
            raise HTTPException(status_code=404, detail="Order not found")
    finally:
        conn.close()

@app.put("/orders/{order_id}/status")
async def update_order_status(order_id: int, status_update: OrderStatus):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status_update.status, order_id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")
            conn.commit()
            return {"message": f"Order {order_id} status updated to {status_update.status}"}
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "order-service",
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        conn = get_db_connection()
        conn.close()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = "disconnected"
    return health_status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
