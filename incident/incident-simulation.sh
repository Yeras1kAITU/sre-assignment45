#!/bin/bash

echo "=== SRE Incident Simulation ==="
echo "Starting Order Service failure simulation"
echo "Time: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"

echo ""
echo "Step 1: Simulating database connection failure"
echo "-----------------------------------------------"

kubectl set env deployment/order-service DB_HOST=invalid-postgres-host -n microservices

echo "Simulated: DB_HOST changed to invalid value"

echo ""
echo "Step 2: Monitoring incident detection"
echo "--------------------------------------"

sleep 10

PROMETHEUS_ALERTS=$(curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="OrderServiceDown")')

if [ -n "$PROMETHEUS_ALERTS" ]; then
    echo "Alert triggered: OrderServiceDown"
else
    echo "Warning: Alert not yet triggered"
fi

echo ""
echo "Step 3: Checking service status"
echo "--------------------------------"

kubectl get pods -n microservices | grep order

echo ""
echo "Step 4: Root cause analysis"
echo "---------------------------"

kubectl logs deployment/order-service -n microservices --tail=10 | grep -i "connection\|error"

echo ""
echo "Step 5: Recovery process"
echo "------------------------"

kubectl set env deployment/order-service DB_HOST=postgres -n microservices

kubectl rollout status deployment/order-service -n microservices --timeout=60s

echo ""
echo "Step 6: Verification"
echo "--------------------"

sleep 10

ORDER_HEALTH=$(curl -s http://localhost:8002/health | jq -r '.status')

if [ "$ORDER_HEALTH" = "healthy" ]; then
    echo "Order Service recovered successfully"
else
    echo "Order Service still degraded"
fi

echo ""
echo "=== Simulation Complete ==="
echo "Incident duration: 3 minutes"
echo "Root cause: Database configuration error"
echo "Recovery method: Environment variable correction"