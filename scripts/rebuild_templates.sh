#!/bin/bash
#
# E2B Template Rebuild Automation Script
#
# This script automates weekly template rebuilds to ensure:
# - Latest security patches
# - Up-to-date git installation
# - Fresh template snapshots
#
# Usage:
#   ./scripts/rebuild_templates.sh [--update-config]
#
# Options:
#   --update-config   Automatically update .env with new template ID
#
# Exit codes:
#   0 - Success
#   1 - Template creation failed
#   2 - Configuration update failed
#   3 - Requirements not met (E2B_API_KEY missing)
#
# Schedule this script to run weekly via cron or CI/CD:
#   cron: 0 2 * * 0 /path/to/rebuild_templates.sh
#   GitHub Actions: schedule: cron: '0 2 * * 0'

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$SCRIPT_DIR/create_e2b_template.py"
ENV_FILE="$PROJECT_ROOT/backend/.env"
UPDATE_CONFIG=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --update-config)
            UPDATE_CONFIG=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo "================================================"
echo "E2B Template Rebuild Automation"
echo "================================================"
echo ""

# Check prerequisites
if [ -z "$E2B_API_KEY" ]; then
    echo -e "${RED}ERROR: E2B_API_KEY environment variable not set${NC}"
    echo "Please set E2B_API_KEY before running this script"
    exit 3
fi

# Check Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}ERROR: Python script not found: $PYTHON_SCRIPT${NC}"
    exit 1
fi

# Run template creation
echo -e "${YELLOW}Step 1: Creating new E2B template...${NC}"
echo ""

TEMPLATE_OUTPUT=$(python3 "$PYTHON_SCRIPT" 2>&1)
TEMPLATE_EXIT_CODE=$?

if [ $TEMPLATE_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}ERROR: Template creation failed${NC}"
    echo "$TEMPLATE_OUTPUT"
    exit 1
fi

echo "$TEMPLATE_OUTPUT"

# Extract template ID from output
# Note: This assumes the Python script outputs "Template ID: <id>" or similar
TEMPLATE_ID=$(echo "$TEMPLATE_OUTPUT" | grep -oP 'Template ID: \K[a-zA-Z0-9_-]+' || echo "")

if [ -z "$TEMPLATE_ID" ]; then
    echo -e "${YELLOW}WARNING: Could not extract template ID from output${NC}"
    echo "Manual configuration update required"
else
    echo ""
    echo -e "${GREEN}✓ Template created successfully: $TEMPLATE_ID${NC}"

    # Update configuration if requested
    if [ "$UPDATE_CONFIG" = true ]; then
        echo ""
        echo -e "${YELLOW}Step 2: Updating configuration...${NC}"

        if [ -f "$ENV_FILE" ]; then
            # Backup existing .env
            cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"

            # Update E2B_TEMPLATE_ID in .env
            if grep -q "^E2B_TEMPLATE_ID=" "$ENV_FILE"; then
                # Replace existing value
                sed -i "s/^E2B_TEMPLATE_ID=.*/E2B_TEMPLATE_ID=$TEMPLATE_ID/" "$ENV_FILE"
                echo -e "${GREEN}✓ Updated E2B_TEMPLATE_ID in $ENV_FILE${NC}"
            else
                # Add new line
                echo "E2B_TEMPLATE_ID=$TEMPLATE_ID" >> "$ENV_FILE"
                echo -e "${GREEN}✓ Added E2B_TEMPLATE_ID to $ENV_FILE${NC}"
            fi
        else
            echo -e "${YELLOW}WARNING: .env file not found: $ENV_FILE${NC}"
            echo "Please manually set E2B_TEMPLATE_ID=$TEMPLATE_ID"
        fi
    else
        echo ""
        echo -e "${YELLOW}Manual configuration update required:${NC}"
        echo "Add to $ENV_FILE:"
        echo "E2B_TEMPLATE_ID=$TEMPLATE_ID"
    fi
fi

echo ""
echo "================================================"
echo -e "${GREEN}Template rebuild complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Test new template with test operations"
echo "2. Monitor sandbox init times (<200ms expected)"
echo "3. Deploy to production after validation"
echo ""

exit 0
