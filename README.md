## Setup Instructions

### Prerequisites
- Docker & Docker Compose v2+
- Python 3.9+ (for local development only)
- Terraform 1.0+ (for cloud deployment only)
- AWS CLI (for cloud deployment only)
---

## 1. Clone the Repository

```bash
git clone https://github.com/Yeras1kAITU/sre-assignment45.git
cd sre-assignment45
```

---

## 2. Local Deployment (Docker Compose)

```bash
# Build and start all services
docker-compose up -d --build

# Wait 30 seconds for services to initialize
# Check container status
docker-compose ps
```

All 9 containers should show **STATUS: Up**.

---

## 3. Access the Application

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |

---

## 4. Verify Services

```bash
# Health checks
curl http://localhost:8000/health   # Auth Service
curl http://localhost:8001/health   # Product Service
curl http://localhost:8002/health   # Order Service
curl http://localhost:8003/health   # User Service
curl http://localhost:8004/health   # Chat Service

# Product data
curl http://localhost:8001/products

# Order list
curl http://localhost:8002/orders
```

---

## 5. Cloud Deployment (AWS via Terraform)

```bash
cd terraform

# Initialize
terraform init

# Preview resources
terraform plan

# Deploy (takes ~3 minutes)
terraform apply

# Get public IP
terraform output instance_public_ip
```

Access the app at `http://<PUBLIC_IP>`.

---

## 6. Stop & Cleanup

```bash
# Stop local containers
docker-compose down

# Destroy AWS infrastructure
cd terraform
terraform destroy
```

---

##Project Structure

```
services/          # 5 microservices (auth, product, order, user, chat)
frontend/          # HTML/CSS/JS web interface
nginx/             # Reverse proxy configuration
database/          # PostgreSQL init script
monitoring/        # Prometheus & Grafana configs
terraform/         # AWS infrastructure code
docker-compose.yml # Container orchestration
```