#!/bin/bash
set -e

echo "🔍 Agent Squad - Setup Verification Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        return 1
    fi
}

check_service() {
    local url=$1
    local name=$2

    if curl -f -s -o /dev/null $url; then
        echo -e "${GREEN}✓${NC} $name is running at $url"
        return 0
    else
        echo -e "${RED}✗${NC} $name is not responding at $url"
        return 1
    fi
}

# Check prerequisites
echo "📦 Checking Prerequisites..."
echo ""

check_command docker
check_command docker-compose || check_command "docker compose"
check_command node
check_command python3
check_command git

echo ""
echo "🐳 Checking Docker Services..."
echo ""

# Check if docker-compose services are running
if docker ps | grep -q agent-squad-postgres; then
    echo -e "${GREEN}✓${NC} PostgreSQL container is running"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL container is not running"
fi

if docker ps | grep -q agent-squad-redis; then
    echo -e "${GREEN}✓${NC} Redis container is running"
else
    echo -e "${YELLOW}⚠${NC} Redis container is not running"
fi

if docker ps | grep -q agent-squad-backend; then
    echo -e "${GREEN}✓${NC} Backend container is running"
else
    echo -e "${YELLOW}⚠${NC} Backend container is not running"
fi

if docker ps | grep -q agent-squad-frontend; then
    echo -e "${GREEN}✓${NC} Frontend container is running"
else
    echo -e "${YELLOW}⚠${NC} Frontend container is not running"
fi

echo ""
echo "🌐 Checking Service Endpoints..."
echo ""

# Wait a moment for services to be ready
sleep 2

# Check service endpoints
check_service "http://localhost:8000/health" "Backend Health Check" || true
check_service "http://localhost:8000/docs" "Backend API Docs" || true
check_service "http://localhost:3000" "Frontend" || true

# Check database connectivity
echo ""
echo "🗄️  Checking Database..."
echo ""

if docker exec agent-squad-postgres pg_isready -U postgres &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL is accepting connections"
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL is not accepting connections"
fi

# Check Redis
echo ""
echo "🔴 Checking Redis..."
echo ""

if docker exec agent-squad-redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✓${NC} Redis is responding to PING"
else
    echo -e "${YELLOW}⚠${NC} Redis is not responding"
fi

echo ""
echo "=========================================="
echo "✨ Verification Complete!"
echo ""
echo "If all checks passed, your setup is ready!"
echo "If some checks failed, try:"
echo "  1. Run: docker-compose up"
echo "  2. Wait for all services to start"
echo "  3. Run this script again"
echo ""
