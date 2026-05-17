from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Product Service")

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

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str
    created_at: Optional[datetime]

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

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Product Service...")

@app.get("/")
async def root():
    return {
        "service": "Product Service",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/products")
async def get_products(category: Optional[str] = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if category:
                cur.execute("SELECT * FROM products WHERE category = %s", (category,))
            else:
                cur.execute("SELECT * FROM products ORDER BY created_at DESC")
            products = cur.fetchall()
            return {"products": products, "count": len(products)}
    finally:
        conn.close()

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cur.fetchone()
            if product:
                return {"product": product}
            raise HTTPException(status_code=404, detail="Product not found")
    finally:
        conn.close()

@app.post("/products")
async def create_product(product: ProductCreate):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO products (name, description, price, stock, category) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (product.name, product.description, product.price, product.stock, product.category)
            )
            product_id = cur.fetchone()['id']
            conn.commit()
            return {"id": product_id, "message": "Product created successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")
    finally:
        conn.close()

@app.put("/products/{product_id}")
async def update_product(product_id: int, product: ProductCreate):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET name=%s, description=%s, price=%s, stock=%s, category=%s WHERE id=%s",
                (product.name, product.description, product.price, product.stock, product.category, product_id)
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")
            conn.commit()
            return {"message": "Product updated successfully"}
    finally:
        conn.close()

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")
            conn.commit()
            return {"message": "Product deleted successfully"}
    finally:
        conn.close()

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "service": "product-service",
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")