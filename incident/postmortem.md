# Postmortem Report: Order Service Database Connection Failure

## Incident Summary

**Incident ID:** INC-2026-001

**Date:** 2026-05-17

**Duration:** 14:30 UTC to 15:15 UTC (45 minutes)

**Impact:** Complete Order Service outage affecting order creation, retrieval, and status updates. Approximately 150 failed order attempts. Payment and notification services partially degraded due to dependency on order data.

**Severity:** HIGH

**Root Cause:** Incorrect PostgreSQL connection string in Order Service environment variables after configuration update.

## Timeline

- 14:30: Prometheus alert "OrderServiceDown" triggered
- 14:32: On-call engineer acknowledged alert
- 14:35: Grafana dashboard confirmed Order Service HTTP 503 responses
- 14:40: Log analysis showed "Database connection failed" errors
- 14:45: Database verification confirmed PostgreSQL running normally
- 14:50: Configuration check revealed incorrect DB_HOST value
- 14:55: Environment variable corrected in deployment
- 15:00: Order Service restarted and health check passed
- 15:05: All systems verified operational
- 15:15: Incident closed, monitoring confirmed stability

## Root Cause Analysis

The Order Service deployment configuration was updated at 14:15 UTC to add Redis connection parameters. During this update, the DB_HOST environment variable was accidentally changed from "postgres" to "postgres-db". This caused all database connection attempts to fail with timeout errors.

The Order Service health check correctly detected the failure after 3 consecutive failures, marking the service as unhealthy. Kubernetes liveness probe triggered container restart every 15 seconds, creating a crash loop that prevented automatic recovery.

## Impact Assessment

**Failed Operations:**
- 150 order creation attempts failed
- 500 health check failures recorded
- 50 payment processing attempts delayed

**User Impact:**
- Frontend users saw "Order Service unavailable" messages
- Order history page displayed errors
- Checkout process completely blocked

**Business Impact:**
- Estimated 15% of daily orders lost
- Customer support received 25 related tickets

## Action Items

| Item | Action | Owner | Due Date | Status |
|------|--------|-------|----------|--------|
| 1 | Implement configuration validation pre-deployment | Platform Team | 2024-05-20 | Pending |
| 2 | Add ConfigMap for environment variables | SRE Team | 2024-05-18 | Pending |
| 3 | Create ConfigMap validation webhook | Platform Team | 2024-05-25 | Pending |
| 4 | Document environment variable naming convention | All Teams | 2024-05-17 | Pending |
| 5 | Implement canary deployments for config changes | SRE Team | 2024-05-30 | Pending |
| 6 | Add database connection retry with backoff | Dev Team | 2024-05-22 | Pending |

## Prevention Measures

1. **Configuration Validation:** Implement schema validation for all environment variables before deployment

2. **Separation of Concerns:** Use Kubernetes ConfigMaps to centralize configuration management

3. **Canary Deployments:** Route 10% traffic to new configuration before full rollout

4. **Database Connection Pooling:** Implement retry logic with exponential backoff

5. **Automated Testing:** Add integration tests that verify database connectivity in CI pipeline

## Lessons Learned

**What Went Well:**
- Monitoring detected the issue within 2 minutes
- On-call engineer responded immediately
- Rollback procedure was documented and followed

**What Went Wrong:**
- No validation prevented incorrect configuration
- Crash loop prevented manual debugging
- No staging environment for configuration testing

**Where We Got Lucky:**
- Incident occurred during low traffic period
- Database remained available for other services
- No data corruption occurred

## Metrics After Resolution

- Order Service availability restored to 99.95%
- Order creation latency: 45ms P95
- Error rate: 0.05%
- Customer satisfaction restored to baseline
