#!/bin/bash

# Agent Squad Setup Script
# One-command setup for development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    local all_good=true

    # Check Docker
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
        print_success "Docker is installed (version $DOCKER_VERSION)"
    else
        print_error "Docker is not installed"
        print_info "  Install from: https://www.docker.com/get-started"
        all_good=false
    fi

    # Check Docker Compose
    if command_exists docker-compose || docker compose version &> /dev/null; then
        if command_exists docker-compose; then
            COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f4 | cut -d ',' -f1)
        else
            COMPOSE_VERSION=$(docker compose version --short)
        fi
        print_success "Docker Compose is installed (version $COMPOSE_VERSION)"
    else
        print_error "Docker Compose is not installed"
        print_info "  Install from: https://docs.docker.com/compose/install/"
        all_good=false
    fi

    # Check Docker daemon
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        print_info "  Start Docker Desktop or run: sudo systemctl start docker"
        all_good=false
    fi

    if [ "$all_good" = false ]; then
        print_error "Prerequisites check failed. Please install missing dependencies."
        exit 1
    fi

    echo ""
}

# Setup environment file
setup_env() {
    print_header "Setting Up Environment"

    if [ -f "backend/.env" ]; then
        print_warning "backend/.env already exists, skipping..."
    else
        print_info "Creating backend/.env from .env.example..."
        cp backend/.env.example backend/.env
        print_success "Created backend/.env"
        print_warning "Remember to update API keys in backend/.env for production!"
    fi

    echo ""
}

# Start services
start_services() {
    print_header "Starting Services"

    print_info "Building Docker images..."
    docker-compose build

    print_success "Images built successfully"
    echo ""

    print_info "Starting services with docker-compose..."
    docker-compose up -d

    print_success "Services started"
    echo ""
}

# Wait for services to be healthy
wait_for_services() {
    print_header "Waiting for Services to Start"

    print_info "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
            print_success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done

    print_info "Waiting for Redis..."
    for i in {1..30}; do
        if docker-compose exec -T redis redis-cli ping &> /dev/null; then
            print_success "Redis is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Redis failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done

    print_info "Waiting for NATS..."
    for i in {1..30}; do
        if curl -s http://localhost:8222/healthz &> /dev/null; then
            print_success "NATS is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "NATS failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done

    print_info "Waiting for Backend API..."
    for i in {1..60}; do
        if curl -s http://localhost:8000/api/v1/health &> /dev/null; then
            print_success "Backend API is ready"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "Backend API failed to start within 60 seconds"
            docker-compose logs backend
            exit 1
        fi
        sleep 1
    done

    print_info "Waiting for Frontend..."
    for i in {1..60}; do
        if curl -s http://localhost:3000 &> /dev/null; then
            print_success "Frontend is ready"
            break
        fi
        if [ $i -eq 60 ]; then
            print_error "Frontend failed to start within 60 seconds"
            docker-compose logs frontend
            exit 1
        fi
        sleep 1
    done

    echo ""
}

# Display status
display_status() {
    print_header "Setup Complete!"

    echo -e "${GREEN}🚀 Agent Squad is now running!${NC}"
    echo ""
    echo "Services:"
    echo -e "  ${BLUE}Frontend:${NC}  http://localhost:3000"
    echo -e "  ${BLUE}Backend:${NC}   http://localhost:8000"
    echo -e "  ${BLUE}API Docs:${NC}  http://localhost:8000/docs"
    echo -e "  ${BLUE}Health:${NC}    http://localhost:8000/api/v1/health"
    echo ""
    echo "Infrastructure:"
    echo -e "  ${BLUE}PostgreSQL:${NC} localhost:5432"
    echo -e "  ${BLUE}Redis:${NC}      localhost:6379"
    echo -e "  ${BLUE}NATS:${NC}       localhost:4222 (monitoring: localhost:8222)"
    echo ""
    echo "Useful Commands:"
    echo -e "  ${YELLOW}docker-compose logs -f${NC}              # View all logs"
    echo -e "  ${YELLOW}docker-compose logs -f backend${NC}      # View backend logs"
    echo -e "  ${YELLOW}docker-compose logs -f frontend${NC}     # View frontend logs"
    echo -e "  ${YELLOW}docker-compose ps${NC}                    # View service status"
    echo -e "  ${YELLOW}docker-compose down${NC}                  # Stop all services"
    echo -e "  ${YELLOW}docker-compose down -v${NC}               # Stop and remove volumes"
    echo ""
    echo "Next Steps:"
    echo -e "  1. Open ${BLUE}http://localhost:3000${NC} in your browser"
    echo -e "  2. Update API keys in ${YELLOW}backend/.env${NC} (OpenAI, Anthropic, etc.)"
    echo -e "  3. Install Ollama (optional): ${BLUE}https://ollama.com/download${NC}"
    echo -e "  4. Read the docs: ${BLUE}docs/QUICK_START.md${NC}"
    echo ""
}

# Main execution
main() {
    clear

    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║                                           ║"
    echo "║        Agent Squad Setup Script          ║"
    echo "║                                           ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"

    # Change to project root
    cd "$(dirname "$0")/.."

    check_prerequisites
    setup_env
    start_services
    wait_for_services
    display_status

    print_success "Setup complete!"
}

# Run main function
main
