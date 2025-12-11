#!/bin/bash

# Script to run tests with different configurations

echo "🧪 QOLQA Backend Test Runner"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to run tests
run_tests() {
    local test_type=$1
    local marker=$2
    
    echo -e "\n${YELLOW}Running ${test_type} tests...${NC}"
    
    if [ -z "$marker" ]; then
        pytest -v
    else
        pytest -v -m "$marker"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${test_type} tests passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ ${test_type} tests failed!${NC}"
        return 1
    fi
}

# Parse command line arguments
case "$1" in
    "validation")
        run_tests "Validation" "validation"
        ;;
    "integration")
        run_tests "Integration" "integration"
        ;;
    "unit")
        run_tests "Unit" "unit"
        ;;
    "auth")
        echo -e "${YELLOW}Running authentication tests (currently skipped)...${NC}"
        pytest -v -m "auth"
        ;;
    "coverage")
        echo -e "${YELLOW}Running tests with coverage...${NC}"
        pytest --cov=. --cov-report=html --cov-report=term
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "quick")
        echo -e "${YELLOW}Running quick test suite...${NC}"
        pytest -v -m "validation"
        ;;
    "all")
        run_tests "All" ""
        ;;
    "watch")
        echo -e "${YELLOW}Running tests in watch mode...${NC}"
        pytest-watch
        ;;
    *)
        echo "Usage: $0 {validation|integration|unit|auth|coverage|quick|all|watch}"
        echo ""
        echo "Options:"
        echo "  validation   - Run validation tests only"
        echo "  integration  - Run integration tests only"
        echo "  unit         - Run unit tests only"
        echo "  auth         - Run authentication tests (currently skipped)"
        echo "  coverage     - Run all tests with coverage report"
        echo "  quick        - Run quick validation tests"
        echo "  all          - Run all tests"
        echo "  watch        - Run tests in watch mode (requires pytest-watch)"
        exit 1
        ;;
esac

exit $?
