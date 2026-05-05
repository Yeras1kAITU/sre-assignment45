#!/bin/bash
echo "========================================="
echo "  Automated Log Analysis"
echo "========================================="
echo ""

# Pattern 1: Database connection failures
echo "[1] Checking for database connection failures..."
docker logs order-service 2>&1 | grep -i "database connection failed\|could not translate host\|psycopg2.OperationalError" | tail -5
if [ $? -eq 0 ]; then
    echo "  Database connection issues detected!"
else
    echo "  No database connection issues found"
fi

# Pattern 2: Service restart loops
echo ""
echo "[2] Checking for restart loops..."
for container in auth-service product-service order-service user-service chat-service; do
    RESTARTS=$(docker inspect $container --format='{{.RestartCount}}' 2>/dev/null)
    if [ "$RESTARTS" -gt 3 ] 2>/dev/null; then
        echo "  $container: $RESTARTS restarts (possible loop)"
    elif [ -n "$RESTARTS" ]; then
        echo "  $container: $RESTARTS restarts"
    else
        echo "   $container: not running"
    fi
done

# Pattern 3: Health check failures
echo ""
echo "[3] Checking health endpoint status..."
for port in 8000 8001 8002 8003 8004; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo "  Port $port: healthy (HTTP $STATUS)"
    else
        echo "   Port $port: unhealthy (HTTP $STATUS)"
    fi
done

# Pattern 4: Error rate summary
echo ""
echo "[4] Recent errors from container logs..."
for container in auth-service product-service order-service user-service; do
    ERRORS=$(docker logs $container --since 5m 2>&1 | grep -ci "error\|exception\|traceback")
    echo "  $container: $ERRORS errors in last 5 minutes"
done

# Pattern 5: Resource usage
echo ""
echo "[5] Container resource usage..."
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -10

echo ""
echo "========================================="
echo "  Log analysis complete"
echo "========================================="
