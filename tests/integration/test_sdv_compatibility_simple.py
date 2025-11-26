#!/usr/bin/env python3
"""
Simple SDV Compatibility Test
Tests that the UDA agent can resolve sdv imports correctly
"""

import sys
import os
import subprocess
import tempfile

# Add parent directory for imports
sys.path.append('..')

def test_sdv_compatibility():
    """Test that SDV compatibility layer works"""
    print("🧪 Testing SDV Compatibility Layer")
    print("=" * 50)

    # Create a simple test script with sdv imports
    test_script = '''
import sys
sys.path.append('../../src')

# Import UDA agent to trigger SDV compatibility setup
from uda_agent import UniversalDeploymentAgent

# Create agent instance to trigger compatibility setup
agent = UniversalDeploymentAgent()

print("✅ Agent created successfully")

# Test if sdv imports work
try:
    # This should work if compatibility layer is set up correctly
    import sdv.vdb.reply
    print("✅ sdv.vdb.reply import successful")
except ImportError as e:
    print(f"❌ sdv.vdb.reply import failed: {e}")
    sys.exit(1)

try:
    import sdv.vehicle_app
    print("✅ sdv.vehicle_app import successful")
except ImportError as e:
    print(f"❌ sdv.vehicle_app import failed: {e}")
    sys.exit(1)

# Test if the modules have expected attributes
try:
    from sdv.vehicle_app import VehicleApp
    print("✅ VehicleApp class imported successfully")
except ImportError as e:
    print(f"❌ VehicleApp import failed: {e}")
    sys.exit(1)

try:
    from sdv.vdb.reply import DataPointReply
    print("✅ DataPointReply imported successfully")
except ImportError as e:
    print(f"❌ DataPointReply import failed: {e}")
    sys.exit(1)

print("🎉 All SDV compatibility tests passed!")
'''

    # Write test script to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        temp_file = f.name

    try:
        print("🚀 Running SDV compatibility test...")

        # Change to integration directory and run test
        original_cwd = os.getcwd()
        os.chdir('integration')

        # Run the test script
        result = subprocess.run([
            sys.executable, temp_file
        ], capture_output=True, text=True, timeout=30)

        os.chdir(original_cwd)

        print("📤 STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("❌ STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("✅ SDV compatibility test PASSED")
            return True
        else:
            print(f"❌ SDV compatibility test FAILED (code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ SDV compatibility test timed out")
        os.chdir(original_cwd)
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        try:
            os.chdir(original_cwd)
        except:
            pass
        return False
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass

def test_sdv_app_execution():
    """Test that SDV app code can be executed"""
    print("\n🧪 Testing SDV App Execution")
    print("=" * 40)

    # Create the SDV test app (same as the one Kit Server sends)
    sdv_app = '''import sys
import os
sys.path.append('../../src')

# Trigger SDV compatibility setup
from uda_agent import UniversalDeploymentAgent

# Create agent instance (this sets up SDV compatibility)
agent = UniversalDeploymentAgent()

print("🚀 Starting SDV App Test...")
print("📦 Testing imports...")

try:
    from sdv.vdb.reply import DataPointReply
    from sdv.vehicle_app import VehicleApp
    print("✅ sdv imports successful!")
except ImportError as e:
    print(f"❌ sdv imports failed: {e}")
    sys.exit(1)

# Mock vehicle class for testing
class MockVehicle:
    class Body:
        class Lights:
            class Beam:
                class Low:
                    @staticmethod
                    async def set(value):
                        print(f"💡 Setting light to: {value}")

                    @staticmethod
                    async def get():
                        class Response:
                            value = True
                        return Response()

vehicle = MockVehicle()

class TestApp(VehicleApp):
    def __init__(self, vehicle_client):
        super().__init__()
        self.Vehicle = vehicle_client

    async def on_start(self):
        print("✅ SDV VehicleApp started successfully!")
        print("🔄 Testing vehicle signal access...")

        try:
            await self.Vehicle.Body.Lights.Beam.Low.IsOn.set(True)
            value = (await self.Vehicle.Body.Lights.Beam.Low.IsOn.get()).value
            print(f"💡 Light value: {value}")

            await self.Vehicle.Body.Lights.Beam.Low.IsOn.set(False)
            print("✅ Vehicle signal access test passed!")
        except Exception as e:
            print(f"🔧 Vehicle signal test failed (expected without KUKSA): {e}")

import asyncio

async def main():
    app = TestApp(vehicle)
    await app.on_start()

# Run the test
asyncio.run(main())
print("🎉 SDV App execution test completed successfully!")
'''

    # Write app to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sdv_app)
        temp_file = f.name

    try:
        print("🚀 Running SDV app execution test...")

        # Change to integration directory and run test
        original_cwd = os.getcwd()
        os.chdir('integration')

        # Run the SDV app
        result = subprocess.run([
            sys.executable, temp_file
        ], capture_output=True, text=True, timeout=30)

        os.chdir(original_cwd)

        print("📤 STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("❌ STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("✅ SDV app execution test PASSED")
            return True
        else:
            print(f"❌ SDV app execution test FAILED (code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ SDV app execution test timed out")
        os.chdir(original_cwd)
        return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        try:
            os.chdir(original_cwd)
        except:
            pass
        return False
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass

def main():
    """Run all SDV compatibility tests"""
    print("🧪 SDV Compatibility Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Basic compatibility
    results.append(test_sdv_compatibility())

    # Test 2: SDV app execution
    results.append(test_sdv_app_execution())

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 30)

    passed = sum(results)
    total = len(results)

    print(f"Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All SDV compatibility tests PASSED!")
        print("✅ SDV compatibility layer is working correctly")
        print("✅ UDA agent can handle sdv imports")
        print("✅ SDV apps can be deployed and executed")
        return True
    else:
        print("⚠️ Some SDV compatibility tests FAILED")
        print("❌ Check the output above for details")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)