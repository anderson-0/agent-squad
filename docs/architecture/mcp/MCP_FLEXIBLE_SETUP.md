# MCP Flexible Setup - Best of Both Worlds

## 🎯 The Solution: Flexible Configuration

You asked about Smithery pricing (10k requests/month limit), so we implemented **both options**:

1. **Self-Hosted** (DEFAULT) ✅ - Free, unlimited, production-ready
2. **Smithery** (OPTIONAL) - Easier setup, good for quick testing

**Easy switch between them** - just change one line in config!

---

## 📋 Quick Comparison

| Feature | Self-Hosted (Default) | Smithery (Optional) |
|---------|----------------------|---------------------|
| **Cost** | **$0/month** ✅ | $0 for <10k req/month |
| **Request Limit** | **Unlimited** ✅ | 10,000/month free |
| **Setup Time** | 15 minutes | 5 minutes ✅ |
| **Control** | **Full control** ✅ | Limited |
| **Privacy** | **100% yours** ✅ | Proxied through Smithery |
| **Maintenance** | You manage | They manage ✅ |
| **Production** | **✅ Recommended** | ⚠️ Watch limits |
| **Development** | ✅ Great | ✅ Great |

**Our Recommendation**:
- **Production**: Self-hosted (unlimited, free)
- **Quick Testing**: Either works

---

## 🚀 Setup Instructions

### Option 1: Self-Hosted (Recommended)

**Setup Time**: 15 minutes
**Cost**: $0/month forever
**Best For**: Production apps, unlimited scale

```bash
# 1. Install MCP servers
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-github
# Jira auto-installs via npx

# 2. Set credentials
cp .env.mcp.example .env
# Edit .env with your tokens

# 3. Verify config (default is self-hosted)
grep "active_profile" backend/agents/configuration/mcp_tool_mapping.yaml
# Should show: active_profile: "self_hosted"

# Done! Ready to use.
```

**Full Guide**: See `MCP_SETUP_GUIDE.md`

### Option 2: Smithery (Quick Testing)

**Setup Time**: 5 minutes
**Cost**: Free for <10k requests/month
**Best For**: Quick testing, demos

```bash
# 1. Install ONLY Git server (GitHub/Jira hosted by Smithery)
npm install -g @modelcontextprotocol/server-git

# 2. Set credentials
cp .env.mcp.example .env
# Edit .env with your tokens

# 3. Switch to Smithery profile
# Edit backend/agents/configuration/mcp_tool_mapping.yaml
# Change: active_profile: "smithery"

# Done! Smithery hosts GitHub/Jira for you.
```

**Full Guide**: See `MCP_SETUP_SMITHERY.md`

---

## 🔄 Switching Between Profiles

### Method 1: Edit Config File (Persistent)

Edit `backend/agents/configuration/mcp_tool_mapping.yaml`:

```yaml
# Change this line:
active_profile: "self_hosted"  # or "smithery"
```

Restart your application.

### Method 2: Programmatically (Runtime)

```python
from backend.agents.configuration.mcp_tool_mapper import get_tool_mapper

mapper = get_tool_mapper()

# Check current profile
print(mapper.get_active_profile())  # "self_hosted"

# Switch to Smithery (for testing)
mapper.set_active_profile("smithery")

# Switch back to self-hosted (for production)
mapper.set_active_profile("self_hosted")
```

### Method 3: Environment Variable (Future)

```bash
# Set in .env
MCP_PROFILE=smithery  # or self_hosted

# Or export
export MCP_PROFILE=self_hosted
```

---

## 📊 When to Use Each

### Use Self-Hosted When:

✅ **In production** - Unlimited requests
✅ **High volume** - >10k requests/month
✅ **Need full control** - Custom configurations
✅ **Privacy matters** - Data stays with you
✅ **Long-term** - No vendor dependency

**Example**: Your production AI agent making 100k API calls/day

### Use Smithery When:

✅ **Quick prototyping** - Faster setup
✅ **Low volume** - <10k requests/month
✅ **Demo/testing** - Short-term usage
✅ **Zero maintenance** - They handle updates

**Example**: Weekend hackathon, quick POC demo

---

## 💰 Cost Analysis

### Scenario 1: Low Volume App (<10k requests/month)

| Approach | Cost | Setup | Maintenance |
|----------|------|-------|-------------|
| Self-Hosted | **$0** | 15 min | 1 hour/month |
| Smithery | **$0** | 5 min | 0 hours |

**Winner**: Either works! Smithery slightly easier.

### Scenario 2: Medium Volume (10k-100k requests/month)

| Approach | Cost | Setup | Maintenance |
|----------|------|-------|-------------|
| Self-Hosted | **$0** | 15 min | 1 hour/month |
| Smithery | **$?** | 5 min | 0 hours |

**Winner**: Self-hosted (unlimited free)

### Scenario 3: High Volume (>100k requests/month)

| Approach | Cost | Setup | Maintenance |
|----------|------|-------|-------------|
| Self-Hosted | **$0** | 15 min | 2 hours/month |
| Smithery | **$$** | 5 min | 0 hours |

**Winner**: Self-hosted (much cheaper)

---

## 🛠️ Technical Details

### Configuration Structure

```yaml
# mcp_tool_mapping.yaml

active_profile: "self_hosted"  # ← Switch here

server_profiles:
  self_hosted:  # ← Free unlimited
    github:
      command: "uvx"
      args: ["mcp-server-github"]

  smithery:  # ← 10k free/month
    github:
      command: "npx"
      args: ["-y", "@smithery/cli", "run", "@smithery-ai/github"]

# Roles remain the same (agent permissions)
roles:
  backend_developer:
    tools: [...]
```

### How It Works

1. **Profile Selection**: System reads `active_profile`
2. **Server Config**: Loads config from selected profile
3. **Tool Initialization**: Creates MCP connections
4. **Agent Usage**: Agents use tools transparently

**Agents don't know which profile is active** - they just use tools!

---

## 📈 Migration Path

### Starting with Smithery (Easy Testing)

```
Week 1: Smithery
├── Quick setup (5 min)
├── Test all features
├── Validate functionality
└── Under 10k requests (free)

Week 2-3: Production Prep
├── Install self-hosted servers (15 min)
├── Test in staging
├── Switch profile to "self_hosted"
└── Deploy to production

Week 4+: Production
├── Unlimited requests
├── $0 monthly cost
├── Full control
└── Scale infinitely
```

### Starting with Self-Hosted (Production Ready)

```
Day 1: Self-Hosted
├── Install servers (15 min)
├── Configure credentials
├── Test functionality
└── Deploy to production

Forever:
├── Unlimited requests
├── $0 monthly cost
├── No vendor lock-in
└── Production-ready
```

---

## 🎯 Our Recommendation

### For Most Users: **Start with Self-Hosted**

**Why?**
1. **No surprises** - No unexpected costs
2. **Unlimited scale** - Grow without limits
3. **Production-ready** - Use same setup dev→prod
4. **15 minutes** - Setup is still quick
5. **Learning** - Understand the infrastructure

**Setup**: Follow `MCP_SETUP_GUIDE.md`

### For Quick Testing: **Smithery is Fine**

**Why?**
1. **5 minutes** - Fastest setup
2. **Good for POC** - Prove the concept
3. **Easy switch** - Can move to self-hosted later
4. **10k free** - Enough for initial testing

**Setup**: Follow `MCP_SETUP_SMITHERY.md`

---

## 🔒 Security Considerations

### Self-Hosted

✅ **Data privacy** - Tokens never leave your infra
✅ **Full control** - You manage everything
✅ **Audit trail** - Complete visibility
✅ **Compliance** - Meets strict requirements

### Smithery

⚠️ **Proxied requests** - Goes through Smithery
✅ **Secure transport** - HTTPS encrypted
⚠️ **Third-party** - Trust Smithery's security
⚠️ **Shared infra** - Multi-tenant platform

**For sensitive data**: Self-hosted is safer

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `MCP_SETUP_GUIDE.md` | **Self-hosted setup** (recommended) |
| `MCP_SETUP_SMITHERY.md` | Smithery setup (optional) |
| `MCP_TOOL_MAPPING.md` | Design & architecture |
| `MCP_FLEXIBLE_SETUP.md` | This document |
| `SMITHERY_MIGRATION.md` | Before/after comparison |

---

## ❓ FAQ

**Q: Can I use both profiles?**
A: Not simultaneously. Pick one, but easy to switch.

**Q: What's the switching cost?**
A: Just change one line in config + restart. ~1 minute.

**Q: Does switching affect my agents?**
A: No! Agents use tools the same way regardless of profile.

**Q: Can I have custom profiles?**
A: Yes! Add your own profile in `server_profiles` section.

**Q: What about other MCP servers?**
A: Easy to add! Both Smithery and self-hosted support custom servers.

**Q: Smithery vs official MCP servers?**
A: Official servers = self-host. Smithery = hosted version. We support both!

---

## 🎉 Summary

**You get the best of both worlds:**

✅ **Self-Hosted** (default)
- Free unlimited usage
- Production-ready
- Full control
- 15 minutes setup

✅ **Smithery** (optional)
- Quick testing
- Zero maintenance
- 5 minutes setup
- 10k free/month

✅ **Easy Switch**
- Change one line in config
- No code changes needed
- Agents work identically

**Our recommendation**: **Self-hosted for production**, Smithery optional for quick testing.

**Next Steps**:
1. Choose your approach
2. Follow the setup guide
3. Test with your agents
4. Build amazing AI workflows!

**Questions?** Check the troubleshooting sections in setup guides.
