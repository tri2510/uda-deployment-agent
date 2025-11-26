#!/usr/bin/env python3
"""
UDA Agent Test Runner
Comprehensive test suite for UDA agent SDV runtime compatibility
"""

import subprocess
import sys
import os
import time
from datetime import datetime

# Test categories and descriptions
TEST_SUITES = [
    # Unit Tests - Basic functionality
    {
        "category": "unit",
        "name": "Unit Tests",
        "description": "Basic connectivity and component tests",
        "tests": [
            ("test_connectivity.py", "Basic Connectivity Test"),
            ("debug_routing.py", "Message Routing Debug Test")
        ]
    },

    # Integration Tests - Core SDV runtime functionality
    {
        "category": "integration",
        "name": "Integration Tests",
        "description": "SDV runtime compatible feature tests",
        "tests": [
            ("test_runtime_info.py", "Runtime Info Test"),
            ("test_deploy_request.py", "Deploy Request Test"),
            ("test_run_python_app.py", "Run Python App Test"),
            ("test_stop_python_app.py", "Stop Python App Test"),
            ("test_output_to_kitserver.py", "Output Messages to Kit Server Test")
        ]
    },

    # Regression Tests - Critical functionality
    {
        "category": "regression",
        "name": "Regression Tests",
        "description": "Critical SDV runtime compatibility checks",
        "tests": [
            ("test_messageTokit_kitReply.py", "MessageToKit-kitReply Event Test")
        ]
    },

    # End-to-End Tests - Complete workflows
    {
        "category": "e2e",
        "name": "End-to-End Tests",
        "description": "Complete workflow and scenario tests",
        "tests": [
            ("test_full_flow.py", "Full System Flow Test")
        ]
    }
]

def run_test(test_file, test_dir, description):
    """Run a single test file"""
    print(f"\n🚀 Running: {description}")
    print(f"📁 Category: {test_dir}")
    print(f"📄 File: {test_file}")
    print("=" * 70)

    test_path = os.path.join(test_dir, test_file)

    try:
        # Change to appropriate directory for test execution
        original_cwd = os.getcwd()
        if test_dir != ".":
            os.chdir(test_dir)

        # Update paths in tests that need to reference tools
        env = os.environ.copy()
        if test_dir != ".":
            env['PYTHONPATH'] = os.path.join(original_cwd, test_dir) + ':' + os.path.join(original_cwd, 'tools')

        # Run the test
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=60, env=env)

        os.chdir(original_cwd)

        print("📤 STDOUT:")
        if result.stdout:
            print(result.stdout)
        else:
            print("   (No stdout output)")

        if result.stderr:
            print("❌ STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("✅ Test completed successfully")
            return True
        else:
            print(f"❌ Test failed with code: {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ Test timed out after 60 seconds")
        os.chdir(original_cwd)
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        os.chdir(original_cwd)
        return False

def run_test_suite(suite, fast_mode=False):
    """Run a complete test suite"""
    print(f"\n{'='*80}")
    print(f"🧪 {suite['name']} - {suite['description']}")
    print(f"{'='*80}")

    test_dir = suite['category']
    passed = 0
    total = len(suite['tests'])

    for i, (test_file, description) in enumerate(suite['tests'], 1):
        print(f"\n📊 Progress: {i}/{total} tests in {suite['name']}")

        if not os.path.exists(os.path.join(test_dir, test_file)):
            print(f"❌ Test file not found: {test_file}")
            continue

        if run_test(test_file, test_dir, description):
            passed += 1

        if fast_mode and i >= 2:  # Limit tests in fast mode
            print(f"⚡ Fast mode: Skipping remaining {total - i} tests")
            break

    return passed, total

def generate_test_report(results):
    """Generate test execution report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*80}")
    print(f"📊 UDA Agent Test Report")
    print(f"{'='*80}")
    print(f"🕐 Timestamp: {timestamp}")
    print(f"\n📋 Test Results Summary:")

    total_passed = 0
    total_tests = 0

    for suite_name, (passed, total) in results.items():
        status = "✅ PASS" if passed == total else "❌ FAIL"
        print(f"   {suite_name}: {passed}/{total} tests {status}")
        total_passed += passed
        total_tests += total

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 Overall: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")

    if total_passed == total_tests:
        print("🎉 All tests passed! UDA agent is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")

    # Save report to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(f"UDA Agent Test Report\n")
        f.write(f"Generated: {timestamp}\n")
        f.write(f"{'='*50}\n\n")
        for suite_name, (passed, total) in results.items():
            f.write(f"{suite_name}: {passed}/{total} passed\n")
        f.write(f"\nOverall: {total_passed}/{total_tests} passed ({success_rate:.1f}%)\n")

    print(f"\n📄 Report saved to: {report_file}")

def cleanup_environment():
    """Run environment cleanup before tests"""
    print("🧹 Cleaning test environment...")
    try:
        result = subprocess.run([sys.executable, 'cleanup.py'],
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Environment cleaned successfully")
            return True
        else:
            print(f"⚠️  Cleanup warnings: {result.stderr}")
            return True  # Continue despite cleanup warnings
    except subprocess.TimeoutExpired:
        print("⚠️  Cleanup timed out, continuing...")
        return True
    except Exception as e:
        print(f"⚠️  Cleanup failed: {e}, continuing...")
        return True

def main():
    """Main test runner"""
    print("🧪 UDA Agent SDV Runtime Compatible Test Suite")
    print("=" * 60)

    # Run cleanup first
    cleanup_environment()

    # Check if UDA agent source exists
    if not os.path.exists("../src/uda_agent.py"):
        print("❌ UDA agent source not found at ../src/uda_agent.py")
        print("   Please run this from the tests directory")
        sys.exit(1)

    # Parse command line arguments
    fast_mode = "--fast" in sys.argv
    run_specific = None

    if "--category" in sys.argv:
        idx = sys.argv.index("--category")
        if idx + 1 < len(sys.argv):
            run_specific = sys.argv[idx + 1]

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python3 run_tests.py [options]")
        print("Options:")
        print("  --fast              Run limited tests for quick validation")
        print("  --category <name>  Run specific test category (unit, integration, regression, e2e)")
        print("  --help, -h          Show this help")
        print("\nAvailable categories:")
        for suite in TEST_SUITES:
            print(f"  {suite['category']:<12} {suite['name']}")
        return

    # Run tests
    results = {}

    if run_specific:
        # Run specific category
        for suite in TEST_SUITES:
            if suite['category'] == run_specific:
                print(f"🎯 Running specific category: {suite['name']}")
                passed, total = run_test_suite(suite, fast_mode)
                results[suite['name']] = (passed, total)
                break
        else:
            print(f"❌ Unknown category: {run_specific}")
            print("   Available categories: unit, integration, regression, e2e")
            sys.exit(1)
    else:
        # Run all test suites
        for suite in TEST_SUITES:
            passed, total = run_test_suite(suite, fast_mode)
            results[suite['name']] = (passed, total)

    # Generate report
    generate_test_report(results)

if __name__ == "__main__":
    main()