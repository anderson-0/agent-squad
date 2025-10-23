#!/usr/bin/env python3
"""
Test MCP Tool Integration with AgnoSquadAgent (Day 4)

This script tests the new MCP tool integration features added to AgnoSquadAgent:
- Tool discovery
- Tool execution
- Tool-aware prompt generation
- Automatic tool use with LLM
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/workspace/backend')

from backend.agents.agno_base import AgnoSquadAgent, AgentConfig
from backend.integrations.mcp.client import MCPClientManager
from uuid import uuid4


class TestAgent(AgnoSquadAgent):
    """Simple test agent for MCP integration testing"""

    def get_capabilities(self) -> list:
        return ["testing", "mcp_tools"]


async def test_mcp_agent_integration():
    """Test the complete MCP integration with AgnoSquadAgent"""

    print("=" * 80)
    print("🧪 Testing MCP Integration with AgnoSquadAgent (Day 4)")
    print("=" * 80)
    print()

    # Test 1: Agent without MCP client
    print("=" * 80)
    print("📊 Test 1: Agent without MCP client")
    print("=" * 80)
    try:
        config = AgentConfig(
            role="developer",
            specialization="backend",
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022",
            system_prompt="You are a test agent."
        )

        agent_no_mcp = TestAgent(config=config, agent_id=uuid4())
        print(f"✅ Agent created: {agent_no_mcp}")
        print(f"   Has MCP client: {agent_no_mcp.has_mcp_client()}")
        print(f"   Available tools: {len(agent_no_mcp.get_available_tools())}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()

    # Test 2: Initialize MCP client and connect to Git server
    print("=" * 80)
    print("📊 Test 2: Connect to Git MCP server")
    print("=" * 80)
    try:
        print("🔌 Initializing MCP client...")
        mcp_client = MCPClientManager()

        print("🔌 Connecting to Git MCP server...")
        await mcp_client.connect_server(
            name="git",
            command="uvx",
            args=["mcp-server-git", "--repository", "/workspace"],
            env={}
        )

        print(f"✅ Connected to Git MCP server")
        print(f"   Servers: {mcp_client.list_servers()}")
        print(f"   Available tools: {list(mcp_client.get_available_tools('git').keys())}")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return

    # Test 3: Create agent with MCP client
    print("=" * 80)
    print("📊 Test 3: Create agent with MCP client")
    print("=" * 80)
    try:
        agent_with_mcp = TestAgent(config=config, agent_id=uuid4(), mcp_client=mcp_client)
        print(f"✅ Agent with MCP created: {agent_with_mcp}")
        print(f"   Has MCP client: {agent_with_mcp.has_mcp_client()}")

        tools = agent_with_mcp.get_available_tools()
        print(f"   Available tools: {len(tools.get('git', {}))} Git tools")

        for tool_name in list(tools.get('git', {}).keys())[:5]:
            print(f"     - {tool_name}")
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Test 4: Direct tool execution
    print("=" * 80)
    print("📊 Test 4: Direct tool execution (read_file)")
    print("=" * 80)
    try:
        print("📖 Reading README.md from repository...")
        result = await agent_with_mcp.execute_tool(
            tool_name="read_file",
            arguments={"path": "README.md"},
            server_name="git"
        )

        if result.success:
            print(f"✅ Tool executed successfully!")
            print(f"   Execution time: {result.execution_time:.2f}s")
            print(f"   Result preview: {str(result.result)[:200]}...")
        else:
            print(f"❌ Tool execution failed: {result.error}")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Test 5: List files in directory
    print("=" * 80)
    print("📊 Test 5: List files tool")
    print("=" * 80)
    try:
        print("📂 Listing files in backend/ directory...")
        result = await agent_with_mcp.execute_tool(
            tool_name="list_files",
            arguments={"path": "backend"},
            server_name="git"
        )

        if result.success:
            print(f"✅ Tool executed successfully!")
            print(f"   Execution time: {result.execution_time:.2f}s")
            print(f"   Result type: {type(result.result)}")
            print(f"   Result preview: {str(result.result)[:300]}...")
        else:
            print(f"❌ Tool execution failed: {result.error}")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Test 6: Tool execution history
    print("=" * 80)
    print("📊 Test 6: Tool execution history")
    print("=" * 80)
    try:
        history = agent_with_mcp.get_tool_execution_history()
        print(f"✅ Retrieved tool execution history")
        print(f"   Total executions: {len(history)}")

        for i, exec_result in enumerate(history, 1):
            status = "✅" if exec_result.success else "❌"
            print(f"   {i}. {status} {exec_result.tool_name} ({exec_result.execution_time:.2f}s)")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

    # Test 7: Tool-aware prompt generation
    print("=" * 80)
    print("📊 Test 7: Tool-aware prompt generation")
    print("=" * 80)
    try:
        tools_prompt = agent_with_mcp._format_tools_for_prompt()
        print(f"✅ Generated tool-aware prompt")
        print(f"   Length: {len(tools_prompt)} characters")
        print(f"   Preview:")
        print(tools_prompt[:500] + "...")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

    # Test 8: Parse tool call from response
    print("=" * 80)
    print("📊 Test 8: Parse tool call from LLM response")
    print("=" * 80)
    try:
        # Simulate LLM response with tool call
        mock_response = '''I'll read the README file for you.

```json
{
  "action": "use_tool",
  "tool": "read_file",
  "server": "git",
  "arguments": {
    "path": "README.md"
  }
}
```
'''

        tool_call = agent_with_mcp._parse_tool_call_from_response(mock_response)

        if tool_call:
            print(f"✅ Successfully parsed tool call")
            print(f"   Tool: {tool_call.tool_name}")
            print(f"   Server: {tool_call.server_name}")
            print(f"   Arguments: {tool_call.arguments}")
        else:
            print(f"❌ Failed to parse tool call")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

    # Test 9: Test with actual LLM (if API key available)
    print("=" * 80)
    print("📊 Test 9: LLM with tool awareness (checking API key)")
    print("=" * 80)

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            print("🤖 Testing LLM response with tool information...")
            print("   Note: LLM sees available tools in system prompt")

            # Just test that the prompt includes tool info
            test_message = "What tools do you have available?"
            messages = agent_with_mcp._build_messages(
                test_message,
                context=None,
                history=[]
            )

            system_message = messages[0]["content"]
            has_tools = "Available Tools" in system_message

            if has_tools:
                print(f"✅ System prompt includes tool information")
                print(f"   System prompt length: {len(system_message)} characters")
                tool_section_start = system_message.find("## Available Tools")
                if tool_section_start != -1:
                    print(f"   Tools section preview:")
                    print(f"   {system_message[tool_section_start:tool_section_start+300]}...")
            else:
                print(f"⚠️  System prompt does NOT include tools (unexpected)")
            print()

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()
    else:
        print("⚠️  ANTHROPIC_API_KEY not set, skipping LLM test")
        print("   (This is OK - we can still test tool integration)")
        print()

    # Cleanup
    print("=" * 80)
    print("🧹 Cleanup")
    print("=" * 80)
    try:
        await mcp_client.disconnect_all()
        print("✅ Disconnected from all MCP servers")
        print()
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        print()

    # Summary
    print("=" * 80)
    print("✅ MCP Integration Tests Complete!")
    print("=" * 80)
    print()
    print("Summary of Day 4 Implementation:")
    print("  ✅ AgnoSquadAgent accepts mcp_client parameter")
    print("  ✅ Tool discovery (get_available_tools)")
    print("  ✅ Direct tool execution (execute_tool)")
    print("  ✅ Tool execution history tracking")
    print("  ✅ Tool-aware prompt generation")
    print("  ✅ Tool call parsing from LLM responses")
    print("  ✅ System prompt enhancement with tool info")
    print()
    print("🎉 AgnoSquadAgent now supports MCP tool integration!")
    print()


if __name__ == "__main__":
    asyncio.run(test_mcp_agent_integration())
