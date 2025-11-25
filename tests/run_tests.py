#!/usr/bin/env python3

"""
UDA Test Runner
Simple script to run UDA tests
"""

import sys
import os
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run UDA tests"""
    logger.info("🚀 Starting UDA Test Runner...")

    # Change to tests directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    try:
        # Run the test framework
        result = subprocess.run([
            sys.executable, 'test_framework.py'
        ], check=True)

        logger.info("✅ Tests completed successfully!")

        # Show test report if exists
        report_file = os.path.join(script_dir, 'test_report.md')
        if os.path.exists(report_file):
            logger.info("📊 Test Report:")
            with open(report_file, 'r') as f:
                print(f.read())

        return 0

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Tests failed with exit code: {e.returncode}")
        return e.returncode
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())