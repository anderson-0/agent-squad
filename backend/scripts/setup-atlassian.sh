#!/bin/bash
# Setup script for local Jira and Confluence Docker instances

set -e

echo "=========================================="
echo "Atlassian Local Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Jira and Confluence Docker containers...${NC}"
echo "This will take 5-10 minutes on first run (large images to download)"
echo ""

# Start Jira and Confluence
docker-compose up -d jira-postgres confluence-postgres jira confluence

echo ""
echo -e "${GREEN}✅ Containers started!${NC}"
echo ""
echo "Waiting for services to be ready..."
echo "(Jira and Confluence take 3-5 minutes to initialize)"
echo ""

# Function to check if service is ready
check_service() {
    local url=$1
    local name=$2
    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 10
    done

    echo -e "${RED}❌ $name failed to start after 10 minutes${NC}"
    return 1
}

# Wait for Jira
echo -n "Waiting for Jira"
check_service "http://localhost:8080/status" "Jira"

# Wait for Confluence
echo -n "Waiting for Confluence"
check_service "http://localhost:8090/status" "Confluence"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Set up Jira (http://localhost:8080)"
echo "   - Choose: 'Set it up for me'"
echo "   - License: 'Generate evaluation license'"
echo "   - Create admin account:"
echo "     • Username: admin"
echo "     • Password: admin123"
echo "     • Email: admin@example.com"
echo ""
echo "2. Set up Confluence (http://localhost:8090)"
echo "   - Choose: 'Production Installation'"
echo "   - License: 'Get an evaluation license'"
echo "   - Database: Already configured (PostgreSQL)"
echo "   - Create admin account (same as Jira):"
echo "     • Username: admin"
echo "     • Password: admin123"
echo "     • Email: admin@example.com"
echo ""
echo "3. Create API Token for admin user:"
echo "   - In Jira: Profile > Account Settings > Security > API Tokens"
echo "   - Create token named 'agent-squad'"
echo "   - Copy token to .env file"
echo ""
echo "4. Update .env file:"
echo "   JIRA_URL=http://localhost:8080"
echo "   JIRA_USERNAME=admin@example.com"
echo "   JIRA_API_TOKEN=your_token_here"
echo "   CONFLUENCE_URL=http://localhost:8090"
echo "   CONFLUENCE_USERNAME=admin@example.com"
echo "   CONFLUENCE_API_TOKEN=your_token_here"
echo ""
echo "5. Run tests:"
echo "   docker exec agent-squad-backend pytest backend/tests/test_jira_service.py -v"
echo ""
echo "=========================================="
echo -e "${YELLOW}Access URLs:${NC}"
echo "  Jira:       http://localhost:8080"
echo "  Confluence: http://localhost:8090"
echo "=========================================="
