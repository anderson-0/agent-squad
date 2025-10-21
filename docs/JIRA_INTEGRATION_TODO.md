# Jira/Confluence Integration - TODO (Postponed)

**Status**: ⏸️ Postponed - Will complete after Day 4
**Date Postponed**: October 13, 2025
**Reason**: Focusing on Day 4 (Advanced Orchestration) first, which doesn't require Jira/Confluence

---

## Current Situation

### What We Decided
- User initially wanted to use **local Docker Jira** for testing
- Jira container was running but not fully configured (needed setup wizard completion)
- **Changed plans**: Decided to use **Jira Cloud** instead of local Docker
- **Then changed plans again**: Postponed Jira entirely to focus on Day 4 first

### What's Already Implemented

#### ✅ Done:
1. **JiraService class** (`backend/integrations/jira_service.py`)
   - Methods for: create_issue, get_issue, search_issues, add_comment, update_status
   - Uses MCP client for API calls

2. **ConfluenceService class** (`backend/integrations/confluence_service.py`)
   - Methods for: create_page, get_page, search, update_page

3. **MCP Client Bug Fix**
   - Fixed context manager issue in `backend/integrations/mcp/client.py`
   - Properly handles stdio_client async context manager
   - Stores and cleans up stdio contexts on disconnect

4. **Docker Setup** (Optional - user preferred Cloud)
   - docker-compose.yml has Jira Software 9.12.0 and Confluence 8.5.0
   - PostgreSQL databases for both
   - Environment variables configured
   - Health checks in place

5. **Test Scripts Created**
   - `test_jira_simple.py` - MCP-based test (failed due to pydantic conflict)
   - `test_jira_direct.py` - Direct REST API test (not yet run)

6. **Integration Test Skeleton**
   - `backend/tests/test_integration/test_real_atlassian.py`
   - Tests for both Jira and Confluence
   - Uses environment variables for configuration

7. **Documentation**
   - `docs/LOCAL_ATLASSIAN_SETUP.md` - Complete Docker setup guide
   - `docs/ATLASSIAN_QUICKSTART.md` - Quick start guide
   - `docs/DOCKER_ATLASSIAN_COMPLETE.md` - Implementation summary

#### ⏸️ Pending:

1. **Jira Cloud Setup**
   - Need to create/use Jira Cloud account
   - Generate API token at: https://id.atlassian.com/manage-profile/security/api-tokens
   - Create TEST project in Jira Cloud

2. **Environment Configuration**
   - Update `.env` with:
     ```
     JIRA_URL=https://yoursite.atlassian.net
     JIRA_USERNAME=your-email@example.com
     JIRA_API_TOKEN=your-api-token-here
     ```

3. **Testing**
   - Run `test_jira_direct.py` to verify API access
   - Test operations: create ticket, get ticket, add comment, update status
   - Verify mcp-atlassian works or stick with direct REST API

4. **Confluence Setup** (Optional)
   - Use same Atlassian Cloud account
   - Same API token works for both
   - Update CONFLUENCE_* env vars

5. **Webhook Integration**
   - Implement webhook handler in `backend/api/v1/endpoints/webhooks.py`
   - Handle Jira ticket events
   - Trigger task execution on ticket updates

---

## Known Issues

### Issue 1: mcp-atlassian Pydantic Conflict
**Problem**: `mcp-atlassian` package has incompatibility with newer Pydantic versions
```
TypeError: cannot specify both default and default_factory
```
**Workaround**: Created `test_jira_direct.py` that uses REST API directly
**Permanent Fix**: Either downgrade Pydantic or use direct REST API approach

### Issue 2: Local Docker Jira Not Fully Setup
**Problem**: Jira container running but returns 503 (Service Unavailable)
**Cause**: Setup wizard not completed - no admin user created
**Solution Options**:
1. Complete setup wizard at http://localhost:8080 (takes 10 minutes)
2. Use Jira Cloud instead (preferred by user)

---

## When Returning to This Task

### Step 1: Jira Cloud Setup (5-10 minutes)
1. Create/login to Atlassian account
2. Create API token: https://id.atlassian.com/manage-profile/security/api-tokens
3. Note your Jira URL: `https://yoursite.atlassian.net`
4. Create project with key "TEST"

### Step 2: Update Environment
```bash
# Edit .env file
JIRA_URL=https://yoursite.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=ATATT3xFfGF0...your-token...
```

### Step 3: Update Docker Compose
```bash
# Restart backend with new env vars
docker-compose up -d backend
```

### Step 4: Test Integration
```bash
# Test direct REST API
docker exec agent-squad-backend python3 /workspace/test_jira_direct.py

# Or test via Python script
docker exec agent-squad-backend python3 /workspace/test_jira_simple.py
```

### Step 5: Run Integration Tests
```bash
docker exec agent-squad-backend python3 -m pytest backend/tests/test_integration/test_real_atlassian.py -v
```

### Step 6: Implement Webhooks
- Create endpoint to receive Jira webhooks
- Parse ticket events
- Trigger agent squad execution
- Update ticket status after completion

---

## Files to Review When Returning

1. **Implementation**:
   - `backend/integrations/jira_service.py` - Main Jira service
   - `backend/integrations/confluence_service.py` - Confluence service
   - `backend/integrations/mcp/client.py` - MCP client (already fixed)

2. **Tests**:
   - `test_jira_direct.py` - Direct REST API test
   - `test_jira_simple.py` - MCP-based test
   - `backend/tests/test_integration/test_real_atlassian.py` - Integration tests

3. **Configuration**:
   - `.env` - Environment variables
   - `docker-compose.yml` - Docker setup
   - `.env.example` - Example configuration

4. **Documentation**:
   - `docs/PHASE_4_PLAN.md` - Overall plan (updated with this note)
   - `docs/LOCAL_ATLASSIAN_SETUP.md` - Docker setup guide
   - This file - Complete context

---

## Decision Log

1. **Oct 13, 2025 16:30** - Started with local Docker Jira
2. **Oct 13, 2025 16:45** - Fixed MCP client context manager bug
3. **Oct 13, 2025 17:00** - Discovered Jira 503 error (setup incomplete)
4. **Oct 13, 2025 17:15** - User decided to switch to Jira Cloud
5. **Oct 13, 2025 17:20** - User asked about API token generation
6. **Oct 13, 2025 17:25** - **DECISION: Postpone Jira, do Day 4 first**
   - Reason: Day 4 doesn't require Jira/Confluence
   - Can use existing Git integration for orchestration testing
   - Jira setup takes time, want to make progress elsewhere

---

## Quick Resume Checklist

When you return to this task, you need:
- [ ] Jira Cloud URL
- [ ] Jira Cloud email
- [ ] Jira Cloud API token
- [ ] TEST project created in Jira
- [ ] .env file updated
- [ ] Backend container restarted
- [ ] test_jira_direct.py tested successfully
- [ ] Integration tests passing
- [ ] (Optional) Confluence configured
- [ ] (Optional) Webhooks implemented

---

**Remember**: This is postponed, not abandoned. We have solid foundation code ready - just need Cloud credentials and testing!
