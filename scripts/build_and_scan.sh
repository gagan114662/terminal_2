#!/bin/bash

# TermNet Docker Build & Security Scan Script
# This script builds the Docker image, generates SBOM, and performs security scanning

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-termnet-api}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
SCAN_ENABLED="${SCAN_ENABLED:-true}"
PUSH_TO_REGISTRY="${PUSH_TO_REGISTRY:-false}"
REGISTRY_URL="${REGISTRY_URL:-}"

echo -e "${GREEN}🚀 TermNet Docker Build & Security Pipeline${NC}"
echo "================================================"

# Function to check if tool is installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${YELLOW}⚠️  $1 is not installed${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $1 is installed${NC}"
        return 0
    fi
}

# Check required tools
echo -e "\n${GREEN}📋 Checking required tools...${NC}"
check_tool docker
check_tool python3

# Check optional security tools
echo -e "\n${GREEN}🔒 Checking security tools...${NC}"
SYFT_INSTALLED=$(check_tool syft && echo "true" || echo "false")
TRIVY_INSTALLED=$(check_tool trivy && echo "true" || echo "false")
GRYPE_INSTALLED=$(check_tool grype && echo "true" || echo "false")

# Build Docker image
echo -e "\n${GREEN}🐳 Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Security scanning
if [ "$SCAN_ENABLED" = "true" ]; then
    echo -e "\n${GREEN}🔍 Starting security scanning...${NC}"

    # Create reports directory
    mkdir -p security/reports

    # Generate SBOM with Syft
    if [ "$SYFT_INSTALLED" = "true" ]; then
        echo -e "\n${GREEN}📦 Generating SBOM with Syft...${NC}"
        syft ${IMAGE_NAME}:${IMAGE_TAG} -o spdx-json > security/reports/sbom.json
        echo -e "${GREEN}✅ SBOM generated: security/reports/sbom.json${NC}"
    fi

    # Scan with Trivy
    if [ "$TRIVY_INSTALLED" = "true" ]; then
        echo -e "\n${GREEN}🛡️ Scanning with Trivy...${NC}"
        trivy image --format json --output security/reports/trivy-report.json ${IMAGE_NAME}:${IMAGE_TAG}

        # Show summary
        echo -e "${GREEN}Trivy Summary:${NC}"
        trivy image --severity CRITICAL,HIGH --quiet ${IMAGE_NAME}:${IMAGE_TAG}
    fi

    # Scan with Grype
    if [ "$GRYPE_INSTALLED" = "true" ]; then
        echo -e "\n${GREEN}🔒 Scanning with Grype...${NC}"
        grype ${IMAGE_NAME}:${IMAGE_TAG} -o json > security/reports/grype-report.json

        # Show summary
        echo -e "${GREEN}Grype Summary:${NC}"
        grype ${IMAGE_NAME}:${IMAGE_TAG} --quiet
    fi

    # Run Python validation integration
    echo -e "\n${GREEN}📋 Generating validation receipt...${NC}"
    python3 - <<'EOF'
import sys
import os
import json
from datetime import datetime

# Add project to path
sys.path.insert(0, '.')

try:
    from termnet.security_validation import SecurityValidationEngine

    # Load scan results
    report = {
        "scan_id": f"local-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.utcnow().isoformat(),
        "image": "${IMAGE_NAME}:${IMAGE_TAG}",
        "sbom": {"hash": "pending", "packages_count": 0},
        "vulnerabilities": {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0},
        "compliance_status": "PENDING"
    }

    # Parse Trivy results if available
    try:
        with open('security/reports/trivy-report.json', 'r') as f:
            trivy_data = json.load(f)
            for result in trivy_data.get('Results', []):
                for vuln in result.get('Vulnerabilities', []):
                    severity = vuln.get('Severity', 'UNKNOWN').upper()
                    if severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                        key = severity.lower()
                        report['vulnerabilities'][key] = report['vulnerabilities'].get(key, 0) + 1
                        report['vulnerabilities']['total'] += 1
    except:
        pass

    # Determine compliance
    if report['vulnerabilities']['critical'] > 0:
        report['compliance_status'] = 'FAILED - Critical vulnerabilities'
    elif report['vulnerabilities']['high'] > 5:
        report['compliance_status'] = 'WARNING - High vulnerabilities'
    else:
        report['compliance_status'] = 'PASSED'

    # Create validation receipt
    engine = SecurityValidationEngine()
    receipt = engine.integrate_with_termnet(report)

    print(f"✅ Validation receipt created")
    print(f"📊 Status: {report['compliance_status']}")
    print(f"🔍 Vulnerabilities: C:{report['vulnerabilities']['critical']} H:{report['vulnerabilities']['high']} M:{report['vulnerabilities']['medium']} L:{report['vulnerabilities']['low']}")

except Exception as e:
    print(f"⚠️  Could not generate validation receipt: {e}")
EOF
fi

# Push to registry if configured
if [ "$PUSH_TO_REGISTRY" = "true" ] && [ -n "$REGISTRY_URL" ]; then
    echo -e "\n${GREEN}📤 Pushing to registry...${NC}"
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}
    docker push ${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}
    echo -e "${GREEN}✅ Image pushed to ${REGISTRY_URL}${NC}"
fi

# Final summary
echo -e "\n${GREEN}🎉 Build and scan completed successfully!${NC}"
echo "================================================"
echo -e "Image: ${GREEN}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo -e "Reports: ${GREEN}security/reports/${NC}"

# Check if we should fail based on vulnerabilities
if [ "$SCAN_ENABLED" = "true" ] && [ -f "security/reports/trivy-report.json" ]; then
    CRITICAL_COUNT=$(cat security/reports/trivy-report.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
count = 0
for result in data.get('Results', []):
    for vuln in result.get('Vulnerabilities', []):
        if vuln.get('Severity', '').upper() == 'CRITICAL':
            count += 1
print(count)
" 2>/dev/null || echo "0")

    if [ "$CRITICAL_COUNT" -gt "0" ]; then
        echo -e "\n${RED}❌ Build contains $CRITICAL_COUNT critical vulnerabilities!${NC}"
        echo -e "${YELLOW}Set SCAN_ENABLED=false to skip security checks${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ All checks passed!${NC}"
