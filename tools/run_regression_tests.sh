#!/bin/bash
# Regression test runner for GraphRAG
# This script runs the regression tests with proper environment setup

# Change to the project root directory
cd "$(dirname "$0")/.."

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print a header
print_header() {
    echo -e "\n${BLUE}=======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=======================================${NC}\n"
}

# Function to print a success message
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print a warning message
print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Function to print an error message
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to report a bug
report_bug() {
    local description="$1"
    local cause="$2"
    local critical="$3"
    
    print_warning "Reporting bug: $description"
    
    if [ "$critical" == "true" ]; then
        ./tools/bug_client.py add "$description" "$cause" --critical
    else
        ./tools/bug_client.py add "$description" "$cause"
    fi
}

# Function to run a test
run_test() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .py)
    
    print_header "Running test: $test_name"
    
    # Run the test with UV
    ./tools/uvrun.sh run "$test_file"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        print_success "Test passed: $test_name"
        return 0
    else
        print_error "Test failed: $test_name (exit code: $exit_code)"
        
        # Report the bug
        report_bug "Regression test failed: $test_name" "Test exited with code $exit_code" "false"
        
        return 1
    fi
}

# Check if UV is available
if ! command -v uv &> /dev/null; then
    print_error "UV is not installed. Please install it with: pip install uv"
    exit 1
fi

# Check if the virtual environment exists
if [ ! -d ".venv-py312" ]; then
    print_warning "Virtual environment not found. Creating it with UV..."
    uv venv --python 3.12 .venv-py312
    
    if [ $? -ne 0 ]; then
        print_error "Failed to create virtual environment."
        exit 1
    fi
    
    print_success "Virtual environment created successfully."
fi

# Install dependencies if needed
if [ ! -f ".venv-py312/bin/pytest" ]; then
    print_warning "Installing test dependencies..."
    ./tools/uvrun.sh install pytest websockets requests
    
    if [ $? -ne 0 ]; then
        print_error "Failed to install dependencies."
        exit 1
    fi
    
    print_success "Dependencies installed successfully."
fi

# Start the test environment
print_header "Setting up test environment"
./tools/test_setup.py --start &
TEST_ENV_PID=$!

# Give the services time to start
sleep 5

# Run the tests
print_header "Running regression tests"

# Find all regression tests
TEST_FILES=$(find tests/regression -name "test_*.py" | sort)

# Initialize counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Run each test
for test_file in $TEST_FILES; do
    ((TOTAL_TESTS++))
    
    run_test "$test_file"
    
    if [ $? -eq 0 ]; then
        ((PASSED_TESTS++))
    else
        ((FAILED_TESTS++))
    fi
done

# Stop the test environment
print_header "Stopping test environment"
kill $TEST_ENV_PID
./tools/test_setup.py --stop

# Print summary
print_header "Test Summary"
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    print_success "All tests passed!"
    exit 0
else
    print_error "$FAILED_TESTS tests failed."
    exit 1
fi
