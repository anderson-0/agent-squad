# Agent Squad MVP - Production Readiness Checklist

Quick reference checklist before deploying to production.

**Last Updated:** October 22, 2025
**Version:** MVP 1.0

---

## Pre-Deployment Checklist

### ☑️ Environment & Configuration

- [ ] `.env.production` file created with all required variables
- [ ] `DEBUG=False` in production environment
- [ ] `SECRET_KEY` generated (32+ characters, cryptographically secure)
- [ ] `DATABASE_URL` configured with production PostgreSQL
- [ ] `REDIS_URL` configured with production Redis
- [ ] `ALLOWED_ORIGINS` set to specific production domains (no `*`)
- [ ] All API keys added (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
- [ ] Environment variables verified (no typos, no missing values)

### ☑️ Database

- [ ] Production database created
- [ ] Database user created with strong password
- [ ] Database permissions granted correctly
- [ ] All migrations applied (`alembic upgrade head`)
- [ ] Migration status verified (`alembic current`)
- [ ] Database connection tested from application
- [ ] Admin user created
- [ ] Squad template loaded (`software-dev-squad`)
- [ ] Database backup configured (automated daily backups)
- [ ] Backup restoration tested successfully

### ☑️ Security

- [ ] HTTPS/SSL certificate configured
- [ ] CORS restricted to specific origins
- [ ] Rate limiting enabled
- [ ] SQL injection protection verified (parameterized queries)
- [ ] XSS protection enabled (FastAPI defaults)
- [ ] CSRF protection configured (for forms)
- [ ] Password hashing using bcrypt
- [ ] JWT tokens using secure algorithm (HS256)
- [ ] Sensitive data not logged
- [ ] `.env` files in `.gitignore`
- [ ] No API keys in source code
- [ ] Security headers configured (HSTS, X-Content-Type-Options, etc.)

### ☑️ Testing

- [ ] All unit tests passing (`pytest tests/ -v`)
- [ ] Integration tests passing
- [ ] E2E test passing (`python test_mvp_e2e.py`)
- [ ] Code coverage > 30% (MVP minimum)
- [ ] Load testing completed
- [ ] API endpoints tested manually
- [ ] Authentication flow tested end-to-end
- [ ] Template system tested (create squad from template)
- [ ] Routing engine tested (3 test cases)
- [ ] Conversation flow tested

### ☑️ API & Documentation

- [ ] API documentation accessible (`/docs`)
- [ ] All endpoints return correct status codes
- [ ] Error responses properly formatted
- [ ] API versioning implemented (`/api/v1/`)
- [ ] Health check endpoint working (`/health`)
- [ ] OpenAPI/Swagger UI functional
- [ ] ReDoc documentation functional
- [ ] Postman collection created (optional)
- [ ] API rate limits documented

### ☑️ Performance

- [ ] Database queries optimized
- [ ] Database indexes created (via migrations)
- [ ] Connection pooling configured
- [ ] Redis caching enabled
- [ ] Response times < 500ms for key endpoints
- [ ] Static files served efficiently
- [ ] Gzip compression enabled
- [ ] N+1 queries eliminated
- [ ] Large payloads paginated

### ☑️ Monitoring & Logging

- [ ] Application logging configured (INFO level)
- [ ] Error tracking setup (Sentry, Rollbar, or similar)
- [ ] Performance monitoring configured (optional: New Relic, DataDog)
- [ ] Uptime monitoring setup (UptimeRobot, Pingdom)
- [ ] Log aggregation configured (optional)
- [ ] Alerts configured for critical errors
- [ ] Database performance monitoring enabled
- [ ] API metrics tracked
- [ ] Health check monitored

### ☑️ Infrastructure

- [ ] Production server/service configured
- [ ] Auto-scaling configured (if applicable)
- [ ] Load balancer configured (if using multiple instances)
- [ ] CDN configured for static files (optional)
- [ ] DNS configured correctly
- [ ] Firewall rules configured
- [ ] VPC/network security configured (if AWS/cloud)
- [ ] Resource limits set (CPU, memory, disk)
- [ ] Deployment pipeline configured
- [ ] Rollback procedure documented

### ☑️ Data & Compliance

- [ ] Data retention policy defined
- [ ] GDPR compliance reviewed (if EU users)
- [ ] Data encryption at rest enabled (database)
- [ ] Data encryption in transit enabled (HTTPS)
- [ ] User data deletion procedure implemented
- [ ] Terms of Service created
- [ ] Privacy Policy created
- [ ] Cookie policy created (if applicable)

### ☑️ Business Continuity

- [ ] Disaster recovery plan documented
- [ ] Backup restoration procedure tested
- [ ] Incident response plan created
- [ ] Emergency contacts documented
- [ ] On-call rotation defined (if team)
- [ ] Runbook created for common issues
- [ ] Rollback procedure documented
- [ ] Database failover tested (if using replicas)

---

## Post-Deployment Checklist

### ☑️ Immediate Verification (0-1 hour)

- [ ] Health check returns 200 OK
- [ ] Homepage loads successfully
- [ ] API documentation accessible (`/docs`)
- [ ] Can login with admin credentials
- [ ] Can create squad from template via CLI
- [ ] Can create squad from template via API
- [ ] All critical endpoints responding
- [ ] SSL certificate valid (no warnings)
- [ ] Logs showing no errors
- [ ] Database connections stable

### ☑️ First Day (0-24 hours)

- [ ] Monitor error logs every 2 hours
- [ ] Check response times (should be < 500ms)
- [ ] Monitor database connection count
- [ ] Track API key usage/costs (OpenAI, Anthropic)
- [ ] Verify automated backups completed
- [ ] Test user registration flow
- [ ] Test squad creation flow
- [ ] Monitor memory usage
- [ ] Check for any unusual activity

### ☑️ First Week (1-7 days)

- [ ] Review all error logs
- [ ] Optimize slow queries (if any)
- [ ] Check backup integrity
- [ ] Review API costs
- [ ] Monitor uptime (should be > 99%)
- [ ] Review security logs
- [ ] Check for dependency updates
- [ ] User feedback reviewed (if any beta users)
- [ ] Performance metrics analyzed
- [ ] Scale resources if needed

---

## Critical Endpoints to Test

### Authentication
- [ ] `POST /api/v1/auth/register` - User registration
- [ ] `POST /api/v1/auth/login` - User login
- [ ] `GET /api/v1/auth/me` - Get current user
- [ ] `POST /api/v1/auth/refresh` - Refresh token

### Templates
- [ ] `GET /api/v1/templates/` - List templates
- [ ] `GET /api/v1/templates/{id}` - Get template details
- [ ] `POST /api/v1/templates/{id}/apply` - Apply template

### Squads
- [ ] `GET /api/v1/squads/` - List squads
- [ ] `POST /api/v1/squads/` - Create squad
- [ ] `GET /api/v1/squads/{id}` - Get squad details

### Routing
- [ ] Routing engine correctly routes developer → tech lead
- [ ] Escalation chain works (3 levels verified)
- [ ] Cross-role routing works

### Conversations
- [ ] Can create conversation
- [ ] Can acknowledge conversation
- [ ] Can answer conversation
- [ ] Conversation timeline accurate

---

## Environment Variables Reference

### Required (Critical)
```
DATABASE_URL              # PostgreSQL connection string
REDIS_URL                 # Redis connection string
SECRET_KEY                # JWT signing key (32+ chars)
OPENAI_API_KEY           # OpenAI API key
ANTHROPIC_API_KEY        # Anthropic API key
ALLOWED_ORIGINS          # CORS allowed origins
DEBUG                    # Must be False in production
```

### Optional (Recommended)
```
PINECONE_API_KEY         # RAG/vector search
SENDGRID_API_KEY         # Email notifications
LOG_LEVEL                # Logging level (INFO)
RATE_LIMIT_ENABLED       # Enable rate limiting
```

---

## Quick Health Check Commands

```bash
# Test application
curl https://your-domain.com/health

# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Test Redis connection
redis-cli -u $REDIS_URL ping

# Test API authentication
curl -X POST https://your-domain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourdomain.com", "password": "password"}'

# Test template system
curl https://your-domain.com/api/v1/templates/ \
  -H "Authorization: Bearer $TOKEN"

# Run E2E test
DEBUG=False python test_mvp_e2e.py
```

---

## Performance Benchmarks

**Target Performance (MVP):**
- Health check: < 100ms
- Authentication: < 300ms
- List templates: < 200ms
- Apply template: < 2 seconds
- Create squad: < 1 second
- API endpoint average: < 500ms
- Database query average: < 100ms

**Resource Limits (MVP):**
- Database: 20 connections max
- Redis: 100MB memory
- Backend: 512MB-1GB RAM
- CPU: 1-2 cores

---

## Red Flags 🚨

**Stop deployment if you see:**
- ❌ Tests failing
- ❌ Migrations not applied
- ❌ `DEBUG=True` in production
- ❌ No SSL certificate
- ❌ API keys in source code
- ❌ No database backups configured
- ❌ CORS set to `*` (allow all)
- ❌ Default SECRET_KEY
- ❌ Database connection errors
- ❌ Redis connection errors

**Fix immediately before deploying!**

---

## Success Criteria ✅

**MVP is production-ready when:**
- ✅ All checklists above completed
- ✅ E2E test passes against production database
- ✅ Health check returns 200 OK
- ✅ Can create squad from template (< 30 seconds)
- ✅ All 6 agents instantiated correctly
- ✅ Routing engine works (3/3 tests pass)
- ✅ Escalation chain works (3 levels verified)
- ✅ Conversation flow works (question → ack → answer)
- ✅ Backups automated and tested
- ✅ Monitoring and alerts configured
- ✅ Security checklist 100% complete

---

## Quick Reference Links

- **Full Deployment Guide:** [MVP_DEPLOYMENT_GUIDE.md](./MVP_DEPLOYMENT_GUIDE.md)
- **Template System Guide:** [TEMPLATE_SYSTEM_GUIDE.md](./TEMPLATE_SYSTEM_GUIDE.md)
- **API Documentation:** `https://your-domain.com/docs`
- **Architecture Overview:** [docs/architecture/overview.md](./docs/architecture/overview.md)
- **E2E Test:** `python test_mvp_e2e.py`
- **CLI Tool:** `python -m backend.cli.apply_template --help`

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Developer** | _____________ | ______ | ________ |
| **QA/Test** | _____________ | ______ | ________ |
| **DevOps** | _____________ | ______ | ________ |
| **Product** | _____________ | ______ | ________ |

---

**🎉 Ready for production?** Mark all checkboxes, run the E2E test, and deploy!

**Need help?** See [MVP_DEPLOYMENT_GUIDE.md](./MVP_DEPLOYMENT_GUIDE.md) for detailed instructions.
