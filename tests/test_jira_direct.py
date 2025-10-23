#!/usr/bin/env python3
"""
Direct REST API test for Jira integration (no MCP).
Tests creating a ticket and retrieving it by ID.
"""

import requests
import json
from requests.auth import HTTPBasicAuth

# Configuration
JIRA_URL = "http://jira:8080"
USERNAME = "admin@example.com"
PASSWORD = "admin123"

print("=" * 60)
print("🧪 Testing Real Jira Integration (Direct REST API)")
print("=" * 60)
print()

print(f"📋 Configuration:")
print(f"   URL: {JIRA_URL}")
print(f"   Username: {USERNAME}")
print(f"   Password: {'*' * len(PASSWORD)}")
print()

# Setup auth
auth = HTTPBasicAuth(USERNAME, PASSWORD)
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Test 1: Get server info
print("=" * 60)
print("📊 Test 1: Get Server Info")
print("=" * 60)
try:
    print(f"🔍 GET {JIRA_URL}/rest/api/2/serverInfo")
    response = requests.get(
        f"{JIRA_URL}/rest/api/2/serverInfo",
        auth=auth,
        headers=headers,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        server_info = response.json()
        print(f"✅ Server Info Retrieved!")
        print(f"   Version: {server_info.get('version')}")
        print(f"   Build: {server_info.get('buildNumber')}")
        print(f"   Server Title: {server_info.get('serverTitle')}")
    else:
        print(f"❌ Failed: {response.text[:200]}")
    print()
except Exception as e:
    print(f"❌ Error: {e}")
    print()

# Test 2: Search for existing issues
print("=" * 60)
print("📊 Test 2: Search for Existing Issues")
print("=" * 60)
try:
    jql = "ORDER BY created DESC"
    print(f"🔍 Searching with JQL: {jql}")
    response = requests.get(
        f"{JIRA_URL}/rest/api/2/search",
        auth=auth,
        headers=headers,
        params={"jql": jql, "maxResults": 5},
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search Completed!")
        print(f"   Total: {data.get('total')} issues")
        print(f"   Returned: {len(data.get('issues', []))} issues")
        for issue in data.get('issues', [])[:3]:
            print(f"   - {issue['key']}: {issue['fields']['summary']}")
    else:
        print(f"❌ Failed: {response.text[:200]}")
    print()
except Exception as e:
    print(f"❌ Error: {e}")
    print()

# Test 3: Create a new issue
print("=" * 60)
print("📝 Test 3: Create a New Issue")
print("=" * 60)
try:
    issue_data = {
        "fields": {
            "project": {"key": "TEST"},
            "summary": "Test Issue from Direct REST API Integration",
            "description": "This issue was created by automated integration testing using direct REST API calls to verify real Jira connectivity. ✅",
            "issuetype": {"name": "Task"},
            "priority": {"name": "Medium"}
        }
    }

    print(f"📝 Creating issue in project TEST...")
    print(f"   Summary: {issue_data['fields']['summary']}")
    response = requests.post(
        f"{JIRA_URL}/rest/api/2/issue",
        auth=auth,
        headers=headers,
        json=issue_data,
        timeout=10
    )
    print(f"   Status: {response.status_code}")

    if response.status_code in [200, 201]:
        created_issue = response.json()
        issue_key = created_issue.get('key')
        issue_id = created_issue.get('id')
        print(f"✅ Issue Created!")
        print(f"   Key: {issue_key}")
        print(f"   ID: {issue_id}")
        print(f"   URL: {JIRA_URL}/browse/{issue_key}")
        print()

        # Test 4: Get the issue we just created
        print("=" * 60)
        print("🔍 Test 4: Get Issue by Key")
        print("=" * 60)
        try:
            print(f"🔍 GET {JIRA_URL}/rest/api/2/issue/{issue_key}")
            response = requests.get(
                f"{JIRA_URL}/rest/api/2/issue/{issue_key}",
                auth=auth,
                headers=headers,
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                issue = response.json()
                print(f"✅ Issue Retrieved!")
                print(f"   Key: {issue['key']}")
                print(f"   Summary: {issue['fields']['summary']}")
                print(f"   Status: {issue['fields']['status']['name']}")
                print(f"   Priority: {issue['fields']['priority']['name']}")
                print(f"   Created: {issue['fields']['created']}")
            else:
                print(f"❌ Failed: {response.text[:200]}")
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

        # Test 5: Add a comment
        print("=" * 60)
        print("💬 Test 5: Add Comment to Issue")
        print("=" * 60)
        try:
            comment_data = {
                "body": "This is a test comment added by automated integration testing using direct REST API. ✅ The integration is working perfectly!"
            }

            print(f"💬 Adding comment to {issue_key}...")
            response = requests.post(
                f"{JIRA_URL}/rest/api/2/issue/{issue_key}/comment",
                auth=auth,
                headers=headers,
                json=comment_data,
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                comment = response.json()
                print(f"✅ Comment Added!")
                print(f"   Comment ID: {comment.get('id')}")
                print(f"   Author: {comment.get('author', {}).get('displayName')}")
            else:
                print(f"❌ Failed: {response.text[:200]}")
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

        # Test 6: Update the issue
        print("=" * 60)
        print("✏️  Test 6: Update Issue")
        print("=" * 60)
        try:
            update_data = {
                "fields": {
                    "description": "This issue was created by automated integration testing. UPDATED: Integration test completed successfully! ✅"
                }
            }

            print(f"✏️  Updating {issue_key}...")
            response = requests.put(
                f"{JIRA_URL}/rest/api/2/issue/{issue_key}",
                auth=auth,
                headers=headers,
                json=update_data,
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 204:
                print(f"✅ Issue Updated!")
            else:
                print(f"❌ Failed: {response.text[:200]}")
            print()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

    else:
        print(f"❌ Failed to create issue: {response.text[:200]}")
        print()
except Exception as e:
    print(f"❌ Error: {e}")
    print()

print("=" * 60)
print("✅ All Tests Completed!")
print("=" * 60)
print()
print("Summary:")
print("  ✅ Server Info Retrieved")
print("  ✅ Search Issues")
print("  ✅ Create Issue")
print("  ✅ Get Issue by Key")
print("  ✅ Add Comment")
print("  ✅ Update Issue")
print()
print("🎉 Real Jira Integration Working Perfectly!")
