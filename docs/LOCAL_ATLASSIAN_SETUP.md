# Local Atlassian Setup - Jira & Confluence

**Complete guide for running Jira and Confluence locally with Docker**

---

## 📋 Overview

This setup provides **real Jira and Confluence instances** running locally in Docker containers for development and testing, replacing mocked responses with actual API calls.

### What You Get

- ✅ **Jira Software 9.12.0** - Full-featured issue tracking
- ✅ **Confluence 8.5.0** - Complete documentation platform
- ✅ **PostgreSQL databases** - Separate DB for each service
- ✅ **Persistent data** - Data survives container restarts
- ✅ **Evaluation licenses** - 90-day free trial (renewable)

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **Docker**: Docker Desktop or Docker Engine
- **Ports**: 8080 (Jira), 8090/8091 (Confluence), 5433/5434 (PostgreSQL)

---

## 🚀 Quick Start

### 1. Start Services

```bash
# Option A: Use the setup script (recommended)
./scripts/setup-atlassian.sh

# Option B: Manual start
docker-compose up -d jira-postgres confluence-postgres jira confluence
```

**First run will take 5-10 minutes** (downloading ~2GB of images)

**Subsequent starts take 2-3 minutes** (containers warming up)

### 2. Wait for Services

Monitor startup progress:

```bash
# Watch Jira logs
docker logs -f agent-squad-jira

# Watch Confluence logs
docker logs -f agent-squad-confluence

# Check health status
docker ps --filter "name=jira" --filter "name=confluence"
```

Services are ready when:
- ✅ Jira: `http://localhost:8080` shows setup wizard
- ✅ Confluence: `http://localhost:8090` shows setup wizard

---

## ⚙️ Initial Configuration

### Step 1: Configure Jira (http://localhost:8080)

1. **Welcome Screen**
   - Click **"Set it up for me"**

2. **License**
   - Select **"Generate an evaluation license"**
   - You'll need an Atlassian account (free signup)
   - License is valid for 90 days

3. **Database**
   - Already configured! (Using PostgreSQL from docker-compose)
   - Click **"Next"** to accept default database settings

4. **Admin Account**
   ```
   Username: admin
   Email:    admin@example.com
   Password: admin123
   ```
   (Use these credentials consistently)

5. **Email Setup**
   - Skip for local development
   - Click **"Finish"**

6. **Create Project**
   - Choose **"Scrum"** or **"Kanban"**
   - Project Key: **TEST**
   - Project Name: **Test Project**

### Step 2: Configure Confluence (http://localhost:8090)

1. **Welcome Screen**
   - Select **"Production Installation"**

2. **License**
   - Click **"Get an evaluation license"**
   - Use same Atlassian account as Jira
   - License is valid for 90 days

3. **Database**
   - Already configured! (Using PostgreSQL from docker-compose)
   - Click **"Next"**

4. **Load Content**
   - Choose **"Empty Site"** for clean start
   - Or **"Example Site"** for sample content

5. **Admin Account**
   ```
   Username: admin
   Email:    admin@example.com
   Password: admin123
   ```
   (Same as Jira for consistency)

6. **Create Space**
   - Space Key: **DEV**
   - Space Name: **Development**

---

## 🔑 API Token Setup

To use Jira/Confluence APIs, you need an API token:

### Generate Token

**For Jira Cloud API tokens** (if using Jira/Confluence Server, use basic auth):

1. Go to: http://localhost:8080
2. Click profile icon (top right) → **Profile**
3. Go to **Personal Access Tokens**
4. Click **Create token**
5. Name: `agent-squad`
6. Copy the token immediately (shown only once)

**For local Docker setup**, use **Basic Auth** instead:
- Username: `admin@example.com`
- Password: `admin123`
- No token needed!

### Update .env File

Create or update `.env` in the project root:

```bash
# Jira Configuration
JIRA_URL=http://localhost:8080
JIRA_USERNAME=admin@example.com
JIRA_API_TOKEN=admin123

# Confluence Configuration
CONFLUENCE_URL=http://localhost:8090
CONFLUENCE_USERNAME=admin@example.com
CONFLUENCE_API_TOKEN=admin123
```

**Note**: For local Docker instances, the "API_TOKEN" is just your password.

---

## 🧪 Testing with Real Services

### Run Integration Tests

```bash
# Test Jira integration
docker exec agent-squad-backend pytest backend/tests/test_jira_service.py -v -s

# Test Confluence integration
docker exec agent-squad-backend pytest backend/tests/test_confluence_service.py -v -s

# Test complete workflow
docker exec agent-squad-backend pytest backend/tests/test_integration/test_ticket_to_pr.py -v -s
```

### Create Test Data

#### In Jira:

```bash
# Use Jira UI (http://localhost:8080):
1. Create a few test issues in TEST project
2. Try different issue types (Task, Bug, Story)
3. Add comments
4. Transition issues (To Do → In Progress → Done)
```

#### In Confluence:

```bash
# Use Confluence UI (http://localhost:8090):
1. Create pages in DEV space
2. Add content with rich text
3. Create child pages
4. Try searching for content
```

---

## 📊 Service Management

### Start Services

```bash
# Start all Atlassian services
docker-compose up -d jira-postgres confluence-postgres jira confluence

# Start only Jira
docker-compose up -d jira-postgres jira

# Start only Confluence
docker-compose up -d confluence-postgres confluence
```

### Stop Services

```bash
# Stop all Atlassian services
docker-compose stop jira confluence jira-postgres confluence-postgres

# Stop only Jira
docker-compose stop jira jira-postgres

# Stop only Confluence
docker-compose stop confluence confluence-postgres
```

### View Logs

```bash
# Jira logs (follow)
docker logs -f agent-squad-jira

# Confluence logs (follow)
docker logs -f agent-squad-confluence

# All logs (last 100 lines)
docker-compose logs --tail=100 jira confluence
```

### Restart Services

```bash
# Restart after configuration changes
docker-compose restart jira confluence
```

### Check Status

```bash
# Service health
docker ps --filter "name=jira" --filter "name=confluence"

# Database health
docker exec agent-squad-jira-postgres pg_isready -U jira
docker exec agent-squad-confluence-postgres pg_isready -U confluence
```

---

## 🗄️ Data Management

### Backup Data

```bash
# Backup Jira data
docker run --rm \
  --volumes-from agent-squad-jira \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/jira-data-$(date +%Y%m%d).tar.gz \
  /var/atlassian/application-data/jira

# Backup Confluence data
docker run --rm \
  --volumes-from agent-squad-confluence \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/confluence-data-$(date +%Y%m%d).tar.gz \
  /var/atlassian/application-data/confluence

# Backup databases
docker exec agent-squad-jira-postgres \
  pg_dump -U jira jiradb > backups/jiradb-$(date +%Y%m%d).sql

docker exec agent-squad-confluence-postgres \
  pg_dump -U confluence confluencedb > backups/confluencedb-$(date +%Y%m%d).sql
```

### Reset to Clean State

```bash
# WARNING: This deletes all data!

# Stop services
docker-compose stop jira confluence jira-postgres confluence-postgres

# Remove volumes (deletes all data)
docker volume rm agent-squad_jira_data
docker volume rm agent-squad_confluence_data
docker volume rm agent-squad_jira_postgres_data
docker volume rm agent-squad_confluence_postgres_data

# Start fresh
docker-compose up -d jira-postgres confluence-postgres jira confluence
```

### Export Test Data

Create a script to populate test data:

```python
# scripts/populate_test_data.py
import asyncio
from backend.integrations.jira_service import JiraService
from backend.integrations.confluence_service import ConfluenceService
from backend.integrations.mcp.client import MCPClientManager

async def populate():
    mcp = MCPClientManager()

    # Create Jira issues
    jira = JiraService(
        mcp,
        "http://localhost:8080",
        "admin@example.com",
        "admin123"
    )
    await jira.initialize()

    for i in range(5):
        await jira.create_issue(
            project="TEST",
            summary=f"Test Issue {i+1}",
            description=f"This is test issue number {i+1}",
            issue_type="Task"
        )

    # Create Confluence pages
    confluence = ConfluenceService(
        mcp,
        "http://localhost:8090",
        "admin@example.com",
        "admin123"
    )
    await confluence.initialize()

    for i in range(3):
        await confluence.create_page(
            space="DEV",
            title=f"Test Page {i+1}",
            content=f"<p>This is test page number {i+1}</p>"
        )

    await jira.cleanup()
    await confluence.cleanup()

asyncio.run(populate())
```

---

## 🔧 Troubleshooting

### Jira Won't Start

**Symptom**: Container exits or keeps restarting

```bash
# Check logs
docker logs agent-squad-jira --tail=100

# Common issues:
1. Insufficient memory (needs 2GB minimum)
   - Solution: Increase Docker memory limit

2. Port 8080 already in use
   - Solution: Stop other services or change port in docker-compose.yml

3. Database connection failed
   - Solution: Ensure jira-postgres is healthy
   docker ps --filter "name=jira-postgres"
```

### Confluence Won't Start

**Symptom**: Container exits or keeps restarting

```bash
# Check logs
docker logs agent-squad-confluence --tail=100

# Common issues:
1. Insufficient memory (needs 2GB minimum)
   - Solution: Increase Docker memory limit

2. Port 8090 already in use
   - Solution: Stop other services or change port

3. Synchrony (collaboration) service issues
   - Solution: Disable Synchrony for local dev in Confluence admin
```

### API Authentication Fails

**Symptom**: 401 Unauthorized errors

```bash
# For local Docker instances, use basic auth:
Username: admin@example.com
Password: admin123

# NOT: API tokens (those are for Cloud only)

# Update your .env:
JIRA_API_TOKEN=admin123  # This is the password, not a token
CONFLUENCE_API_TOKEN=admin123
```

### Slow Performance

**Symptom**: Services take forever to respond

```bash
# Solutions:
1. Increase Docker memory (8GB+ recommended)
2. Close other applications
3. Use SSD storage for Docker volumes
4. Reduce JVM memory if needed:
   - Edit docker-compose.yml
   - Change: JVM_MAXIMUM_MEMORY=2048m (reduce from 4096m)
```

### License Expired

**Symptom**: "License expired" message after 90 days

```bash
# Solutions:
1. Generate new evaluation license (free)
2. Or use trial license (same process as initial setup)
3. Or use developer license (also free)
```

### Can't Access from Host

**Symptom**: `curl http://localhost:8080` fails

```bash
# Check if services are running
docker ps | grep jira

# Check if ports are exposed
docker port agent-squad-jira

# Test from inside container
docker exec agent-squad-jira curl -I http://localhost:8080

# Check firewall settings
# macOS: System Preferences > Security > Firewall
# Linux: sudo ufw status
```

---

## 🎯 Best Practices

### Development Workflow

1. **Start services at beginning of day**
   ```bash
   docker-compose up -d jira confluence
   ```

2. **Keep them running during development**
   - Saves 2-3 minutes per restart
   - Maintains session state

3. **Stop services when done**
   ```bash
   docker-compose stop jira confluence
   ```

4. **Backup before major changes**
   ```bash
   ./scripts/backup-atlassian.sh
   ```

### Resource Management

```bash
# Check resource usage
docker stats agent-squad-jira agent-squad-confluence

# Typical usage:
# Jira: 2-3GB RAM, 10-20% CPU
# Confluence: 2-3GB RAM, 10-20% CPU

# If running low on resources:
# 1. Stop one service if you only need the other
# 2. Reduce JVM memory in docker-compose.yml
# 3. Increase Docker Desktop memory limit
```

### Test Data Management

```bash
# Create reusable test data sets
1. Set up initial data via UI
2. Backup volumes
3. Restore when needed

# Use consistent test data:
Project: TEST
Space: DEV
Admin: admin@example.com / admin123
```

---

## 📚 Useful URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Jira | http://localhost:8080 | Main Jira UI |
| Jira API | http://localhost:8080/rest/api/2 | REST API v2 |
| Jira Admin | http://localhost:8080/secure/admin | Admin console |
| Confluence | http://localhost:8090 | Main Confluence UI |
| Confluence API | http://localhost:8090/rest/api | REST API |
| Confluence Admin | http://localhost:8090/admin | Admin console |

---

## 🔍 Useful API Examples

### Test Jira Connection

```bash
# Get server info
curl -u admin@example.com:admin123 \
  http://localhost:8080/rest/api/2/serverInfo

# Search issues
curl -u admin@example.com:admin123 \
  http://localhost:8080/rest/api/2/search?jql=project=TEST
```

### Test Confluence Connection

```bash
# Get server info
curl -u admin@example.com:admin123 \
  http://localhost:8090/rest/api/space

# Search content
curl -u admin@example.com:admin123 \
  "http://localhost:8090/rest/api/content/search?cql=space=DEV"
```

---

## 🎉 You're All Set!

Your local Atlassian environment is ready for:
- ✅ Real API testing
- ✅ Integration development
- ✅ Agent workflow testing
- ✅ End-to-end automation

**Next Steps:**
1. Create test issues in Jira
2. Create test pages in Confluence
3. Run integration tests
4. Build agent workflows!

---

**Questions or Issues?**
- Check troubleshooting section above
- Review Docker logs
- Test API endpoints manually
- Verify .env configuration
