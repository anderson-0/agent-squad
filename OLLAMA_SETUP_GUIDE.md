# Ollama Local LLM Setup Guide

**Status:** ✅ Ollama Support Added to Agent Squad
**Date:** November 3, 2025
**Benefit:** FREE local LLM for development and testing (no API keys required!)

---

## Why Ollama?

### ✅ Benefits
- **FREE** - No API costs, unlimited usage
- **Fast** - Runs locally on your machine
- **Private** - Data never leaves your machine
- **No Rate Limits** - Use as much as you need
- **No API Keys** - No sign-up required
- **Production-Ready** - Used by thousands of developers

### 🆚 Comparison with Other Options

| Feature | Ollama | Groq | OpenAI | Anthropic |
|---------|--------|------|--------|-----------|
| Cost | FREE | FREE (limited) | $0.10-0.50/test | $0.10-0.50/test |
| Speed | Very Fast (local) | Very Fast | Medium | Medium |
| Privacy | 100% local | Cloud | Cloud | Cloud |
| API Key | Not required | Required | Required | Required |
| Rate Limits | None | Yes (free tier) | Yes | Yes |
| Internet | Not required | Required | Required | Required |

**Recommendation**: Use Ollama for local development and testing, switch to cloud providers for production.

---

## Installation

### macOS

```bash
# Download and install from website (easiest)
open https://ollama.com/download

# Or use Homebrew
brew install ollama
```

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows

Download from: https://ollama.com/download

---

## Quick Start

### 1. Start Ollama Service

```bash
# Ollama runs as a background service
# On macOS/Linux, it usually starts automatically after installation

# To verify it's running:
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

### 2. Pull a Model

```bash
# Pull the default model (Llama 3.2, ~2GB)
ollama pull llama3.2

# Or choose a different model:
ollama pull llama3.2:1b  # Smaller, faster (1.3GB)
ollama pull llama3.1     # Larger, smarter (4.7GB)
ollama pull mistral      # Alternative model (4.1GB)
ollama pull codellama    # Specialized for code (3.8GB)
```

**Model Recommendations**:
- **llama3.2:1b** - Fastest, smallest (1.3GB) - Good for quick testing
- **llama3.2** - Balanced (2GB) - Default, good for most tasks
- **llama3.1** - Best quality (4.7GB) - Use when quality matters
- **codellama** - Code-focused (3.8GB) - Best for coding tasks

### 3. Verify Setup

```bash
# Test Ollama is working
ollama run llama3.2 "Hello, how are you?"

# You should see a response from the model
```

---

## Agent Squad Configuration

### 1. Update `.env` File

The `.env` file has been pre-configured with Ollama settings:

```bash
# Ollama (Local LLM - FREE, no API key required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**No changes needed!** These are the default values.

### 2. Verify Configuration

```bash
cd /Users/anderson/Documents/anderson-0/agent-squad/backend

# Check health endpoint (with Ollama running)
curl -s http://127.0.0.1:8000/api/v1/health/detailed | python3 -m json.tool
```

**Expected output**:
```json
{
  "components": {
    "llm_providers": {
      "openai": "not_configured",
      "anthropic": "not_configured",
      "groq": "not_configured",
      "ollama": "running"  // ✅ This means Ollama is working!
    }
  }
}
```

---

## Usage in Agent Squad

### Create an Agent with Ollama

```python
from backend.agents.factory import AgentFactory
from uuid import uuid4

# Create project manager with Ollama
agent_id = uuid4()
pm_agent = AgentFactory.create_agent(
    agent_id=agent_id,
    role="project_manager",
    llm_provider="ollama",           # Use Ollama
    llm_model="llama3.2",             # Model to use
    temperature=0.7
)

# Use the agent
response = await pm_agent.process_message(
    message="Create a plan for this feature",
    context={"feature": "User authentication"}
)

print(response.content)
```

### Supported Ollama Models

You can use any model available in Ollama:

```python
# Default (good for most tasks)
llm_model="llama3.2"

# Faster, smaller
llm_model="llama3.2:1b"

# Better quality
llm_model="llama3.1"

# Code-focused
llm_model="codellama"

# Uncensored model (for testing)
llm_model="mistral"
```

---

## Running Your First Test with Ollama

### Prerequisites
```bash
# 1. Ensure Ollama is running
curl http://localhost:11434/api/tags

# 2. Ensure model is pulled
ollama list | grep llama3.2

# 3. Ensure backend is running
curl http://127.0.0.1:8000/health
```

### Test Script

Create `test_ollama_agent.py`:

```python
import asyncio
from backend.agents.factory import AgentFactory
from uuid import uuid4

async def test_ollama():
    """Test agent with Ollama"""
    print("Creating agent with Ollama...")

    agent_id = uuid4()
    pm_agent = AgentFactory.create_agent(
        agent_id=agent_id,
        role="project_manager",
        llm_provider="ollama",
        llm_model="llama3.2",
        temperature=0.7
    )

    print("Agent created! Testing message processing...")

    response = await pm_agent.process_message(
        message="Create a simple task breakdown for implementing user authentication",
        context={}
    )

    print("\n=== Agent Response ===")
    print(response.content)
    print("\n=== Session Info ===")
    print(f"Session ID: {pm_agent.session_id}")
    print(f"Framework: {response.metadata.get('framework')}")
    print("\n✅ Test successful!")

if __name__ == "__main__":
    asyncio.run(test_ollama())
```

**Run it:**
```bash
cd /Users/anderson/Documents/anderson-0/agent-squad
PYTHONPATH=$PWD backend/.venv/bin/python test_ollama_agent.py
```

---

## Troubleshooting

### Issue: "ollama: not_running" in health check

**Solution:**
```bash
# Check if Ollama service is running
ps aux | grep ollama

# If not running, start it
ollama serve

# Or on macOS, if installed via app
open -a Ollama
```

### Issue: "Model not found"

**Solution:**
```bash
# List installed models
ollama list

# Pull the model if not present
ollama pull llama3.2
```

### Issue: "Connection refused" to localhost:11434

**Solution:**
```bash
# Check if Ollama is listening on port 11434
lsof -i :11434

# If not, restart Ollama
pkill ollama
ollama serve &
```

### Issue: Slow responses

**Solutions:**
1. Use a smaller model: `llama3.2:1b` instead of `llama3.1`
2. Ensure sufficient RAM (8GB minimum, 16GB recommended)
3. Close other applications to free up memory

### Issue: Out of memory

**Solutions:**
1. Use the smallest model: `ollama pull llama3.2:1b`
2. Close other applications
3. Restart Ollama: `pkill ollama && ollama serve &`

---

## Performance Tips

### 1. Model Selection
- **Quick Testing**: Use `llama3.2:1b` (fastest, 1.3GB)
- **Development**: Use `llama3.2` (balanced, 2GB)
- **Quality Testing**: Use `llama3.1` (best, 4.7GB)

### 2. Temperature Settings
```python
temperature=0.7   # Balanced (default)
temperature=0.3   # More focused, deterministic
temperature=1.0   # More creative, varied
```

### 3. Memory Management
```bash
# Check Ollama memory usage
ps aux | grep ollama

# Restart Ollama to free memory
pkill ollama
ollama serve &
```

### 4. Pre-load Models
```bash
# Pre-load a model into memory for faster first response
ollama run llama3.2 "test" > /dev/null
```

---

## Comparison: Ollama vs Cloud Providers

### Week 1 Testing (10-20 test workflows)

| Provider | Cost | Speed | Setup Time | Privacy |
|----------|------|-------|------------|---------|
| **Ollama** | **$0** | Very Fast | 5 minutes | 100% local |
| Groq | $0 (limited) | Very Fast | 2 minutes | Cloud |
| OpenAI | $2-5 | Medium | 2 minutes | Cloud |
| Anthropic | $2-5 | Medium | 2 minutes | Cloud |

### Recommendations

**For Local Development**: Use Ollama
- No costs
- Fast
- Private
- No internet required

**For Production**: Use OpenAI or Anthropic
- Better quality
- More reliable
- Better support
- Managed service

**For Free Testing**: Use Groq (backup to Ollama)
- Fast
- Free tier
- Cloud-based
- No local setup

---

## Next Steps

### After Ollama Setup

1. ✅ Verify Ollama is running
2. ✅ Pull llama3.2 model
3. ✅ Check health endpoint shows "ollama: running"
4. ✅ Run test script to verify agent creation
5. ✅ Proceed with Week 1 E2E testing

### Week 1 Testing with Ollama

You can now proceed with all Week 1 testing tasks:
- ✅ Day 1: Create and run first E2E test workflow
- ✅ Day 2: Test NATS message bus streaming
- ✅ Day 2: Test MCP tool integration
- ✅ Day 3: Test multi-agent workflows
- ✅ Day 3: Test dynamic task spawning
- ✅ Day 3: Test workflow branching

**All without any API costs!** 🎉

---

## Advanced Configuration

### Custom Ollama Port

If Ollama is running on a different port:

```bash
# In backend/.env
OLLAMA_BASE_URL=http://localhost:8080
```

### Remote Ollama Server

If Ollama is running on another machine:

```bash
# In backend/.env
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

### Multiple Models

Switch between models dynamically:

```python
# In your test script
agent = AgentFactory.create_agent(
    agent_id=uuid4(),
    role="backend_developer",
    llm_provider="ollama",
    llm_model="codellama",  # Use CodeLlama for coding tasks
    temperature=0.5
)
```

---

## Documentation

- **Ollama Website**: https://ollama.com
- **Ollama GitHub**: https://github.com/ollama/ollama
- **Ollama Models**: https://ollama.com/library
- **Agno Framework**: https://docs.agno.com

---

## Summary

✅ **Ollama support added to Agent Squad**
✅ **No API keys required**
✅ **FREE unlimited local LLM**
✅ **Ready for Week 1 testing**

**Installation:** 5 minutes
**Cost:** $0
**Setup:** Already configured in `.env`

**Next:** Install Ollama and start testing!

```bash
# Quick start (macOS)
brew install ollama
ollama pull llama3.2
curl http://localhost:11434/api/tags  # Verify

# Then run your tests!
```

---

**Status:** Ready to proceed with backend testing Week 1!
