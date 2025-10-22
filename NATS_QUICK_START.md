# NATS Quick Start - TL;DR Version

**You want to use NATS but don't know how? Here's the simplest path.**

---

## Current Status: ✅ You're Already Set Up!

NATS is already running on your machine at `localhost:4222`

Check it:
```bash
ps aux | grep nats-server
# You should see it running!
```

---

## 3 Deployment Options (Choose One)

### Option 1: Local Development (What You Have Now) ✅

**Current setup**:
- NATS running on your Mac
- Perfect for development and testing
- Free, no infrastructure needed

**To use it**:
```bash
# In your .env file
MESSAGE_BUS=nats
NATS_URL=nats://localhost:4222
```

**To restart if needed**:
```bash
./nats/nats-server-v2.10.7-darwin-arm64/nats-server \
  -js \
  -p 4222 \
  --store_dir ./nats-data
```

**Cost**: $0
**Complexity**: 1/10
**When to use**: Development, testing, demos

---

### Option 2: Docker (Recommended for Teams)

**Setup** (5 minutes):

1. Create `docker-compose.nats.yml`:
```yaml
version: '3.8'

services:
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
      --max_mem_store 1GB
      --max_file_store 10GB
    volumes:
      - nats-data:/data
    restart: unless-stopped

volumes:
  nats-data:
```

2. Start it:
```bash
docker-compose -f docker-compose.nats.yml up -d
```

3. Use it:
```bash
# In your .env
MESSAGE_BUS=nats
NATS_URL=nats://nats:4222  # or nats://localhost:4222
```

4. Monitor it:
```bash
# Check health
docker logs nats

# View stats
curl http://localhost:8222/varz
```

**Cost**: $0 (runs on your machine)
**Complexity**: 3/10
**When to use**: Team development, consistent environment

---

### Option 3: Production (AWS/Cloud)

**Simplest Production Setup** (15 minutes):

#### Step 1: Launch EC2 Instance

**Via AWS Console**:
1. Go to EC2 → Launch Instance
2. Choose: Ubuntu 22.04 LTS
3. Instance type: t3.medium (2 vCPU, 4GB RAM)
4. Storage: 50GB
5. Security group: Allow ports 4222 (NATS), 22 (SSH)
6. Launch

**Cost**: ~$30/month

#### Step 2: Install NATS on Server

SSH into your instance:
```bash
ssh ubuntu@your-ec2-ip

# Download and install NATS
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo mv nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/

# Create data directory
sudo mkdir -p /data/jetstream
sudo chmod 755 /data/jetstream

# Start NATS (simple way)
nats-server -js -p 4222 --store_dir /data/jetstream &

# Or set up as systemd service (production-ready)
```

#### Step 3: Create Systemd Service (Recommended)

```bash
# Create service file
sudo nano /etc/systemd/system/nats.service
```

Paste this:
```ini
[Unit]
Description=NATS Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/nats-server -js -p 4222 --store_dir /data/jetstream -m 8222
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Start it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable nats
sudo systemctl start nats

# Check status
sudo systemctl status nats
```

#### Step 4: Configure Your App

```bash
# In your app's .env file
MESSAGE_BUS=nats
NATS_URL=nats://your-ec2-private-ip:4222
```

**Cost**: ~$30/month (EC2 instance)
**Complexity**: 6/10
**When to use**: Production, multiple app servers

---

## Monitoring Your NATS Server

**Health Check**:
```bash
# Local
curl http://localhost:8222/healthz

# Production
curl http://your-server:8222/healthz
```

**View Statistics**:
```bash
# Server stats
curl http://localhost:8222/varz | jq

# JetStream stats
curl http://localhost:8222/jsz | jq

# Connection stats
curl http://localhost:8222/connz | jq
```

**Real-time Monitoring**:
```bash
watch -n 1 'curl -s http://localhost:8222/varz | jq ".cpu, .mem, .connections"'
```

---

## Common Commands

### Start/Stop NATS

**Local (manual)**:
```bash
# Start
./nats/nats-server-v2.10.7-darwin-arm64/nats-server -js -p 4222 --store_dir ./nats-data

# Stop
pkill nats-server
```

**Docker**:
```bash
# Start
docker-compose -f docker-compose.nats.yml up -d

# Stop
docker-compose -f docker-compose.nats.yml down

# Restart
docker-compose -f docker-compose.nats.yml restart
```

**Production (systemd)**:
```bash
# Start
sudo systemctl start nats

# Stop
sudo systemctl stop nats

# Restart
sudo systemctl restart nats

# Status
sudo systemctl status nats

# Logs
sudo journalctl -u nats -f
```

---

## Testing Your Setup

Run the integration tests we created:
```bash
backend/.venv/bin/python test_nats_integration.py
```

Expected output:
```
✓ PASS  Message Bus Factory
✓ PASS  NATS Connection
✓ PASS  Message Sending
✓ PASS  NATS Statistics
✓ PASS  Real Agent Integration

Results: 5/5 tests passed
🎉 All tests passed!
```

---

## Troubleshooting

### "Connection refused"

```bash
# Check if NATS is running
ps aux | grep nats-server

# Check if port is open
netstat -tuln | grep 4222

# Start NATS if not running
./nats/nats-server-v2.10.7-darwin-arm64/nats-server -js -p 4222 --store_dir ./nats-data
```

### "Stream not found"

This is normal! The stream is created automatically on first message.

### "Permission denied" (Docker)

```bash
# Fix volume permissions
docker-compose down
docker volume rm $(docker volume ls -q | grep nats)
docker-compose up -d
```

---

## Cost Summary

| Setup | Monthly Cost | Setup Time | Best For |
|-------|-------------|------------|----------|
| **Local** | $0 | 0 min (done!) | Development |
| **Docker** | $0 | 5 min | Team dev |
| **AWS EC2** | ~$30 | 15 min | Production |
| **AWS HA Cluster** | ~$90 | 1 hour | High availability |

---

## Recommended Path for You

**Today**: Use local setup (already working!)
```bash
# Just set in .env:
MESSAGE_BUS=nats
NATS_URL=nats://localhost:4222
```

**When sharing with team**: Switch to Docker
```bash
docker-compose -f docker-compose.nats.yml up -d
```

**When deploying**: Set up AWS EC2 instance
- Follow Option 3 above
- Cost: ~$30/month

---

## Need Help?

**Full Documentation**:
- `NATS_INFRASTRUCTURE_GUIDE.md` - Complete infrastructure guide
- `NATS_MIGRATION_PLAN.md` - Migration progress and details

**Official NATS Docs**:
- https://docs.nats.io/
- https://docs.nats.io/nats-concepts/jetstream

**Test Commands**:
```bash
# Run integration tests
backend/.venv/bin/python test_nats_integration.py

# Check NATS stats
curl http://localhost:8222/varz | jq

# View stream
curl http://localhost:8222/jsz | jq
```

---

## You're Done! 🎉

Your NATS setup is complete and working. The integration is transparent - your code doesn't change, just flip the `MESSAGE_BUS` environment variable.

**Next Steps**:
1. Try switching to NATS mode: `MESSAGE_BUS=nats`
2. Run the tests to verify: `backend/.venv/bin/python test_nats_integration.py`
3. Monitor with: `curl http://localhost:8222/varz | jq`

That's it! You're using a production-grade message bus that can scale to millions of messages per second.
