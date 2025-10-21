#!/usr/bin/env python3
"""
Simple test script for real Jira integration.
Tests creating a ticket and retrieving it by ID.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, '/workspace/backend')

from backend.integrations.jira_service import JiraService
from backend.integrations.mcp.client import MCPClientManager


async def test_jira_integration():
    """Test creating and retrieving a Jira ticket."""

    print("=" * 60)
    print("🧪 Testing Real Jira Integration")
    print("=" * 60)
    print()

    # Get configuration from environment
    jira_url = os.getenv("JIRA_URL", "http://jira:8080")
    jira_username = os.getenv("JIRA_USERNAME", "admin@example.com")
    jira_token = os.getenv("JIRA_API_TOKEN", "admin123")

    print(f"📋 Configuration:")
    print(f"   URL: {jira_url}")
    print(f"   Username: {jira_username}")
    print(f"   Token: {'*' * len(jira_token)}")
    print()

    # Create MCP client
    print("🔌 Initializing MCP client...")
    mcp_client = MCPClientManager()

    # Create Jira service
    print("🔌 Initializing Jira service...")
    jira = JiraService(
        mcp_client,
        jira_url,
        jira_username,
        jira_token
    )

    try:
        # Initialize connection
        print("🔌 Connecting to Jira via MCP...")
        await jira.initialize()
        print("✅ Connected to Jira!")
        print()

        # Test 1: Search for existing issues
        print("=" * 60)
        print("📊 Test 1: Search for existing issues")
        print("=" * 60)
        try:
            print("🔍 Searching for issues (JQL: ORDER BY created DESC)...")
            search_result = await jira.search_issues(
                jql="ORDER BY created DESC",
                max_results=5
            )
            print(f"✅ Search completed!")
            print(f"   Result type: {type(search_result)}")
            print(f"   Result: {str(search_result)[:300]}...")
            print()
        except Exception as e:
            print(f"❌ Search failed: {e}")
            print()

        # Test 2: Create a new issue
        print("=" * 60)
        print("📝 Test 2: Create a new issue")
        print("=" * 60)
        try:
            print("📝 Creating test issue in project TEST...")
            create_result = await jira.create_issue(
                project="TEST",
                summary="Test Issue from Integration Test",
                description="This issue was created by automated integration testing to verify real Jira connectivity.",
                issue_type="Task",
                priority="Medium"
            )
            print(f"✅ Issue created!")
            print(f"   Result type: {type(create_result)}")
            print(f"   Result: {str(create_result)[:300]}...")
            print()

            # Try to extract issue key
            import json
            issue_key = None
            if isinstance(create_result, str):
                try:
                    data = json.loads(create_result)
                    issue_key = data.get("key")
                except:
                    pass
            else:
                issue_key = create_result.get("key") if hasattr(create_result, 'get') else None

            if issue_key:
                print(f"📌 Issue Key: {issue_key}")
                print()

                # Test 3: Get the issue we just created
                print("=" * 60)
                print("🔍 Test 3: Get issue by ID")
                print("=" * 60)
                try:
                    print(f"🔍 Fetching issue {issue_key}...")
                    get_result = await jira.get_issue(issue_key)
                    print(f"✅ Issue retrieved!")
                    print(f"   Result type: {type(get_result)}")
                    print(f"   Result: {str(get_result)[:300]}...")
                    print()

                    # Test 4: Add a comment
                    print("=" * 60)
                    print("💬 Test 4: Add comment to issue")
                    print("=" * 60)
                    try:
                        print(f"💬 Adding comment to {issue_key}...")
                        comment_result = await jira.add_comment(
                            issue_key,
                            "This is a test comment added by automated integration testing. ✅"
                        )
                        print(f"✅ Comment added!")
                        print(f"   Result: {str(comment_result)[:200]}...")
                        print()
                    except Exception as e:
                        print(f"❌ Comment failed: {e}")
                        print()

                except Exception as e:
                    print(f"❌ Get issue failed: {e}")
                    print()
            else:
                print("⚠️  Could not extract issue key from create result")
                print()

        except Exception as e:
            print(f"❌ Create issue failed: {e}")
            print()

        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print()
        print("🧹 Cleaning up...")
        await jira.cleanup()
        print("✅ Cleanup complete!")


if __name__ == "__main__":
    asyncio.run(test_jira_integration())
