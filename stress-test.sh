#!/bin/bash
echo "========================================="
echo "  CPU Stress Test - Order Service"
echo "========================================="
echo ""

echo "Pre-test metrics:"
echo "---"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -E "NAME|order-service"
echo ""

echo "Running CPU stress on Order Service..."
echo "Duration: 20 seconds"
echo ""

START_TIME=$(date +%s)
END_TIME=$((START_TIME + 20))
REQUESTS=0

while [ $(date +%s) -lt $END_TIME ]; do
    for i in $(seq 1 5); do
        curl -s -o /dev/null -X POST http://localhost/api/orders/orders \
            -H "Content-Type: application/json" \
            -d '{"user_id":"stress_test","items":[{"product_id":1,"quantity":1,"price":0}],"total_amount":0}' &
    done
    REQUESTS=$((REQUESTS+5))
    sleep 0.1
done
wait

echo ""
echo "Post-test metrics:"
echo "---"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -E "NAME|order-service"

echo ""
echo "Total requests sent: $REQUESTS"
echo "Requests per second: ~$((REQUESTS / 20))"
echo ""
echo "========================================="
echo "  Stress Test Complete"
echo "========================================="
