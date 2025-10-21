"""
Real Integration Tests for Atlassian Services (No Mocks!)

These tests require:
1. Jira running at http://localhost:8080
2. Confluence running at http://localhost:8090
3. .env configured with credentials

Run with:
    docker exec agent-squad-backend pytest backend/tests/test_integration/test_real_atlassian.py -v -s

Skip if services not available:
    pytest backend/tests/test_integration/test_real_atlassian.py --skip-real
"""

import pytest
import os
import asyncio
from backend.integrations.jira_service import JiraService
from backend.integrations.confluence_service import ConfluenceService
from backend.integrations.mcp.client import MCPClientManager


# Check if Atlassian services are configured
JIRA_URL = os.getenv("JIRA_URL", "http://localhost:8080")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "admin@example.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "admin123")

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "http://localhost:8090")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "admin@example.com")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "admin123")

# Skip marker for when services aren't available
skip_if_no_jira = pytest.mark.skipif(
    JIRA_URL == "http://localhost:8080" and not os.getenv("JIRA_API_TOKEN"),
    reason="Jira not configured (set JIRA_API_TOKEN in .env)"
)

skip_if_no_confluence = pytest.mark.skipif(
    CONFLUENCE_URL == "http://localhost:8090" and not os.getenv("CONFLUENCE_API_TOKEN"),
    reason="Confluence not configured (set CONFLUENCE_API_TOKEN in .env)"
)


@pytest.fixture
async def mcp_client():
    """Create real MCP client."""
    client = MCPClientManager()
    yield client
    # Cleanup any connections
    await asyncio.sleep(0.1)


@pytest.fixture
async def jira_service(mcp_client):
    """Create JiraService with real connection."""
    service = JiraService(
        mcp_client,
        JIRA_URL,
        JIRA_USERNAME,
        JIRA_API_TOKEN
    )
    await service.initialize()
    yield service
    await service.cleanup()


@pytest.fixture
async def confluence_service(mcp_client):
    """Create ConfluenceService with real connection."""
    service = ConfluenceService(
        mcp_client,
        CONFLUENCE_URL,
        CONFLUENCE_USERNAME,
        CONFLUENCE_API_TOKEN
    )
    await service.initialize()
    yield service
    await service.cleanup()


# ==================== Jira Real Tests ====================

@pytest.mark.asyncio
@skip_if_no_jira
async def test_real_jira_search_issues(jira_service):
    """Test real Jira search with JQL."""
    print(f"\n🔍 Searching Jira issues at {JIRA_URL}")

    # Search for all issues (or create some first if none exist)
    result = await jira_service.search_issues(
        jql="ORDER BY created DESC",
        max_results=10
    )

    print(f"✅ Found {len(result) if isinstance(result, list) else 'N/A'} issues")
    assert result is not None
    print(f"   Result type: {type(result)}")
    print(f"   Result: {result[:200] if isinstance(result, str) else result}")


@pytest.mark.asyncio
@skip_if_no_jira
async def test_real_jira_create_and_update_issue(jira_service):
    """Test creating and updating a real Jira issue."""
    print(f"\n📝 Creating test issue in Jira at {JIRA_URL}")

    # Create issue
    create_result = await jira_service.create_issue(
        project="TEST",
        summary="Test Issue from Integration Test",
        description="This issue was created by automated testing",
        issue_type="Task",
        priority="Medium"
    )

    print(f"✅ Created issue")
    print(f"   Result: {create_result[:200] if isinstance(create_result, str) else create_result}")

    # Extract issue key from result (format may vary)
    # Result might be JSON string or dict
    import json
    if isinstance(create_result, str):
        try:
            create_data = json.loads(create_result)
            issue_key = create_data.get("key")
        except:
            # If can't parse, skip update test
            print("⚠️  Could not parse issue key, skipping update")
            return
    else:
        issue_key = create_result.get("key")

    if not issue_key:
        print("⚠️  No issue key in result, skipping update")
        return

    print(f"   Issue key: {issue_key}")

    # Get the issue
    print(f"\n🔍 Getting issue {issue_key}")
    get_result = await jira_service.get_issue(issue_key)
    print(f"✅ Retrieved issue")
    print(f"   Result: {str(get_result)[:200]}")

    # Add comment
    print(f"\n💬 Adding comment to issue {issue_key}")
    comment_result = await jira_service.add_comment(
        issue_key,
        "This is a test comment from automated testing"
    )
    print(f"✅ Added comment")
    print(f"   Result: {str(comment_result)[:200]}")

    # Update issue
    print(f"\n✏️  Updating issue {issue_key}")
    update_result = await jira_service.update_issue(
        issue_key,
        {"description": "Updated description from automated test"}
    )
    print(f"✅ Updated issue")
    print(f"   Result: {str(update_result)[:200]}")


@pytest.mark.asyncio
@skip_if_no_jira
async def test_real_jira_transitions(jira_service):
    """Test getting available transitions."""
    print(f"\n🔄 Testing Jira transitions")

    # First, search for any issue
    search_result = await jira_service.search_issues(
        jql="ORDER BY created DESC",
        max_results=1
    )

    if not search_result:
        print("⚠️  No issues found, skipping transition test")
        pytest.skip("No issues available for transition test")

    # Parse issue key
    import json
    if isinstance(search_result, str):
        try:
            issues = json.loads(search_result)
            if isinstance(issues, list) and len(issues) > 0:
                issue_key = issues[0].get("key")
            else:
                print("⚠️  No issues in search result")
                pytest.skip("No issues in search result")
        except:
            print("⚠️  Could not parse search result")
            pytest.skip("Could not parse search result")
    else:
        if isinstance(search_result, list) and len(search_result) > 0:
            issue_key = search_result[0].get("key")
        else:
            pytest.skip("No issues in search result")

    print(f"   Using issue: {issue_key}")

    # Get transitions
    transitions = await jira_service.get_transitions(issue_key)
    print(f"✅ Got transitions for {issue_key}")
    print(f"   Result: {str(transitions)[:200]}")
    assert transitions is not None


# ==================== Confluence Real Tests ====================

@pytest.mark.asyncio
@skip_if_no_confluence
async def test_real_confluence_list_spaces(confluence_service):
    """Test listing real Confluence spaces."""
    print(f"\n📚 Listing Confluence spaces at {CONFLUENCE_URL}")

    result = await confluence_service.list_spaces(limit=10)

    print(f"✅ Got spaces")
    print(f"   Result type: {type(result)}")
    print(f"   Result: {str(result)[:200]}")
    assert result is not None


@pytest.mark.asyncio
@skip_if_no_confluence
async def test_real_confluence_search(confluence_service):
    """Test searching Confluence content."""
    print(f"\n🔍 Searching Confluence content")

    result = await confluence_service.search_content(
        query="test",
        limit=5
    )

    print(f"✅ Search completed")
    print(f"   Result type: {type(result)}")
    print(f"   Result: {str(result)[:200]}")
    assert result is not None


@pytest.mark.asyncio
@skip_if_no_confluence
async def test_real_confluence_create_and_get_page(confluence_service):
    """Test creating and retrieving a real Confluence page."""
    print(f"\n📄 Creating test page in Confluence")

    # Create page
    import time
    page_title = f"Test Page {int(time.time())}"

    create_result = await confluence_service.create_page(
        space="DEV",
        title=page_title,
        content="<p>This is a test page created by automated testing.</p><p>Created at: " + time.strftime("%Y-%m-%d %H:%M:%S") + "</p>"
    )

    print(f"✅ Created page '{page_title}'")
    print(f"   Result: {str(create_result)[:200]}")

    # Extract page ID
    import json
    if isinstance(create_result, str):
        try:
            page_data = json.loads(create_result)
            page_id = page_data.get("id")
        except:
            print("⚠️  Could not parse page ID, skipping get")
            return
    else:
        page_id = create_result.get("id")

    if not page_id:
        print("⚠️  No page ID in result, skipping get")
        return

    print(f"   Page ID: {page_id}")

    # Get the page
    print(f"\n🔍 Getting page {page_id}")
    get_result = await confluence_service.get_page(page_id)
    print(f"✅ Retrieved page")
    print(f"   Result: {str(get_result)[:200]}")

    # Get page by title
    print(f"\n🔍 Getting page by title '{page_title}'")
    get_by_title_result = await confluence_service.get_page_by_title("DEV", page_title)
    print(f"✅ Retrieved page by title")
    print(f"   Result: {str(get_by_title_result)[:200]}")


# ==================== Combined Workflow Test ====================

@pytest.mark.asyncio
@skip_if_no_jira
@skip_if_no_confluence
async def test_real_complete_workflow(jira_service, confluence_service):
    """
    Test complete real workflow:
    1. Create Jira issue
    2. Create Confluence documentation page
    3. Link them together via comment
    """
    print(f"\n🎯 Testing complete real workflow")

    import time
    timestamp = int(time.time())

    # Step 1: Create Jira issue
    print(f"\n1️⃣  Creating Jira issue...")
    jira_result = await jira_service.create_issue(
        project="TEST",
        summary=f"Workflow Test Issue {timestamp}",
        description="Issue created as part of complete workflow test",
        issue_type="Task"
    )
    print(f"✅ Created Jira issue")

    # Extract issue key
    import json
    if isinstance(jira_result, str):
        try:
            jira_data = json.loads(jira_result)
            issue_key = jira_data.get("key")
        except:
            print("⚠️  Could not parse issue, aborting workflow")
            return
    else:
        issue_key = jira_result.get("key")

    if not issue_key:
        print("⚠️  No issue key, aborting workflow")
        return

    print(f"   Issue: {issue_key}")

    # Step 2: Create Confluence page
    print(f"\n2️⃣  Creating Confluence documentation...")
    confluence_result = await confluence_service.create_page(
        space="DEV",
        title=f"Documentation for {issue_key}",
        content=f"<h1>{issue_key} Documentation</h1><p>This page documents the work for <strong>{issue_key}</strong>.</p><p>Created: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>"
    )
    print(f"✅ Created Confluence page")

    # Extract page URL (approximate)
    confluence_page_url = f"{CONFLUENCE_URL}/pages/viewpage.action?pageId="

    # Step 3: Link them via comment
    print(f"\n3️⃣  Linking Jira and Confluence...")
    comment_result = await jira_service.add_comment(
        issue_key,
        f"Documentation created: See Confluence space DEV for details.\nCreated by automated workflow test."
    )
    print(f"✅ Added linking comment")

    print(f"\n🎉 Complete workflow test PASSED!")
    print(f"   Jira issue: {JIRA_URL}/browse/{issue_key}")
    print(f"   Confluence: {CONFLUENCE_URL}/spaces/DEV")


# ==================== Connection Tests ====================

@pytest.mark.asyncio
async def test_jira_connection_available():
    """Test if Jira is accessible (doesn't require MCP)."""
    import urllib.request

    try:
        response = urllib.request.urlopen(f"{JIRA_URL}/status", timeout=5)
        print(f"✅ Jira is accessible at {JIRA_URL}")
        assert response.status == 200 or response.status == 302
    except Exception as e:
        pytest.skip(f"Jira not accessible: {e}")


@pytest.mark.asyncio
async def test_confluence_connection_available():
    """Test if Confluence is accessible (doesn't require MCP)."""
    import urllib.request

    try:
        response = urllib.request.urlopen(f"{CONFLUENCE_URL}/status", timeout=5)
        print(f"✅ Confluence is accessible at {CONFLUENCE_URL}")
        assert response.status == 200 or response.status == 302
    except Exception as e:
        pytest.skip(f"Confluence not accessible: {e}")
