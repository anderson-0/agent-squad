#!/bin/bash
#
# Security Audit Script
#
# Runs comprehensive security checks on the Agent Squad codebase
#
# Requirements:
#   - bandit (Python security linter)
#   - safety (dependency vulnerability scanner)
#   - uv or pip (package manager)
#
# Usage:
#   ./scripts/security_audit.sh

set -e

echo "🔒 Starting Security Audit for Agent Squad"
echo "=========================================="
echo ""

# Check if in correct directory
if [ ! -d "backend" ]; then
    echo "❌ Error: Must be run from project root"
    exit 1
fi

# Check for virtual environment
if [ ! -d "backend/.venv" ]; then
    echo "❌ Error: Virtual environment not found at backend/.venv"
    echo "   Run: cd backend && uv venv"
    exit 1
fi

# Activate virtual environment
PYTHON="backend/.venv/bin/python"
PIP="backend/.venv/bin/pip"
BANDIT="backend/.venv/bin/bandit"
SAFETY="backend/.venv/bin/safety"

# Ensure tools are installed
echo "📦 Checking security tools..."
if [ ! -f "$BANDIT" ] || [ ! -f "$SAFETY" ]; then
    echo "   Installing bandit and safety..."
    cd backend && uv pip install bandit safety && cd ..
fi

echo "✅ Security tools ready"
echo ""

# Create reports directory
mkdir -p reports/security
REPORT_DIR="reports/security"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# ============================================================================
# 1. BANDIT - Python Code Security Scan
# ============================================================================

echo "🔍 Running Bandit (Python Security Linter)..."
echo "   Scanning for:"
echo "   - SQL injection vulnerabilities"
echo "   - Hardcoded secrets"
echo "   - Weak cryptography"
echo "   - Command injection"
echo "   - Path traversal"
echo "   - And more..."
echo ""

$BANDIT -r backend \
    -ll \
    --exit-zero \
    -f json \
    -o "$REPORT_DIR/bandit_${TIMESTAMP}.json" \
    2>&1 | tee "$REPORT_DIR/bandit_${TIMESTAMP}.txt"

# Also generate human-readable report
$BANDIT -r backend \
    -ll \
    --exit-zero \
    -f txt \
    2>&1 > "$REPORT_DIR/bandit_${TIMESTAMP}_readable.txt"

echo "✅ Bandit scan complete"
echo "   Reports: $REPORT_DIR/bandit_${TIMESTAMP}.*"
echo ""

# ============================================================================
# 2. SAFETY - Dependency Vulnerability Scan
# ============================================================================

echo "🔍 Running Safety (Dependency Vulnerability Scanner)..."
echo "   Checking for known vulnerabilities in:"
echo "   - Python dependencies"
echo "   - Transitive dependencies"
echo ""

$SAFETY check \
    --file backend/requirements.txt \
    --output json \
    > "$REPORT_DIR/safety_${TIMESTAMP}.json" 2>&1 || true

$SAFETY check \
    --file backend/requirements.txt \
    --output text \
    > "$REPORT_DIR/safety_${TIMESTAMP}.txt" 2>&1 || true

echo "✅ Safety scan complete"
echo "   Reports: $REPORT_DIR/safety_${TIMESTAMP}.*"
echo ""

# ============================================================================
# 3. CUSTOM SECURITY CHECKS
# ============================================================================

echo "🔍 Running Custom Security Checks..."

# Check for hardcoded secrets (basic grep)
echo "   Checking for potential hardcoded secrets..."
grep -r -n -E "(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]" backend \
    --exclude-dir=".venv" \
    --exclude-dir="__pycache__" \
    --exclude="*.pyc" \
    > "$REPORT_DIR/potential_secrets_${TIMESTAMP}.txt" 2>/dev/null || echo "   ✅ No obvious hardcoded secrets found"

# Check for debug mode in production files
echo "   Checking for debug mode enabled..."
grep -r -n "DEBUG\s*=\s*True" backend \
    --exclude-dir=".venv" \
    --exclude-dir="__pycache__" \
    > "$REPORT_DIR/debug_mode_${TIMESTAMP}.txt" 2>/dev/null || echo "   ✅ No hardcoded DEBUG=True found"

# Check for print statements (should use logging)
echo "   Checking for print statements (should use logging)..."
grep -r -n "print(" backend \
    --exclude-dir=".venv" \
    --exclude-dir="__pycache__" \
    --exclude-dir="alembic" \
    | head -20 > "$REPORT_DIR/print_statements_${TIMESTAMP}.txt" 2>/dev/null || true

# Check for TODOs related to security
echo "   Checking for security TODOs..."
grep -r -n -i "TODO.*secur" backend \
    --exclude-dir=".venv" \
    --exclude-dir="__pycache__" \
    > "$REPORT_DIR/security_todos_${TIMESTAMP}.txt" 2>/dev/null || echo "   ✅ No security TODOs found"

echo "✅ Custom checks complete"
echo ""

# ============================================================================
# 4. GENERATE SUMMARY REPORT
# ============================================================================

echo "📊 Generating Summary Report..."

SUMMARY_FILE="$REPORT_DIR/SUMMARY_${TIMESTAMP}.md"

cat > "$SUMMARY_FILE" <<EOF
# Security Audit Summary

**Date**: $(date)
**Project**: Agent Squad
**Scan Type**: Automated Security Audit

## Tools Used

1. **Bandit** - Python Code Security Linter
2. **Safety** - Dependency Vulnerability Scanner
3. **Custom Checks** - Hardcoded secrets, debug mode, etc.

## Results

### 1. Bandit Results

\`\`\`bash
# View full report:
cat $REPORT_DIR/bandit_${TIMESTAMP}_readable.txt
\`\`\`

EOF

# Count Bandit issues by severity
if [ -f "$REPORT_DIR/bandit_${TIMESTAMP}.json" ]; then
    HIGH=$(grep -o '"severity": "HIGH"' "$REPORT_DIR/bandit_${TIMESTAMP}.json" 2>/dev/null | wc -l || echo "0")
    MEDIUM=$(grep -o '"severity": "MEDIUM"' "$REPORT_DIR/bandit_${TIMESTAMP}.json" 2>/dev/null | wc -l || echo "0")
    LOW=$(grep -o '"severity": "LOW"' "$REPORT_DIR/bandit_${TIMESTAMP}.json" 2>/dev/null | wc -l || echo "0")

    cat >> "$SUMMARY_FILE" <<EOF
**Issues Found:**
- 🔴 High Severity: $HIGH
- 🟡 Medium Severity: $MEDIUM
- 🟢 Low Severity: $LOW

EOF
fi

cat >> "$SUMMARY_FILE" <<EOF
### 2. Safety Results

\`\`\`bash
# View full report:
cat $REPORT_DIR/safety_${TIMESTAMP}.txt
\`\`\`

EOF

# Count Safety vulnerabilities
if [ -f "$REPORT_DIR/safety_${TIMESTAMP}.txt" ]; then
    VULNS=$(grep -c "vulnerability" "$REPORT_DIR/safety_${TIMESTAMP}.txt" 2>/dev/null || echo "0")
    cat >> "$SUMMARY_FILE" <<EOF
**Vulnerabilities Found:** $VULNS

EOF
fi

cat >> "$SUMMARY_FILE" <<EOF
### 3. Custom Checks

- Potential Secrets: See \`potential_secrets_${TIMESTAMP}.txt\`
- Debug Mode: See \`debug_mode_${TIMESTAMP}.txt\`
- Print Statements: See \`print_statements_${TIMESTAMP}.txt\`
- Security TODOs: See \`security_todos_${TIMESTAMP}.txt\`

## Recommendations

### High Priority
1. Fix all HIGH severity Bandit issues
2. Update dependencies with known vulnerabilities
3. Remove any hardcoded secrets
4. Ensure DEBUG=False in production

### Medium Priority
1. Fix MEDIUM severity Bandit issues
2. Replace print() with logging
3. Address security TODOs

### Low Priority
1. Review LOW severity Bandit issues
2. Consider additional security hardening

## Next Steps

1. Review detailed reports in \`$REPORT_DIR/\`
2. Create GitHub issues for each high/medium severity finding
3. Implement fixes
4. Re-run audit to verify fixes
5. Schedule regular security audits (weekly/monthly)

## Compliance Checklist

- [ ] No hardcoded secrets
- [ ] No SQL injection vulnerabilities
- [ ] No command injection vulnerabilities
- [ ] All dependencies up-to-date
- [ ] No known vulnerabilities in dependencies
- [ ] Proper authentication and authorization
- [ ] Input validation on all endpoints
- [ ] HTTPS enforced in production
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Logging and monitoring in place
- [ ] Error messages don't leak sensitive data

## Report Files

All reports saved to: \`$REPORT_DIR/\`

- \`bandit_${TIMESTAMP}.json\` - Bandit JSON report
- \`bandit_${TIMESTAMP}_readable.txt\` - Bandit human-readable report
- \`safety_${TIMESTAMP}.json\` - Safety JSON report
- \`safety_${TIMESTAMP}.txt\` - Safety human-readable report
- \`potential_secrets_${TIMESTAMP}.txt\` - Hardcoded secrets check
- \`debug_mode_${TIMESTAMP}.txt\` - Debug mode check
- \`print_statements_${TIMESTAMP}.txt\` - Print statement check
- \`security_todos_${TIMESTAMP}.txt\` - Security TODOs
- \`SUMMARY_${TIMESTAMP}.md\` - This summary report

EOF

echo "✅ Summary report generated: $SUMMARY_FILE"
echo ""

# ============================================================================
# FINAL OUTPUT
# ============================================================================

echo "=========================================="
echo "🎉 Security Audit Complete!"
echo "=========================================="
echo ""
echo "📊 Summary Report: $SUMMARY_FILE"
echo "📁 All Reports: $REPORT_DIR/"
echo ""
echo "Next Steps:"
echo "  1. Review summary: cat $SUMMARY_FILE"
echo "  2. Check detailed reports in $REPORT_DIR/"
echo "  3. Fix high/medium severity issues"
echo "  4. Re-run audit to verify fixes"
echo ""
