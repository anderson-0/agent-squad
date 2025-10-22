# NATS Infrastructure Setup Guide

**Complete guide to deploying and managing NATS for Agent Squad**

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Setup](#docker-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Provider Options](#cloud-provider-options)
5. [Monitoring & Operations](#monitoring--operations)
6. [Backup & Recovery](#backup--recovery)
7. [Security](#security)
8. [Scaling & High Availability](#scaling--high-availability)

---

## Local Development Setup

### What You Already Have

You already have NATS running! The setup script downloaded and started it:

```bash
# NATS server location
./nats/nats-server-v2.10.7-darwin-arm64/nats-server

# Data storage
./nats-data/jetstream/

# Server log
./nats-server.log
```

### Starting NATS Locally (Manual)

If you need to restart NATS:

```bash
# Start NATS with JetStream
./nats/nats-server-v2.10.7-darwin-arm64/nats-server \
  -js \
  -p 4222 \
  --store_dir ./nats-data \
  --log_file nats-server.log

# Or start in foreground (see logs in terminal)
./nats/nats-server-v2.10.7-darwin-arm64/nats-server \
  -js \
  -p 4222 \
  --store_dir ./nats-data
```

**Ports**:
- `4222` - Client connections
- `8222` - HTTP monitoring (optional)

### Installing NATS Permanently (macOS)

```bash
# Using Homebrew
brew install nats-server

# Start NATS
nats-server -js -p 4222 --store_dir ./nats-data

# Or run as background service
brew services start nats-server
```

### Installing NATS on Linux

```bash
# Ubuntu/Debian
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo mv nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/

# Start NATS
nats-server -js -p 4222 --store_dir /var/lib/nats
```

### Installing NATS on Windows

```powershell
# Download from GitHub releases
# https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-windows-amd64.zip

# Extract and run
.\nats-server.exe -js -p 4222 --store_dir .\nats-data
```

### NATS CLI Tools (Optional but Useful)

```bash
# macOS
brew install nats-io/nats-tools/nats

# Linux
curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh

# Verify installation
nats --version

# Connect to your local NATS
nats context save local --server nats://localhost:4222

# Check server info
nats server info

# Check streams
nats stream ls
nats stream info agent-messages

# Monitor messages
nats stream view agent-messages
```

---

## Docker Setup

### Option 1: Docker Compose (Recommended for Development)

Create `docker-compose.nats.yml`:

```yaml
version: '3.8'

services:
  nats:
    image: nats:2.10.7-alpine
    container_name: agent-squad-nats
    ports:
      - "4222:4222"    # Client connections
      - "8222:8222"    # HTTP monitoring
      - "6222:6222"    # Cluster routing (for HA)
    command: >
      -js
      -m 8222
      --store_dir /data
      --max_mem_store 1GB
      --max_file_store 10GB
    volumes:
      - nats-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8222/healthz"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - agent-squad-network

  # Your existing services
  postgres:
    # ... existing postgres config ...
    networks:
      - agent-squad-network

  redis:
    # ... existing redis config ...
    networks:
      - agent-squad-network

  backend:
    # ... existing backend config ...
    environment:
      - MESSAGE_BUS=nats
      - NATS_URL=nats://nats:4222
      # ... other env vars ...
    depends_on:
      - nats
      - postgres
      - redis
    networks:
      - agent-squad-network

volumes:
  nats-data:

networks:
  agent-squad-network:
    driver: bridge
```

**Start everything**:
```bash
docker-compose -f docker-compose.nats.yml up -d

# Check NATS is running
docker logs agent-squad-nats

# Monitor NATS
curl http://localhost:8222/varz

# Stop
docker-compose -f docker-compose.nats.yml down
```

### Option 2: Standalone NATS Container

```bash
# Create volume for persistence
docker volume create nats-data

# Run NATS
docker run -d \
  --name nats \
  -p 4222:4222 \
  -p 8222:8222 \
  -v nats-data:/data \
  nats:2.10.7-alpine \
  -js \
  -m 8222 \
  --store_dir /data \
  --max_mem_store 1GB \
  --max_file_store 10GB

# Check logs
docker logs -f nats

# Stop
docker stop nats
docker rm nats
```

### Option 3: Full Docker Compose with App

Update your existing `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Add NATS service
  nats:
    image: nats:2.10.7-alpine
    container_name: nats
    ports:
      - "4222:4222"
      - "8222:8222"
    command: >
      -js
      -m 8222
      --store_dir /data
      --max_mem_store ${NATS_MAX_MEMORY:-1GB}
      --max_file_store ${NATS_MAX_STORAGE:-10GB}
    volumes:
      - nats-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8222/healthz"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Update backend service
  backend:
    # ... existing config ...
    environment:
      MESSAGE_BUS: ${MESSAGE_BUS:-memory}
      NATS_URL: ${NATS_URL:-nats://nats:4222}
      NATS_STREAM_NAME: ${NATS_STREAM_NAME:-agent-messages}
      NATS_MAX_MSGS: ${NATS_MAX_MSGS:-1000000}
      NATS_MAX_AGE_DAYS: ${NATS_MAX_AGE_DAYS:-7}
    depends_on:
      - nats
      - postgres
      - redis

volumes:
  nats-data:
```

**Environment Variables** (add to `.env`):
```bash
MESSAGE_BUS=nats
NATS_URL=nats://nats:4222
NATS_STREAM_NAME=agent-messages
NATS_MAX_MSGS=1000000
NATS_MAX_AGE_DAYS=7
NATS_MAX_MEMORY=1GB
NATS_MAX_STORAGE=10GB
```

---

## Production Deployment

### Requirements

For production, you need:
1. **Persistent storage** - For JetStream data
2. **Memory** - At least 1GB for NATS (2GB recommended)
3. **Network** - Low latency between NATS and app servers
4. **Monitoring** - Prometheus/Grafana for metrics

### Production NATS Configuration

Create `nats-server.conf`:

```conf
# Basic Settings
port: 4222
server_name: agent-squad-nats-1

# HTTP Monitoring
http_port: 8222

# Logging
log_file: "/var/log/nats/nats-server.log"
log_size_limit: 100MB
max_traced_msg_len: 1024

# Limits
max_connections: 64000
max_control_line: 4096
max_payload: 1048576  # 1MB
max_pending: 268435456  # 256MB

# JetStream
jetstream {
  store_dir: "/data/jetstream"

  # Storage limits
  max_memory_store: 2GB
  max_file_store: 50GB

  # Domain (optional, for multi-region)
  # domain: "us-east-1"
}

# Clustering (for HA - see below)
# cluster {
#   name: agent-squad-cluster
#   listen: 0.0.0.0:6222
#   routes: [
#     nats://nats-1:6222
#     nats://nats-2:6222
#     nats://nats-3:6222
#   ]
# }

# Security
# authorization {
#   users = [
#     {
#       user: "agent-squad-app"
#       password: "$2a$11$your-bcrypt-password-hash"
#       permissions: {
#         publish: ["agent.>"]
#         subscribe: ["agent.>"]
#       }
#     }
#   ]
# }
```

**Start NATS in production**:
```bash
nats-server -c nats-server.conf
```

### Systemd Service (Linux Production)

Create `/etc/systemd/system/nats-server.service`:

```ini
[Unit]
Description=NATS Server
After=network.target

[Service]
Type=simple
User=nats
Group=nats
ExecStart=/usr/local/bin/nats-server -c /etc/nats/nats-server.conf
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure
RestartSec=5s
LimitNOFILE=65536

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/data/jetstream /var/log/nats

[Install]
WantedBy=multi-user.target
```

**Setup**:
```bash
# Create nats user
sudo useradd -r -s /bin/false nats

# Create directories
sudo mkdir -p /data/jetstream /var/log/nats /etc/nats
sudo chown -R nats:nats /data/jetstream /var/log/nats

# Copy config
sudo cp nats-server.conf /etc/nats/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable nats-server
sudo systemctl start nats-server

# Check status
sudo systemctl status nats-server

# View logs
sudo journalctl -u nats-server -f
```

---

## Cloud Provider Options

### AWS (Recommended for Production)

**Option A: EC2 Instance**

1. **Launch EC2 Instance**:
   - Instance type: `t3.medium` (2 vCPU, 4GB RAM) - $30/month
   - Storage: 50GB EBS volume for JetStream
   - Security group: Open ports 4222, 8222, 6222
   - AMI: Ubuntu 22.04 LTS

2. **Install NATS**:
```bash
# SSH into instance
ssh ubuntu@your-ec2-ip

# Install NATS
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo mv nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/

# Create systemd service (see above)
# Start NATS
sudo systemctl start nats-server
```

3. **Configure App Servers**:
```bash
# In your app's .env
NATS_URL=nats://10.0.1.50:4222  # Private IP of EC2
```

**Option B: ECS/Fargate (Container-based)**

Create `task-definition.json`:

```json
{
  "family": "agent-squad-nats",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "nats",
      "image": "nats:2.10.7-alpine",
      "portMappings": [
        {"containerPort": 4222, "protocol": "tcp"},
        {"containerPort": 8222, "protocol": "tcp"}
      ],
      "command": [
        "-js",
        "-m", "8222",
        "--store_dir", "/data",
        "--max_mem_store", "1GB",
        "--max_file_store", "10GB"
      ],
      "mountPoints": [
        {
          "sourceVolume": "nats-data",
          "containerPath": "/data"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/nats",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "nats"
        }
      }
    }
  ],
  "volumes": [
    {
      "name": "nats-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-xxxxxxxxx"
      }
    }
  ]
}
```

**Option C: AWS Marketplace NATS**

AWS offers managed NATS via marketplace partners like Synadia.

### Google Cloud Platform (GCP)

**Compute Engine Instance**:

```bash
# Create instance
gcloud compute instances create nats-server \
  --machine-type=e2-medium \
  --boot-disk-size=50GB \
  --tags=nats-server

# Allow firewall
gcloud compute firewall-rules create allow-nats \
  --allow=tcp:4222,tcp:8222,tcp:6222 \
  --target-tags=nats-server

# SSH and install NATS
gcloud compute ssh nats-server
# ... install steps same as above ...
```

**Google Kubernetes Engine (GKE)** - See Kubernetes section below

### Azure

**Virtual Machine**:

```bash
# Create VM
az vm create \
  --resource-group agent-squad \
  --name nats-server \
  --image UbuntuLTS \
  --size Standard_B2s \
  --admin-username azureuser

# Open ports
az vm open-port --port 4222 --resource-group agent-squad --name nats-server
az vm open-port --port 8222 --resource-group agent-squad --name nats-server

# SSH and install
ssh azureuser@your-vm-ip
# ... install steps ...
```

### DigitalOcean (Cheapest Option)

**Droplet Setup**:

```bash
# Create droplet via web UI
# - Plan: Basic $12/month (2GB RAM, 1 vCPU)
# - OS: Ubuntu 22.04
# - Region: Choose closest to your app servers

# SSH into droplet
ssh root@your-droplet-ip

# Install NATS (same as Ubuntu steps above)
```

### Kubernetes (Any Cloud)

Create `nats-deployment.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: nats

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nats-data
  namespace: nats
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: nats-config
  namespace: nats
data:
  nats.conf: |
    port: 4222
    http_port: 8222
    jetstream {
      store_dir: "/data/jetstream"
      max_memory_store: 2GB
      max_file_store: 40GB
    }

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: nats
  namespace: nats
spec:
  serviceName: nats
  replicas: 1
  selector:
    matchLabels:
      app: nats
  template:
    metadata:
      labels:
        app: nats
    spec:
      containers:
      - name: nats
        image: nats:2.10.7-alpine
        ports:
        - containerPort: 4222
          name: client
        - containerPort: 8222
          name: monitor
        - containerPort: 6222
          name: cluster
        volumeMounts:
        - name: nats-data
          mountPath: /data
        - name: config
          mountPath: /etc/nats
        command:
        - nats-server
        - -c
        - /etc/nats/nats.conf
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8222
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8222
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: nats-config
  volumeClaimTemplates:
  - metadata:
      name: nats-data
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 50Gi

---
apiVersion: v1
kind: Service
metadata:
  name: nats
  namespace: nats
spec:
  selector:
    app: nats
  ports:
  - name: client
    port: 4222
    targetPort: 4222
  - name: monitor
    port: 8222
    targetPort: 8222
  clusterIP: None  # Headless service for StatefulSet
```

**Deploy**:
```bash
kubectl apply -f nats-deployment.yaml

# Check status
kubectl get pods -n nats
kubectl logs -n nats nats-0

# Access from app
# NATS_URL=nats://nats.nats.svc.cluster.local:4222
```

---

## Monitoring & Operations

### NATS Monitoring Dashboard

NATS exposes metrics at `http://localhost:8222/`:

- `/varz` - Server variables and stats
- `/connz` - Connection information
- `/routez` - Route information
- `/subsz` - Subscription information
- `/healthz` - Health check
- `/jsz` - JetStream stats

**Example**:
```bash
# Check server health
curl http://localhost:8222/healthz

# Get JetStream stats
curl http://localhost:8222/jsz | jq

# Monitor in real-time
watch -n 1 'curl -s http://localhost:8222/varz | jq ".cpu, .mem, .connections"'
```

### Prometheus Integration

NATS has a Prometheus exporter built-in. Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'nats'
    static_configs:
      - targets: ['localhost:8222']
    metrics_path: /metrics
```

**Run Prometheus**:
```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### Grafana Dashboard

Import NATS dashboard from Grafana:
- Dashboard ID: `2279` (NATS Server Stats)
- URL: https://grafana.com/grafana/dashboards/2279

```bash
# Run Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

# Access at http://localhost:3000
# Login: admin/admin
# Add Prometheus data source
# Import dashboard 2279
```

### Logging

**View logs**:
```bash
# Direct log file
tail -f /var/log/nats/nats-server.log

# Systemd
journalctl -u nats-server -f

# Docker
docker logs -f nats

# Kubernetes
kubectl logs -f -n nats nats-0
```

**Log levels**:
- Debug: `-DV` flag
- Trace: `-DVV` flag
- Production: default (INFO)

---

## Backup & Recovery

### Backup JetStream Data

```bash
# Stop NATS (important!)
sudo systemctl stop nats-server

# Backup data directory
tar -czf nats-backup-$(date +%Y%m%d).tar.gz /data/jetstream/

# Upload to S3 (example)
aws s3 cp nats-backup-$(date +%Y%m%d).tar.gz s3://my-backups/nats/

# Restart NATS
sudo systemctl start nats-server
```

### Restore from Backup

```bash
# Stop NATS
sudo systemctl stop nats-server

# Clear current data
rm -rf /data/jetstream/*

# Restore backup
tar -xzf nats-backup-20251022.tar.gz -C /data/

# Fix permissions
sudo chown -R nats:nats /data/jetstream

# Start NATS
sudo systemctl start nats-server
```

### Automated Backup Script

Create `backup-nats.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/nats"
DATE=$(date +%Y%m%d-%H%M%S)
S3_BUCKET="s3://my-backups/nats"

# Create snapshot
tar -czf ${BACKUP_DIR}/nats-${DATE}.tar.gz /data/jetstream/

# Upload to S3
aws s3 cp ${BACKUP_DIR}/nats-${DATE}.tar.gz ${S3_BUCKET}/

# Keep only last 7 days locally
find ${BACKUP_DIR} -name "nats-*.tar.gz" -mtime +7 -delete

echo "Backup complete: nats-${DATE}.tar.gz"
```

**Schedule with cron**:
```bash
# Run daily at 2 AM
0 2 * * * /opt/scripts/backup-nats.sh
```

---

## Security

### Authentication

Create `nats-auth.conf`:

```conf
# Basic Auth
authorization {
  users = [
    {
      user: "agent-squad-app"
      password: "change-this-password"
      permissions: {
        publish: ["agent.>"]
        subscribe: ["agent.>", "_INBOX.>"]
      }
    },
    {
      user: "monitoring"
      password: "monitoring-password"
      permissions: {
        subscribe: ["$SYS.>"]
      }
    }
  ]
}
```

**Update app config**:
```python
NATS_URL=nats://agent-squad-app:change-this-password@localhost:4222
```

### TLS Encryption

Generate certificates:
```bash
# Create CA
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -days 365 -key ca-key.pem -out ca.pem

# Create server cert
openssl genrsa -out server-key.pem 4096
openssl req -new -key server-key.pem -out server.csr
openssl x509 -req -days 365 -in server.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial -out server-cert.pem
```

Update `nats-server.conf`:
```conf
tls {
  cert_file: "/etc/nats/certs/server-cert.pem"
  key_file: "/etc/nats/certs/server-key.pem"
  ca_file: "/etc/nats/certs/ca.pem"
  verify: true
}
```

**App connection**:
```python
NATS_URL=tls://agent-squad-app:password@nats.example.com:4222
```

### Network Security

**Firewall rules** (iptables):
```bash
# Allow only from app servers
iptables -A INPUT -p tcp --dport 4222 -s 10.0.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 4222 -j DROP

# Allow monitoring from internal network
iptables -A INPUT -p tcp --dport 8222 -s 10.0.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 8222 -j DROP
```

**Security Groups** (AWS):
```
Inbound Rules:
- Port 4222: Allow from app security group
- Port 8222: Allow from monitoring security group
- Port 6222: Allow from NATS cluster security group (HA only)
```

---

## Scaling & High Availability

### Single Server (Current Setup)

- ✅ Good for: Development, staging, small production
- ✅ Cost: ~$30-50/month
- ❌ Limitation: Single point of failure
- ❌ Limitation: Vertical scaling only

### 3-Node Cluster (High Availability)

**Setup**:

1. **Server 1** (`nats-1.conf`):
```conf
port: 4222
server_name: nats-1

cluster {
  name: agent-squad-cluster
  listen: 0.0.0.0:6222
  routes: [
    nats://nats-1:6222
    nats://nats-2:6222
    nats://nats-3:6222
  ]
}

jetstream {
  store_dir: "/data/jetstream"
  max_memory_store: 2GB
  max_file_store: 50GB
}
```

2. **Server 2** (`nats-2.conf`):
```conf
port: 4222
server_name: nats-2

cluster {
  name: agent-squad-cluster
  listen: 0.0.0.0:6222
  routes: [
    nats://nats-1:6222
    nats://nats-2:6222
    nats://nats-3:6222
  ]
}

jetstream {
  store_dir: "/data/jetstream"
  max_memory_store: 2GB
  max_file_store: 50GB
}
```

3. **Server 3** (similar to above with `server_name: nats-3`)

**Start cluster**:
```bash
# On each server
nats-server -c /etc/nats/nats-server.conf

# Verify cluster
nats-server --signal reload
curl http://localhost:8222/routez
```

**App connection** (automatic failover):
```python
NATS_URL=nats://nats-1:4222,nats-2:4222,nats-3:4222
```

**Cost**: ~$90-150/month (3 × $30-50)

### Load Balancer

```nginx
# nginx.conf
upstream nats_cluster {
    server nats-1:4222;
    server nats-2:4222;
    server nats-3:4222;
}

server {
    listen 4222;
    proxy_pass nats_cluster;
}
```

---

## Cost Breakdown

### Development/Staging
- **Local**: Free (runs on your machine)
- **Docker**: Free (runs on your machine)
- **Small VPS**: $5-12/month (DigitalOcean, Linode)

### Production (Small)
- **Single EC2/GCE**: ~$30-50/month
- **Managed Container**: ~$40-60/month
- **Total with monitoring**: ~$50-80/month

### Production (High Availability)
- **3-node cluster**: ~$90-150/month
- **Load balancer**: ~$20/month
- **Monitoring**: ~$20/month
- **Backups**: ~$10/month
- **Total**: ~$140-200/month

### Comparison
- **Kafka cluster**: $300-500/month (Zookeeper + 3 brokers)
- **Redis cluster**: $200-300/month
- **RabbitMQ cluster**: $150-250/month
- **NATS cluster**: $140-200/month ✅ (Best value!)

---

## Quick Start Recommendations

### For You Right Now

**Option 1: Keep Current Local Setup** (Recommended for Development)
```bash
# Already running!
# Just set MESSAGE_BUS=nats in .env
```

**Option 2: Docker Compose** (Recommended for Team Development)
```bash
# Create docker-compose.nats.yml (see Docker section)
docker-compose -f docker-compose.nats.yml up -d
```

**Option 3: Production** (When Ready)
```bash
# AWS EC2 t3.medium instance
# Install NATS with systemd
# Configure backups
# Add monitoring
# Estimated cost: ~$50/month
```

---

## Troubleshooting

### NATS won't start

```bash
# Check if port is in use
lsof -i :4222
netstat -tulpn | grep 4222

# Check logs
tail -f nats-server.log

# Check permissions
ls -la /data/jetstream
```

### Can't connect from app

```bash
# Test connection
telnet localhost 4222
nc -zv localhost 4222

# Check firewall
sudo iptables -L -n

# Check NATS is listening
ss -tulpn | grep 4222
```

### Performance issues

```bash
# Check JetStream stats
curl http://localhost:8222/jsz | jq

# Monitor CPU/memory
top -p $(pgrep nats-server)

# Check disk I/O
iostat -x 1
```

---

## Next Steps for You

1. **Now**: Keep using local NATS (already running)
2. **Team setup**: Use Docker Compose
3. **Production**: Deploy to AWS/GCP when ready
4. **Monitoring**: Add Prometheus + Grafana
5. **High Availability**: 3-node cluster when needed

Need help with any specific deployment? Let me know!
