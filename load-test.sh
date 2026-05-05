#!/bin/bash

echo "========================================="
echo "  Capacity Planning Load Test"
echo "========================================="
echo ""

DURATION=30
CONCURRENT=10
TARGET="http://localhost"

echo "Test Parameters:"
echo "  Duration: ${DURATION}s"
echo "  Concurrent users: $CONCURRENT"
echo "  Target: $TARGET"
echo ""

# Function to simulate a user session
simulate_user() {
    local USER_ID=$1
    local START_TIME=$(date +%s)
    local END_TIME=$((START_TIME + DURATION))
    local REQUESTS=0
    local ERRORS=0
    
    while [ $(date +%s) -lt $END_TIME ]; do
        # Browse products
        curl -s -o /dev/null -w "%{http_code}" $TARGET/api/products/products > /dev/null 2>&1
        if [ $? -ne 0 ]; then ERRORS=$((ERRORS+1)); fi
        REQUESTS=$((REQUESTS+1))

        curl -s -o /dev/null -X POST $TARGET/api/orders/orders \
            -H "Content-Type: application/json" \
            -d "{\"user_id\":\"load_test_$USER_ID\",\"items\":[{\"product_id\":1,\"quantity\":1,\"price\":0}],\"total_amount\":0}" > /dev/null 2>&1
        if [ $? -ne 0 ]; then ERRORS=$((ERRORS+1)); fi
        REQUESTS=$((REQUESTS+1))

        curl -s -o /dev/null $TARGET/api/products/health > /dev/null 2>&1
        REQUESTS=$((REQUESTS+1))
        
        sleep 0.5
    done
    
    echo "User $USER_ID: $REQUESTS requests, $ERRORS errors"
}

echo "Starting load test with $CONCURRENT concurrent users..."
echo ""

# Launch concurrent users
for i in $(seq 1 $CONCURRENT); do
    simulate_user $i &
done

wait

echo ""
echo "========================================="
echo "  Load Test Complete"
echo "========================================="

# Collect metrics after test
echo ""
echo "Post-test system metrics:"
echo ""

# CPU and Memory from Docker stats
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | head -10

echo ""
echo "Request metrics from Prometheus:"
curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total[1m])" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['status'] == 'success':
    for result in data['data']['result']:
        print(f\"  {result['metric'].get('job','unknown')}: {float(result['value'][1]):.2f} req/s\")
" 2>/dev/null

echo ""
echo "Error rate:"
curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[1m])" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['status'] == 'success':
    for result in data['data']['result']:
        print(f\"  {result['metric'].get('job','unknown')}: {float(result['value'][1]):.2f} errors/s\")
" 2>/dev/null
