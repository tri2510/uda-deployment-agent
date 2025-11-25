#!/bin/bash

# ==============================================================================
# UDA Comprehensive Test Runner
# Automated testing shell script with clear outputs and detailed reporting
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$SCRIPT_DIR/tests"
LOG_FILE="$TESTS_DIR/test_output.log"
RESULTS_DIR="$TESTS_DIR/results"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to print colored headers
print_header() {
    echo -e "\n${BOLD}${BLUE}$1${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..80})${NC}"
}

# Function to print section
print_section() {
    echo -e "\n${BOLD}${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '-%.0s' {1..60})${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Function to show progress
show_progress() {
    local current=$1
    local total=$2
    local desc=$3
    local percent=$((current * 100 / total))
    local bar_length=30
    local filled_length=$((percent * bar_length / 100))

    local bar=""
    for ((i=0; i<filled_length; i++)); do bar+="█"; done
    for ((i=filled_length; i<bar_length; i++)); do bar+="░"; done

    printf "\r%s %s [%s] %d%%" "$desc" "$bar" "$percent"
    if [ $current -eq $total ]; then echo; fi
}

# Check dependencies
check_dependencies() {
    print_header "🔍 Checking Dependencies"

    local missing_deps=()

    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        print_success "Python 3: $(python3 --version)"
    fi

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            print_success "Docker: Running and accessible"
        else
            print_warning "Docker: Installed but not running"
        fi
    else
        print_warning "Docker: Not installed (Docker tests will be skipped)"
    fi

    # Check required Python packages
    print_info "Checking Python packages..."

    local required_packages=("aiohttp" "psutil" "docker" "requests")
    local missing_packages=()

    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" &> /dev/null; then
            print_success "Package $package: Available"
        else
            missing_packages+=("$package")
        fi
    done

    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_warning "Missing Python packages: ${missing_packages[*]}"
        print_info "Installing missing packages..."
        pip3 install "${missing_packages[@]}" || {
            print_error "Failed to install Python packages"
            return 1
        }
    fi

    # Check UDA agent file
    if [ -f "$SCRIPT_DIR/ultra-lightweight-uda-agent.py" ]; then
        print_success "UDA Agent: Found"
    else
        print_error "UDA Agent: Not found at $SCRIPT_DIR/ultra-lightweight-uda-agent.py"
        return 1
    fi

    print_success "All dependencies satisfied"
    return 0
}

# Prepare test environment
prepare_environment() {
    print_header "🧹 Preparing Test Environment"

    # Clean up any existing processes
    print_info "Cleaning up previous test processes..."
    pkill -f "mock_kit_server.py" 2>/dev/null || true
    pkill -f "ultra-lightweight-uda-agent.py" 2>/dev/null || true

    # Clean up Docker containers if Docker is available
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        print_info "Cleaning up Docker containers..."
        docker stop $(docker ps -q --filter "name=uda-" 2>/dev/null) 2>/dev/null || true
        docker rm $(docker ps -aq --filter "name=uda-" 2>/dev/null) 2>/dev/null || true
    fi

    # Wait a moment for cleanup
    sleep 2

    # Create fresh log file
    print_info "Initializing test logs..."
    echo "UDA Comprehensive Test Log - $(date)" > "$LOG_FILE"
    echo "=============================================" >> "$LOG_FILE"

    print_success "Environment prepared"
}

# Run isolated tests first
run_isolated_tests() {
    print_header "🧪 Running Isolated UDA Tests"

    cd "$SCRIPT_DIR"

    print_info "Starting isolated test runner..."
    if python3 tests/isolated_test_runner.py 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Isolated tests completed successfully"
        return 0
    else
        print_error "Isolated tests failed"
        return 1
    fi
}

# Run comprehensive ISTQB tests
run_istqb_tests() {
    print_header "🎯 Running ISTQB-Comprehensive UDA Tests"

    cd "$SCRIPT_DIR"

    print_info "Starting ISTQB-compliant test runner..."
    print_info "This will execute detailed test cases with clear specifications and results..."

    if python3 tests/istqb_test_framework.py 2>&1 | tee -a "$LOG_FILE"; then
        print_success "ISTQB tests completed successfully"
        return 0
    else
        print_error "ISTQB tests failed"
        return 1
    fi
}

# Run comprehensive tests
run_comprehensive_tests() {
    print_header "🚀 Running Comprehensive UDA Tests"

    cd "$SCRIPT_DIR"

    print_info "Starting comprehensive test runner..."
    print_info "This will test both Docker and non-Docker modes with performance analysis..."

    if python3 tests/comprehensive_test_runner.py 2>&1 | tee -a "$LOG_FILE"; then
        print_success "Comprehensive tests completed successfully"
        return 0
    else
        print_error "Comprehensive tests failed"
        return 1
    fi
}

# Generate summary report
generate_summary() {
    print_header "📊 Test Summary Report"

    local test_time=$(date '+%Y-%m-%d %H:%M:%S')
    local log_entries=$(wc -l < "$LOG_FILE")

    echo "Test Execution Summary"
    echo "====================="
    echo "Date: $test_time"
    echo "Log File: $LOG_FILE"
    echo "Log Entries: $log_entries"
    echo ""

    # Check for HTML report
    if [ -f "$TESTS_DIR/test_report.html" ]; then
        print_success "HTML Report: $TESTS_DIR/test_report.html"
    fi

    # Check for JSON report
    if [ -f "$TESTS_DIR/test_report.json" ]; then
        print_success "JSON Report: $TESTS_DIR/test_report.json"
    fi

    # Extract key metrics from logs
    echo ""
    echo "Key Metrics:"
    echo "-----------"

    # Count test passes/failures
    local passed_count=$(grep -c "✅" "$LOG_FILE" 2>/dev/null || echo "0")
    local error_count=$(grep -c "❌" "$LOG_FILE" 2>/dev/null || echo "0")
    local warning_count=$(grep -c "⚠️" "$LOG_FILE" 2>/dev/null || echo "0")

    echo "✅ Successful operations: $passed_count"
    echo "❌ Errors: $error_count"
    echo "⚠️  Warnings: $warning_count"

    # Extract test completion status
    if grep -q "TEST SUITE PASSED" "$LOG_FILE" 2>/dev/null; then
        print_success "Overall Test Status: PASSED"
    elif grep -q "TEST SUITE FAILED" "$LOG_FILE" 2>/dev/null; then
        print_error "Overall Test Status: FAILED"
    else
        print_warning "Overall Test Status: INCOMPLETE"
    fi

    echo ""
    echo "Report Files Generated:"
    echo "---------------------"

    # List all generated files
    for file in "$TESTS_DIR"/test_report.* "$TESTS_DIR"/test_output.log; do
        if [ -f "$file" ]; then
            local size=$(du -h "$file" | cut -f1)
            echo "📄 $(basename "$file") - $size"
        fi
    done
}

# Show help
show_help() {
    echo "UDA Comprehensive Test Runner"
    echo "============================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -i, --isolated      Run isolated tests only (quick test)"
    echo "  -c, --comprehensive Run comprehensive tests with Docker and performance"
    echo "  -s, --istqb         Run ISTQB-compliant tests with detailed specifications"
    echo "  -d, --dependencies  Check dependencies only"
    echo "  -r, --reports       Generate summary reports from existing logs"
    echo "  -v, --verbose       Enable verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                  Run quick isolated tests"
    echo "  $0 --comprehensive  Run full test suite"
    echo "  $0 --istqb         Run ISTQB-compliant detailed test cases"
    echo "  $0 --dependencies   Verify system dependencies"
    echo ""
    echo "Report files are generated in the tests/ directory:"
    echo "  - istqb_test_report.html  ISTQB HTML report with detailed specifications"
    echo "  - istqb_test_report.json  ISTQB JSON data for analysis"
    echo "  - istqb_test_report.csv   ISTQB CSV for spreadsheet import"
    echo "  - test_report.html   Interactive HTML report"
    echo "  - test_report.json   Raw JSON data"
    echo "  - test_output.log    Detailed execution log"
}

# Main execution
main() {
    local run_isolated=false
    local run_comprehensive=false
    local run_istqb=false
    local check_deps_only=false
    local generate_reports_only=false
    local verbose=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -i|--isolated)
                run_isolated=true
                shift
                ;;
            -c|--comprehensive)
                run_comprehensive=true
                shift
                ;;
            -s|--istqb)
                run_istqb=true
                shift
                ;;
            -d|--dependencies)
                check_deps_only=true
                shift
                ;;
            -r|--reports)
                generate_reports_only=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                set -x
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Print welcome banner
    print_header "🚀 UDA Comprehensive Test Runner"
    echo "Automated testing for Universal Deployment Agent"
    echo "Host: $(hostname) | Date: $(date)"
    echo "Script Directory: $SCRIPT_DIR"

    # Handle specific modes
    if [ "$check_deps_only" = true ]; then
        check_dependencies
        exit $?
    fi

    if [ "$generate_reports_only" = true ]; then
        generate_summary
        exit $?
    fi

    # Default mode: run isolated tests
    if [ "$run_isolated" = false ] && [ "$run_comprehensive" = false ] && [ "$run_istqb" = false ]; then
        run_isolated=true
    fi

    # Set default execution mode based on arguments
    local exit_code=0

    # 1. Check dependencies
    if ! check_dependencies; then
        print_error "Dependency check failed"
        exit 1
    fi

    # 2. Prepare environment
    prepare_environment

    # 3. Run tests based on mode
    if [ "$run_comprehensive" = true ]; then
        if ! run_comprehensive_tests; then
            print_error "Comprehensive tests failed"
            exit_code=1
        fi
    elif [ "$run_istqb" = true ]; then
        if ! run_istqb_tests; then
            print_error "ISTQB tests failed"
            exit_code=1
        fi
    elif [ "$run_isolated" = true ]; then
        if ! run_isolated_tests; then
            print_error "Isolated tests failed"
            exit_code=1
        fi
    fi

    # 4. Generate summary
    generate_summary

    # Final status
    if [ $exit_code -eq 0 ]; then
        print_success "All tests completed successfully!"
        echo ""
        print_info "View detailed reports:"
        print_info "  • HTML: $TESTS_DIR/test_report.html"
        print_info "  • JSON: $TESTS_DIR/test_report.json"
        print_info "  • Logs: $LOG_FILE"
    else
        print_error "Some tests failed. Check logs for details."
        print_info "Log file: $LOG_FILE"
    fi

    exit $exit_code
}

# Execute main function
main "$@"