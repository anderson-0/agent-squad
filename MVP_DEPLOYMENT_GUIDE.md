# Agent Squad MVP - Deployment Guide

Complete guide for deploying the Agent Squad MVP to production.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Backend Deployment](#backend-deployment)
- [Template System Setup](#template-system-setup)
- [Production Checklist](#production-checklist)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Services
- **PostgreSQL** 14+ (managed service recommended: AWS RDS, DigitalOcean, Supabase)
- **Redis** 7+ (managed service recommended: AWS ElastiCache, DigitalOcean, Upstash)
- **Python** 3.11+
- **Domain** with SSL certificate (for HTTPS)

### API Keys Required
- **OpenAI API Key** - For GPT-4 agents (Backend Dev, Frontend Dev, QA)
- **Anthropic API Key** - For Claude agents (PM, Tech Lead, Solution Architect)
- **Pinecone API Key** (optional) - For RAG/vector search
- **Sendgrid API Key** (optional) - For email notifications

### Hosting Options

**Option 1: Render (Easiest)**
- ✅ Free tier available
- ✅ Automatic deployments
- ✅ Built-in PostgreSQL & Redis
- ✅ SSL certificates included

**Option 2: Railway**
- ✅ Simple pricing
- ✅ Auto-scaling
- ✅ Built-in databases
- ✅ Easy environment variables

**Option 3: AWS (Most Scalable)**
- ✅ Full control
- ✅ Best for enterprise
- ⚠️ More complex setup
- ⚠️ Higher cost

**Option 4: DigitalOcean App Platform**
- ✅ Simple pricing
- ✅ Good performance
- ✅ Managed databases
- ✅ Auto-scaling

## Environment Configuration

### 1. Create Production Environment File

Create `.env.production` in the `backend/` directory:

```bash
# Application
APP_NAME="Agent Squad"
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (Replace with your production database URL)
DATABASE_URL=postgresql+asyncpg://username:password@host:5432/agent_squad_prod

# Redis (Replace with your production Redis URL)
REDIS_URL=redis://username:password@host:6379/0

# Security
SECRET_KEY=generate-a-secure-random-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Providers
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# Optional: RAG/Context
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east1-gcp
PINECONE_INDEX_NAME=agent-squad

# Optional: Email
SENDGRID_API_KEY=SG.your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME="Agent Squad"

# CORS
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

### 2. Generate Secure Secret Key

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use openssl
openssl rand -hex 32
```

### 3. Environment Variables Checklist

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string |
| `REDIS_URL` | ✅ Yes | Redis connection string |
| `SECRET_KEY` | ✅ Yes | JWT signing secret (32+ chars) |
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for GPT-4 agents |
| `ANTHROPIC_API_KEY` | ✅ Yes | Anthropic key for Claude agents |
| `ALLOWED_ORIGINS` | ✅ Yes | CORS allowed origins |
| `PINECONE_API_KEY` | ⚠️ Optional | RAG/vector search |
| `SENDGRID_API_KEY` | ⚠️ Optional | Email notifications |

## Database Setup

### 1. Create Production Database

**For Managed PostgreSQL (AWS RDS, DigitalOcean):**

```sql
-- Connect to your managed PostgreSQL instance
CREATE DATABASE agent_squad_prod;
CREATE USER agent_squad_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE agent_squad_prod TO agent_squad_user;

-- Switch to the database
\c agent_squad_prod

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO agent_squad_user;
```

**Connection String Format:**
```
postgresql+asyncpg://agent_squad_user:secure-password@host:5432/agent_squad_prod
```

### 2. Run Database Migrations

```bash
cd backend

# Set production database URL
export DATABASE_URL=postgresql+asyncpg://agent_squad_user:secure-password@host:5432/agent_squad_prod

# Run all migrations
alembic upgrade head

# Verify migrations
alembic current
```

Expected output:
```
8ac963704cb9 (head)
```

### 3. Create Initial User

```bash
# Start Python shell
python

# Create admin user
from backend.core.database import AsyncSessionLocal
from backend.services.user_service import UserService
from backend.schemas.user import UserCreate
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        user_data = UserCreate(
            email="admin@yourdomain.com",
            password="SecurePassword123!",
            full_name="Admin User"
        )
        user = await UserService.create_user(db, user_data)
        print(f"Created admin user: {user.email}")

asyncio.run(create_admin())
```

### 4. Load Squad Template

```bash
# Load the Software Development Squad template
python -m backend.cli.load_template templates/software_dev_squad.yaml

# Verify template loaded
python -m backend.cli.apply_template --list
```

Expected output:
```
⭐ Software Development Squad
    Slug: software-dev-squad
    Agents: 6
    Routing Rules: 17
```

## Backend Deployment

### Option 1: Deploy to Render

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
   ```yaml
   Name: agent-squad-backend
   Environment: Python 3
   Branch: main
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && uvicorn core.app:app --host 0.0.0.0 --port $PORT
   ```

3. **Add Environment Variables**
   - Add all variables from `.env.production`
   - Render will provide `DATABASE_URL` and `REDIS_URL` if using their services

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Test: `https://your-app.onrender.com/health`

### Option 2: Deploy to Railway

1. **Create New Project**
   - Go to [Railway](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"

2. **Add Services**
   ```bash
   # Add PostgreSQL database
   railway add postgres

   # Add Redis
   railway add redis

   # Railway will automatically set DATABASE_URL and REDIS_URL
   ```

3. **Configure Backend**
   ```bash
   # Set build command
   railway variables set BUILD_COMMAND="pip install -r backend/requirements.txt"

   # Set start command
   railway variables set START_COMMAND="cd backend && alembic upgrade head && uvicorn core.app:app --host 0.0.0.0 --port $PORT"
   ```

4. **Add Environment Variables**
   - Go to Variables tab
   - Add all variables from `.env.production`

5. **Deploy**
   - Push to main branch
   - Railway will auto-deploy
   - Test: `https://your-app.up.railway.app/health`

### Option 3: Deploy to AWS (Advanced)

**Use Docker Compose for production:**

```bash
# 1. Build production image
docker build -t agent-squad-backend:latest -f backend/Dockerfile .

# 2. Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
docker tag agent-squad-backend:latest $ECR_REGISTRY/agent-squad-backend:latest
docker push $ECR_REGISTRY/agent-squad-backend:latest

# 3. Deploy to ECS/Fargate
aws ecs update-service --cluster agent-squad --service backend --force-new-deployment
```

**Or use AWS Elastic Beanstalk:**

```bash
# 1. Initialize EB
eb init -p python-3.11 agent-squad

# 2. Create environment
eb create production-env

# 3. Set environment variables
eb setenv DATABASE_URL=$DATABASE_URL \
         REDIS_URL=$REDIS_URL \
         SECRET_KEY=$SECRET_KEY \
         OPENAI_API_KEY=$OPENAI_API_KEY \
         ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# 4. Deploy
eb deploy
```

## Template System Setup

### 1. Verify Template Loaded

```bash
# SSH into your production server or use local connection to prod DB
export DATABASE_URL=postgresql+asyncpg://...production...

# List templates
python -m backend.cli.apply_template --list
```

### 2. Create Initial Squad

```bash
# Create a squad from template for testing
python -m backend.cli.apply_template \
  --user-email admin@yourdomain.com \
  --template software-dev-squad \
  --squad-name "Production Test Squad"
```

Expected output:
```
✓ Created squad: Production Test Squad
✓ Agents created: 6
✓ Routing rules: 17
```

### 3. Test Routing Engine

```bash
# Run E2E test against production database
DEBUG=False python test_mvp_e2e.py
```

All tests should pass:
- ✅ Template loading
- ✅ Squad creation
- ✅ Routing engine (3/3 tests)
- ✅ Escalation chain (3 levels)
- ✅ Conversation flow
- ✅ Cross-role routing

## Production Checklist

### Security ✅

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` (32+ characters, random)
- [ ] HTTPS enabled (SSL certificate)
- [ ] CORS configured with specific origins
- [ ] Rate limiting enabled
- [ ] Database uses strong password
- [ ] Redis uses password authentication
- [ ] API keys stored in environment variables (not code)
- [ ] No secrets committed to Git

### Performance ✅

- [ ] Database connection pooling configured
- [ ] Redis caching enabled
- [ ] Static files served via CDN
- [ ] Gzip compression enabled
- [ ] Database indexes created (via migrations)
- [ ] Query optimization reviewed
- [ ] Background tasks use Celery (if needed)

### Monitoring ✅

- [ ] Health check endpoint working (`/health`)
- [ ] Logging configured (INFO level)
- [ ] Error tracking setup (Sentry, Rollbar)
- [ ] Performance monitoring (New Relic, DataDog)
- [ ] Database monitoring enabled
- [ ] Uptime monitoring (UptimeRobot, Pingdom)
- [ ] API metrics tracked

### Data ✅

- [ ] Database backups automated (daily)
- [ ] Backup restoration tested
- [ ] Migration rollback plan documented
- [ ] Data retention policy defined
- [ ] GDPR compliance reviewed (if EU users)

### Documentation ✅

- [ ] API documentation accessible (`/docs`)
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Rollback procedure documented
- [ ] Emergency contacts listed

## Monitoring & Maintenance

### Health Checks

```bash
# Check application health
curl https://your-domain.com/health

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

### Database Monitoring

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'agent_squad_prod';

-- Check database size
SELECT pg_size_pretty(pg_database_size('agent_squad_prod'));

-- Check table sizes
SELECT
    schemaname as schema,
    tablename as table,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Logs

```bash
# View application logs (Render)
render logs --tail

# View application logs (Railway)
railway logs

# View application logs (AWS)
aws logs tail /aws/ecs/agent-squad --follow

# Search for errors
grep "ERROR" production.log
```

### Backup & Restore

```bash
# Backup database (manual)
pg_dump -h host -U agent_squad_user agent_squad_prod > backup_$(date +%Y%m%d).sql

# Restore database
psql -h host -U agent_squad_user agent_squad_prod < backup_20251022.sql

# Automated backups (AWS RDS)
aws rds create-db-snapshot --db-instance-identifier agent-squad --db-snapshot-identifier agent-squad-snapshot-$(date +%Y%m%d)
```

## Troubleshooting

### 502 Bad Gateway

**Cause:** Backend not responding

**Solution:**
```bash
# Check if backend is running
ps aux | grep uvicorn

# Check logs
tail -f /var/log/agent-squad/error.log

# Restart backend
systemctl restart agent-squad
```

### Database Connection Errors

**Cause:** Incorrect DATABASE_URL or database down

**Solution:**
```bash
# Test database connection
psql $DATABASE_URL

# Check if database is accepting connections
pg_isready -h host -p 5432

# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@host:5432/dbname
```

### Redis Connection Errors

**Cause:** Incorrect REDIS_URL or Redis down

**Solution:**
```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping
# Expected: PONG

# Check if Redis is running
redis-cli -h host -p 6379 info server
```

### Template Not Found

**Cause:** Template not loaded in production database

**Solution:**
```bash
# Load template
python -m backend.cli.load_template templates/software_dev_squad.yaml

# Verify
python -m backend.cli.apply_template --list
```

### Agent Communication Errors

**Cause:** Message bus configuration or database issues

**Solution:**
```bash
# Check message bus type
echo $MESSAGE_BUS  # Should be "memory" for MVP

# Run E2E test
DEBUG=False python test_mvp_e2e.py

# Check conversation table
psql $DATABASE_URL -c "SELECT count(*) FROM agent_conversations;"
```

### OpenAI/Anthropic API Errors

**Cause:** Invalid API key or rate limits

**Solution:**
```bash
# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Anthropic API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"

# Check rate limits in logs
grep "rate_limit" production.log
```

## Scaling Recommendations

### When to Scale

**Scale up when:**
- Response time > 500ms consistently
- Database connections > 80% capacity
- Redis memory > 80% capacity
- CPU usage > 70% consistently
- Error rate > 1%

### Horizontal Scaling

```bash
# Increase number of backend instances (Render/Railway)
# Go to dashboard and adjust instance count

# AWS ECS
aws ecs update-service \
  --cluster agent-squad \
  --service backend \
  --desired-count 3
```

### Database Scaling

```bash
# AWS RDS - Increase instance size
aws rds modify-db-instance \
  --db-instance-identifier agent-squad \
  --db-instance-class db.t3.large \
  --apply-immediately

# Add read replicas
aws rds create-db-instance-read-replica \
  --db-instance-identifier agent-squad-read-1 \
  --source-db-instance-identifier agent-squad
```

### Redis Scaling

```bash
# AWS ElastiCache - Increase node size
aws elasticache modify-cache-cluster \
  --cache-cluster-id agent-squad-redis \
  --cache-node-type cache.t3.medium \
  --apply-immediately
```

## Post-Deployment Verification

### 1. Smoke Tests

```bash
# Test health endpoint
curl https://your-domain.com/health

# Test authentication
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourdomain.com", "password": "password"}'

# Test template listing
curl https://your-domain.com/api/v1/templates/ \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Load Testing

```bash
# Install k6
brew install k6  # macOS
# or: sudo apt install k6  # Ubuntu

# Run load test
k6 run load-test.js

# Monitor response times and error rates
```

### 3. Monitor First 24 Hours

- [ ] Check error logs every 2 hours
- [ ] Monitor response times
- [ ] Watch database connection count
- [ ] Track API key usage/costs
- [ ] Verify backup completed successfully

## Support & Maintenance

### Regular Tasks

**Daily:**
- Check error logs
- Monitor API costs (OpenAI/Anthropic)
- Review slow queries

**Weekly:**
- Verify backups working
- Review performance metrics
- Check for security updates
- Update dependencies

**Monthly:**
- Database maintenance (VACUUM, ANALYZE)
- Review and optimize indexes
- Audit user activity
- Update documentation

### Emergency Contacts

```
Production Issues: [Your contact]
Database Admin: [DBA contact]
DevOps: [DevOps contact]
On-call: [On-call rotation]
```

## Next Steps

1. ✅ Complete all checklist items
2. ✅ Run E2E test against production
3. ✅ Monitor first 24 hours closely
4. ✅ Document any issues encountered
5. ✅ Set up automated monitoring alerts
6. ✅ Create runbook for common issues

---

**🎉 Congratulations! Your Agent Squad MVP is now deployed to production!**

For questions or issues, refer to:
- [Template System Guide](./TEMPLATE_SYSTEM_GUIDE.md)
- [API Documentation](https://your-domain.com/docs)
- [Architecture Overview](./docs/architecture/overview.md)
