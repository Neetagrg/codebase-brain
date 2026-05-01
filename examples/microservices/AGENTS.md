# Microservices Platform - Agent Knowledge Base

## 🎯 Project Overview
**Domain**: Distributed Systems (Node.js + Kubernetes)  
**Type**: Event-driven microservices architecture  
**Scale**: 12 services, ~80K LOC, 500K requests/day  
**Team Size**: 15 engineers across 4 teams

## 📁 Architecture Map

```
services/
├── api-gateway/           # Kong API Gateway
│   ├── routes/
│   └── plugins/
├── auth-service/          # Authentication & Authorization
│   ├── src/controllers/
│   ├── src/middleware/
│   └── src/models/
├── user-service/          # User management
├── order-service/         # Order processing
├── payment-service/       # Payment handling
├── inventory-service/     # Inventory tracking
├── notification-service/  # Email/SMS notifications
└── analytics-service/     # Real-time analytics

shared/
├── proto/                 # gRPC protocol definitions
├── events/                # Event schemas (AsyncAPI)
└── libraries/             # Shared npm packages

infrastructure/
├── k8s/                   # Kubernetes manifests
├── terraform/             # Infrastructure as Code
└── monitoring/            # Observability configs
```

## 🔑 Core Systems

### 1. Service Communication
- **Sync**: gRPC for service-to-service calls
- **Async**: RabbitMQ for event-driven flows
- **API Gateway**: Kong (rate limiting, auth, routing)
- **Service Mesh**: Istio for traffic management
- **Circuit Breaker**: Resilience4j patterns

### 2. Data Management
- **Pattern**: Database per service
- **Auth Service**: PostgreSQL (user credentials)
- **Order Service**: MongoDB (order documents)
- **Inventory Service**: Redis (real-time stock)
- **Analytics Service**: TimescaleDB (time-series)
- **Event Store**: Kafka (event sourcing)

### 3. Observability Stack
- **Metrics**: Prometheus + Grafana
- **Tracing**: Jaeger (OpenTelemetry)
- **Logging**: Fluentd → Elasticsearch → Kibana
- **APM**: New Relic for application monitoring
- **Alerting**: AlertManager → PagerDuty

### 4. Deployment Pipeline
- **CI/CD**: GitHub Actions
- **Container Registry**: AWS ECR
- **Orchestration**: Kubernetes (EKS)
- **GitOps**: ArgoCD for deployments
- **Canary Releases**: Flagger + Istio

## 🛠️ Slash Commands

### /trace-request
**Purpose**: Trace request across microservices  
**Usage**: Debug slow or failed requests  
**Traces**:
1. API Gateway entry point
2. Service-to-service hops
3. Database queries per service
4. External API calls
5. Total latency breakdown

**Example**:
```bash
/trace-request trace-id:abc123
# Output:
# api-gateway → auth-service (15ms)
# api-gateway → order-service (45ms)
#   order-service → inventory-service (30ms)
#   order-service → payment-service (120ms) ← SLOW
# Total: 210ms
```

### /check-circuit-breaker
**Purpose**: Monitor circuit breaker states  
**Usage**: When seeing cascading failures  
**Checks**:
1. Open/closed/half-open states
2. Failure rate thresholds
3. Timeout configurations
4. Fallback behavior

**Example**:
```bash
/check-circuit-breaker payment-service
# Status: OPEN (last 5 min)
# Failures: 45/50 requests
# Cause: Stripe API timeout (30s)
# Fallback: Queue for retry
# Recovery: Auto-retry in 2 min
```

### /analyze-event-flow
**Purpose**: Debug event-driven workflows  
**Usage**: When events not processing correctly  
**Analyzes**:
1. Event publication success
2. Queue depths and lag
3. Consumer processing rates
4. Dead letter queue contents
5. Event ordering issues

**Example**:
```bash
/analyze-event-flow order.created
# Published: 1,250 events/hour
# Consumers: 3 services subscribed
# Lag: inventory-service 45 messages behind
# DLQ: 3 failed events (schema validation)
# Action: Scale inventory-service pods
```

### /validate-service-mesh
**Purpose**: Check service mesh configuration  
**Usage**: Before production deployment  
**Validates**:
1. mTLS between services
2. Traffic routing rules
3. Retry and timeout policies
4. Rate limiting configs
5. Fault injection tests

**Example**:
```bash
/validate-service-mesh order-service
# mTLS: ✓ Enabled (strict mode)
# Retries: ✓ 3 attempts, exponential backoff
# Timeout: ✓ 5s per request
# Rate Limit: ✓ 1000 req/min
# Canary: ✗ Missing weight configuration
```

## 🧩 Service Patterns

### API Gateway Pattern
```javascript
// services/api-gateway/routes/orders.js
module.exports = {
  path: '/api/orders',
  methods: ['GET', 'POST'],
  upstream: 'order-service:3000',
  plugins: ['auth', 'rate-limit', 'cors'],
  rateLimit: { requests: 100, window: 60 }
}
```

### Event Publishing Pattern
```javascript
// services/order-service/src/events/publisher.js
async function publishOrderCreated(order) {
  const event = {
    type: 'order.created',
    version: '1.0',
    data: order,
    metadata: { timestamp: Date.now(), correlationId }
  }
  await rabbitMQ.publish('orders', event)
  await kafka.send('order-events', event) // Dual write
}
```

### Circuit Breaker Pattern
```javascript
// services/order-service/src/clients/payment-client.js
const breaker = new CircuitBreaker(paymentAPI.charge, {
  timeout: 5000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
  fallback: () => ({ status: 'queued' })
})
```

### Saga Pattern (Distributed Transaction)
```javascript
// services/order-service/src/sagas/order-saga.js
async function processOrder(order) {
  try {
    await reserveInventory(order)
    await chargePayment(order)
    await confirmOrder(order)
  } catch (error) {
    await compensate(order) // Rollback
    throw error
  }
}
```

## 📊 Service Communication Flow

### Synchronous Flow (gRPC)
1. **Client**: API Gateway receives HTTP request
2. **Auth**: gRPC call to auth-service (validate token)
3. **Business Logic**: gRPC call to order-service
4. **Data Fetch**: gRPC call to inventory-service
5. **Response**: Aggregate and return to client

### Asynchronous Flow (Events)
1. **Publish**: order-service publishes `order.created`
2. **Fanout**: RabbitMQ routes to multiple queues
3. **Consume**: 
   - inventory-service reserves stock
   - notification-service sends email
   - analytics-service updates metrics
4. **Completion**: Each service publishes completion event

## 🔍 Common Issues & Solutions

### Issue: Service discovery failing
**Location**: `services/order-service/src/config/grpc.js`  
**Cause**: Kubernetes DNS not resolving service names  
**Fix**: Use full DNS name `inventory-service.default.svc.cluster.local`

### Issue: Event processing lag
**Location**: `services/notification-service/src/consumers/`  
**Cause**: Single consumer, high message volume  
**Fix**: Scale to 3 replicas, partition by customer_id

### Issue: Cascading failures
**Location**: `services/payment-service/src/controllers/`  
**Cause**: No circuit breaker on Stripe API calls  
**Fix**: Implement circuit breaker with fallback queue

### Issue: Inconsistent data across services
**Location**: Event-driven flows  
**Cause**: Missing idempotency keys  
**Fix**: Add unique event IDs, implement deduplication

## 🚀 Performance Metrics

- **Request Latency**: p50: 45ms, p95: 180ms, p99: 500ms
- **Throughput**: 500K requests/day (avg 6 req/sec)
- **Availability**: 99.95% uptime (SLA: 99.9%)
- **Error Rate**: < 0.1% (excluding client errors)
- **Event Processing**: < 100ms lag (p95)

## 🔐 Security Architecture

- ✅ mTLS between all services (Istio)
- ✅ JWT authentication (RS256)
- ✅ API Gateway rate limiting
- ✅ Network policies (Kubernetes)
- ✅ Secrets management (Vault)
- ✅ Container scanning (Trivy)
- ✅ RBAC for service accounts

## 📚 Key Dependencies

```json
{
  "express": "4.18.0",
  "@grpc/grpc-js": "1.9.0",
  "amqplib": "0.10.0",
  "kafkajs": "2.2.0",
  "ioredis": "5.3.0",
  "mongoose": "7.5.0",
  "pg": "8.11.0",
  "@opentelemetry/api": "1.6.0",
  "prom-client": "15.0.0"
}
```

## 🎓 Onboarding Guide

### Day 1: Local Development
1. Install Docker Desktop + Kubernetes
2. Clone all service repositories
3. Run `docker-compose up` for local stack
4. Test API Gateway at `localhost:8000`

### Week 1: Service Architecture
- Understand service boundaries
- Learn gRPC vs REST trade-offs
- Study event-driven patterns
- Review observability dashboards

### Month 1: Service Development
- Build new microservice from template
- Implement gRPC endpoints
- Add event publishers/consumers
- Deploy to staging cluster

## 📈 Monitoring Dashboard

### Service Health
- **CPU Usage**: Target < 70%
- **Memory Usage**: Target < 80%
- **Pod Restarts**: Alert if > 3/hour
- **Request Rate**: Monitor for spikes
- **Error Rate**: Alert if > 1%

### Business Metrics
- **Orders/minute**: Track trends
- **Payment Success Rate**: Target > 99%
- **Inventory Accuracy**: Target 100%
- **Notification Delivery**: Target > 98%

---

**Last Updated**: 2026-05-01  
**Maintained By**: Platform Team  
**Questions?**: #microservices-help on Slack