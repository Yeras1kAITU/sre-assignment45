from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Service")

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

class PaymentRequest(BaseModel):
    order_id: int
    amount: float
    payment_method: str = "credit_card"

class PaymentResponse(BaseModel):
    payment_id: int
    order_id: int
    amount: float
    status: str
    transaction_id: str

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

@app.get("/")
async def root():
    return {"service": "Payment Service", "status": "healthy", "version": "1.0.0"}

@app.post("/payments")
async def process_payment(payment: PaymentRequest):
    conn = get_db_connection()
    try:
        # Simulate payment processing (90% success rate)
        success = random.random() < 0.9
        status = "completed" if success else "failed"
        transaction_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}"

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO payments (order_id, amount, payment_method, status, transaction_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (payment.order_id, payment.amount, payment.payment_method, status, transaction_id)
            )
            payment_id = cur.fetchone()['id']
            conn.commit()

            logger.info(f"Payment processed: {payment_id} - {status}")
            return {
                "payment_id": payment_id,
                "order_id": payment.order_id,
                "amount": payment.amount,
                "status": status,
                "transaction_id": transaction_id
            }
    except Exception as e:
        conn.rollback()
        logger.error(f"Payment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")
    finally:
        conn.close()

@app.get("/payments")
async def get_payments(order_id: Optional[int] = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if order_id:
                cur.execute("SELECT * FROM payments WHERE order_id = %s ORDER BY created_at DESC", (order_id,))
            else:
                cur.execute("SELECT * FROM payments ORDER BY created_at DESC")
            payments = cur.fetchall()
            return {"payments": payments, "count": len(payments)}
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "payment-service",
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        conn = get_db_connection()
        conn.close()
        health_status["database"] = "connected"
    except:
        health_status["status"] = "degraded"
        health_status["database"] = "disconnected"
    return health_status

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)