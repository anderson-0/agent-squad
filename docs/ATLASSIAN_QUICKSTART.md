# Atlassian Quick Start Guide

**Get Jira and Confluence running in 10 minutes!**

---

## 🚀 Super Quick Start

```bash
# 1. Start services (takes 5-10 minutes first time)
./scripts/setup-atlassian.sh

# 2. Wait for services to be ready
# Jira will be at: http://localhost:8080
# Confluence will be at: http://localhost:8090

# 3. Complete setup wizards (see below)

# 4. Update .env with credentials

# 5. Test!
docker exec agent-squad-backend pytest backend/tests/test_jira_service.py -v
```

---

## ⚡ Setup Wizards (3 minutes each)

### Jira Setup (http://localhost:8080)

1. Click **"Set it up for me"**
2. Click **"Generate evaluation license"** (free, 90 days)
3. Create admin account:
   - Email: `admin@example.com`
   - Password: `admin123`
4. Create project:
   - Type: **Scrum**
   - Key: **TEST**
   - Name: **Test Project**
5. Done!

### Confluence Setup (http://localhost:8090)

1. Click **"Production Installation"**
2. Click **"Get evaluation license"** (free, 90 days)
3. Choose **"Empty Site"**
4. Create admin account (same as Jira):
   - Email: `admin@example.com`
   - Password: `admin123`
5. Create space:
   - Key: **DEV**
   - Name: **Development**
6. Done!

---

## 🔧 Configure .env

Copy `.env.example` to `.env` and update:

```bash
# For local Docker instances
JIRA_URL=http://localhost:8080
JIRA_USERNAME=admin@example.com
JIRA_API_TOKEN=admin123

CONFLUENCE_URL=http://localhost:8090
CONFLUENCE_USERNAME=admin@example.com
CONFLUENCE_API_TOKEN=admin123
```

**Note**: For local Docker, "API_TOKEN" is just the password!

---

## 🧪 Test It Works

```bash
# Test Jira connection
curl -u admin@example.com:admin123 http://localhost:8080/rest/api/2/serverInfo

# Test Confluence connection
curl -u admin@example.com:admin123 http://localhost:8090/rest/api/space

# Run integration tests
docker exec agent-squad-backend pytest backend/tests/test_jira_service.py -v
docker exec agent-squad-backend pytest backend/tests/test_confluence_service.py -v
```

---

## 📊 Daily Usage

```bash
# Start (quick - services already configured)
docker-compose up -d jira confluence

# Stop (save resources when not in use)
docker-compose stop jira confluence

# View logs
docker logs -f agent-squad-jira
docker logs -f agent-squad-confluence

# Check status
docker ps | grep -E "jira|confluence"
```

---

## 🎯 Create Test Data

### In Jira (http://localhost:8080):
1. Click **"Create"** button
2. Fill in:
   - Project: **TEST**
   - Issue Type: **Task**
   - Summary: "Test Issue"
3. Click **"Create"**
4. Repeat for a few issues

### In Confluence (http://localhost:8090):
1. Go to **DEV** space
2. Click **"Create"** button
3. Add title: "Test Page"
4. Add some content
5. Click **"Publish"**
6. Repeat for a few pages

---

## ⚠️ Common Issues

### "Services won't start"
```bash
# Check Docker memory (needs 8GB minimum)
docker stats

# Increase Docker Desktop memory:
# Settings → Resources → Memory → 8GB+
```

### "Port already in use"
```bash
# Change ports in docker-compose.yml
# Jira: 8080 → 8081
# Confluence: 8090 → 8091
```

### "License expired"
```bash
# Just generate a new one (free, takes 1 minute):
# http://localhost:8080 → Administration → Licensing
```

---

## 📚 Full Documentation

See [LOCAL_ATLASSIAN_SETUP.md](./LOCAL_ATLASSIAN_SETUP.md) for complete documentation including:
- Detailed setup steps
- Advanced configuration
- Backup/restore procedures
- API examples
- Troubleshooting guide

---

## 🎉 You're Ready!

- ✅ Jira running at http://localhost:8080
- ✅ Confluence running at http://localhost:8090
- ✅ Real API testing enabled
- ✅ Integration tests working

**Now build some agent workflows!** 🤖
