#!/usr/bin/env python3
"""
Test runner for UDA agent Kit Server message tests
"""

import subprocess
import sys
import os

def run_test(test_file, description):
    """Run a single test file"""
    print(f"\n🚀 Running: {description}")
    print(f"📁 File: {test_file}")
    print("=" * 60)

    try:
        # Run the test
        result = subprocess.run([sys.executable, test_file],
                              capture_output=True, text=True, timeout=30)

        print("📤 STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("❌ STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("✅ Test completed successfully")
        else:
            print(f"❌ Test failed with code: {result.returncode}")

    except subprocess.TimeoutExpired:
        print("⏰ Test timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Error running test: {e}")

    print("=" * 60)

def main():
    """Run all tests"""
    print("🧪 UDA Agent Kit Server Message Tests")
    print("=" * 60)

    # Change to tests directory
    os.chdir(os.path.dirname(__file__))

    # List of tests to run
    tests = [
        ("test_runtime_info.py", "Runtime Info Test"),
        ("test_deploy_request.py", "Deploy Request Test"),
        ("test_run_python_app.py", "Run Python App Test"),
        ("test_stop_python_app.py", "Stop Python App Test")
    ]

    for test_file, description in tests:
        if os.path.exists(test_file):
            run_test(test_file, description)
        else:
            print(f"❌ Test file not found: {test_file}")

    print("\n🏁 All tests completed!")
    print("\n📝 Instructions:")
    print("1. Make sure UDA agent is running on localhost:3090")
    print("2. Run individual tests: python3 <test_file>.py")
    print("3. Or run all tests with: python3 run_tests.py")

if __name__ == "__main__":
    main()