# Capacity Planning Analysis

## Resource Utilization Summary

### Current System State

| Service | CPU Avg | CPU Peak | Memory Avg | Memory Peak | Replicas |
|---------|---------|----------|------------|-------------|----------|
| auth-service | 15% | 35% | 128MB | 256MB | 1 |
| product-service | 20% | 45% | 256MB | 512MB | 1 |
| order-service | 35% | 70% | 512MB | 1024MB | 2 |
| payment-service | 25% | 55% | 384MB | 768MB | 1 |
| user-service | 10% | 25% | 128MB | 256MB | 1 |
| notification-service | 8% | 20% | 64MB | 128MB | 1 |
| postgres | 40% | 80% | 1024MB | 2048MB | 1 |
| redis | 5% | 15% | 128MB | 256MB | 1 |

### Bottleneck Identification

1. **Primary Bottleneck:** PostgreSQL database (40% average CPU, 80% peak)
2. **Secondary Bottleneck:** Order Service (70% peak CPU during high load)
3. **Third Bottleneck:** Payment Service (55% peak CPU)

## Load Testing Results

### Test Scenario 1: Normal Load (100 requests/second)

| Service | Response Time (P95) | Error Rate | CPU Usage |
|---------|--------------------|------------|-----------|
| auth-service | 45ms | 0.01% | 15% |
| product-service | 35ms | 0.00% | 20% |
| order-service | 120ms | 0.05% | 35% |
| payment-service | 95ms | 0.02% | 25% |
| user-service | 25ms | 0.00% | 10% |
| notification-service | 15ms | 0.00% | 8% |

### Test Scenario 2: Peak Load (500 requests/second)

| Service | Response Time (P95) | Error Rate | CPU Usage |
|---------|--------------------|------------|-----------|
| auth-service | 120ms | 0.15% | 45% |
| product-service | 95ms | 0.10% | 55% |
| order-service | 450ms | 1.20% | 85% |
| payment-service | 280ms | 0.80% | 70% |
| user-service | 65ms | 0.05% | 25% |
| notification-service | 35ms | 0.02% | 15% |

### Test Scenario 3: Saturation Load (1000 requests/second)

| Service | Response Time (P95) | Error Rate | CPU Usage |
|---------|--------------------|------------|-----------|
| auth-service | 350ms | 0.85% | 85% |
| product-service | 280ms | 0.60% | 90% |
| order-service | 1200ms | 4.50% | 98% |
| payment-service | 750ms | 2.80% | 95% |
| user-service | 180ms | 0.40% | 55% |
| notification-service | 85ms | 0.15% | 35% |

## Scaling Recommendations

### Horizontal Scaling

| Service | Current Replicas | Recommended Replicas | Threshold |
|---------|-----------------|----------------------|-----------|
| order-service | 2 | 4 | CPU > 60% for 2 minutes |
| payment-service | 1 | 3 | CPU > 50% for 2 minutes |
| product-service | 1 | 2 | CPU > 60% for 3 minutes |
| auth-service | 1 | 2 | CPU > 50% for 3 minutes |
| postgres | 1 | 1 (read replicas) | Read replica at 40% CPU |
| notification-service | 1 | 1 | Remains low utilization |

### Vertical Scaling

| Service | Current | Recommended | Justification |
|---------|---------|-------------|---------------|
| order-service | 512MB RAM | 1024MB RAM | Memory pressure during peak |
| payment-service | 384MB RAM | 768MB RAM | Transaction processing |
| postgres | 1 vCPU, 1GB | 2 vCPU, 2GB | Database bottleneck |
| order-service CPU | 0.5 vCPU | 1 vCPU | CPU saturation at peak |

## Auto-scaling Configuration

### Kubernetes HPA for Order Service

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-service-hpa
  namespace: microservices
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70