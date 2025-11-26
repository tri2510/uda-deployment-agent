#!/usr/bin/env python3
"""
Test Environment Cleanup Script
Ensures clean environment before running UDA agent tests
"""

import subprocess
import time
import psutil
import sys
import os

def kill_processes_by_name(pattern):
    """Kill processes matching the given pattern"""
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if pattern in cmdline:
                print(f"🔪 Killing process {proc.info['pid']}: {proc.info['name']} ({cmdline[:80]}{'...' if len(cmdline) > 80 else ''})")
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return killed

def check_and_kill_ports():
    """Kill processes using common test ports"""
    ports = [3090, 3091, 8080, 5000]  # Common test ports
    killed = 0

    for port in ports:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections'] or []:
                        if conn.laddr.port == port:
                            print(f"🔪 Killing process {proc.info['pid']} using port {port}: {proc.info['name']}")
                            proc.kill()
                            killed += 1
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except (psutil.AccessDenied):
            pass

    return killed

def clean_temp_files():
    """Clean temporary test files"""
    import glob

    patterns = [
        'test_report_*.txt',
        'test_*.log',
        '/tmp/uda_*',
        '/tmp/mock_*',
        '../logs/*.log',
        '../deployments/*'
    ]

    cleaned = 0
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            try:
                if os.path.isfile(file):
                    os.remove(file)
                    print(f"🗑️  Removing file: {file}")
                    cleaned += 1
                elif os.path.isdir(file) and 'deployments' in file:
                    # Don't remove deployments folder, just warn
                    print(f"⚠️  Skipping directory: {file}")
            except OSError as e:
                print(f"⚠️  Could not remove {file}: {e}")

    return cleaned

def wait_for_processes_to_die(timeout=10):
    """Wait for processes to fully terminate"""
    print(f"⏳ Waiting for processes to terminate...")
    for i in range(timeout):
        time.sleep(1)
        sys.stdout.write(f"   {i+1}/{timeout}\r")
        sys.stdout.flush()
    print()

def verify_clean_environment():
    """Verify that the environment is clean"""
    print("🔍 Verifying clean environment...")

    # Check for remaining processes
    remaining_patterns = ['mock_kit_server', 'uda_agent']
    for pattern in remaining_patterns:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if pattern in cmdline:
                    print(f"⚠️  Warning: Found remaining process with pattern '{pattern}': PID {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    # Check for ports still in use
    ports = [3090, 3091, 8080, 5000]
    for port in ports:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                print(f"⚠️  Warning: Port {port} is still in use")
            sock.close()
        except:
            pass

def main():
    """Main cleanup function"""
    print("🧹 UDA Agent Test Environment Cleanup")
    print("=" * 50)

    print("\n1️⃣ Killing test processes...")
    process_killed = kill_processes_by_name('mock_kit_server.py')
    process_killed += kill_processes_by_name('uda_agent.py')
    process_killed += kill_processes_by_name('python.*test')
    print(f"   ✅ Killed {process_killed} processes")

    print("\n2️⃣ Killing processes using test ports...")
    port_killed = check_and_kill_ports()
    print(f"   ✅ Killed {port_killed} processes on test ports")

    print("\n3️⃣ Cleaning temporary files...")
    files_cleaned = clean_temp_files()
    print(f"   ✅ Cleaned {files_cleaned} temporary files")

    print("\n4️⃣ Waiting for processes to fully terminate...")
    wait_for_processes_to_die()

    print("\n5️⃣ Verifying clean environment...")
    verify_clean_environment()

    print("\n✅ Cleanup completed!")
    print("Environment should now be clean for test execution.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        sys.exit(1)