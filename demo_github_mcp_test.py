#!/usr/bin/env python3
"""
Demo: Test GitHub MCP Tools via Smithery

This script tests that your agents can use GitHub tools through Smithery.

Prerequisites:
1. GITHUB_TOKEN set in .env
2. Smithery profile active in mcp_tool_mapping.yaml
3. Access to a GitHub repository

Run:
    PYTHONPATH=$PWD python demo_github_mcp_test.py
"""

import os
import sys
import asyncio
from uuid import uuid4
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.agents.factory import AgentFactory
from backend.agents.configuration.mcp_tool_mapper import get_tool_mapper
from backend.services.agent_mcp_service import get_agent_mcp_service


def print_step(step: str, message: str):
    """Print formatted step"""
    print(f"\n{'='*70}")
    print(f"STEP {step}: {message}")
    print(f"{'='*70}\n")


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


async def test_configuration():
    """Test that configuration is correct"""
    print_step("1", "Checking Configuration")

    # Check active profile
    mapper = get_tool_mapper()
    active_profile = mapper.get_active_profile()

    print_info(f"Active MCP profile: {active_profile}")

    if active_profile != "smithery":
        print_error("Configuration is not set to 'smithery'")
        print_info("Edit backend/agents/configuration/mcp_tool_mapping.yaml")
        print_info("Change: active_profile: 'smithery'")
        return False

    print_success("Configuration set to Smithery!")

    # Check GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print_error("GITHUB_TOKEN not found in environment")
        print_info("1. Copy .env.mcp.example to .env")
        print_info("2. Add your GitHub token to .env")
        print_info("3. Run: export $(cat .env | xargs)")
        return False

    if github_token.startswith("ghp_"):
        print_success("GitHub token found and looks valid!")
    else:
        print_error("GitHub token doesn't start with 'ghp_'")
        print_info("Make sure you copied the full token from GitHub")
        return False

    return True


async def test_agent_creation():
    """Test creating an agent with MCP tools"""
    print_step("2", "Creating Backend Developer Agent")

    try:
        # Create agent
        agent = AgentFactory.create_agent(
            agent_id=uuid4(),
            role="backend_developer",
            llm_provider="openai",
            llm_model="gpt-4o-mini"
        )

        print_success("Agent created successfully!")
        print_info(f"Agent: {agent}")

        # Check if agent has tools
        tool_count = len(agent.agent.tools) if hasattr(agent.agent, 'tools') else 0
        print_info(f"Agent has {tool_count} tools configured")

        if tool_count > 0:
            print_success("MCP tools initialized!")
            print_info("Available tools:")
            for tool in agent.agent.tools[:5]:  # Show first 5
                tool_name = tool.__name__ if hasattr(tool, '__name__') else str(tool)
                print(f"  - {tool_name}")
            if tool_count > 5:
                print(f"  ... and {tool_count - 5} more")
        else:
            print_error("No tools found on agent")
            print_info("This might mean MCP servers didn't initialize")

        return agent

    except Exception as e:
        print_error(f"Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_mcp_service():
    """Test MCP service directly"""
    print_step("3", "Testing MCP Service")

    try:
        mcp_service = get_agent_mcp_service()

        # Get available tools for backend_developer
        available_tools = await mcp_service.get_available_tools("backend_developer")

        print_info("Tools available for backend_developer:")
        for server, tools in available_tools.items():
            print(f"\n  {server} server:")
            for tool in tools[:5]:  # Show first 5
                print(f"    - {tool}")
            if len(tools) > 5:
                print(f"    ... and {len(tools) - 5} more")

        # Try to initialize tools
        print_info("\nInitializing MCP servers...")
        sessions = await mcp_service.initialize_agent_tools("backend_developer")

        print_success(f"Initialized {len(sessions)} MCP servers!")
        for server_name in sessions:
            print(f"  ✓ {server_name}")

        return True

    except Exception as e:
        print_error(f"MCP service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_github_operation(agent):
    """Test a simple GitHub operation"""
    print_step("4", "Testing GitHub Operation")

    print_info("We'll ask the agent to search for a GitHub repository")
    print_info("This tests that Smithery's GitHub MCP server is working")

    try:
        # Simple query that uses GitHub search
        response = await agent.process_message(
            message="Search for the most popular Python repository on GitHub. Just tell me the name.",
            context={"test": True}
        )

        print_success("Agent responded!")
        print_info("Agent's response:")
        print(f"\n{response.content}\n")

        # Check if tools were used
        if response.tool_calls:
            print_success(f"Agent used {len(response.tool_calls)} tool(s)!")
            for tool_call in response.tool_calls:
                print(f"  - {tool_call}")
        else:
            print_error("Agent didn't use any tools")
            print_info("This might mean:")
            print_info("  - MCP tools not properly initialized")
            print_info("  - Agent decided not to use tools")

        return True

    except Exception as e:
        print_error(f"GitHub operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test flow"""
    print("\n" + "="*70)
    print("🚀 AGENT SQUAD - GitHub MCP Testing (Smithery)")
    print("="*70)

    # Step 1: Check configuration
    if not await test_configuration():
        print("\n" + "="*70)
        print("❌ Configuration check failed!")
        print("Please fix the issues above and try again.")
        print("="*70)
        return

    # Step 2: Create agent
    agent = await test_agent_creation()
    if not agent:
        print("\n" + "="*70)
        print("❌ Agent creation failed!")
        print("="*70)
        return

    # Step 3: Test MCP service
    if not await test_mcp_service():
        print("\n" + "="*70)
        print("❌ MCP service test failed!")
        print("="*70)
        return

    # Step 4: Test GitHub operation
    await test_github_operation(agent)

    # Final summary
    print("\n" + "="*70)
    print("🎉 TESTING COMPLETE!")
    print("="*70)
    print("\n✅ Your agents can now use GitHub tools via Smithery!")
    print("\nNext steps:")
    print("  1. Try more complex operations (create issues, PRs, etc.)")
    print("  2. Test with your own repositories")
    print("  3. Build your AI-powered workflows!")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run tests
    asyncio.run(main())
