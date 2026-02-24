#!/usr/bin/env python3
import subprocess
import sys
import os

def check_tool(tool_name, version_arg="--version"):
    try:
        result = subprocess.run([tool_name, version_arg], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, f"✓ {tool_name} is working"
        else:
            return False, f"✗ {tool_name} returned error: {result.stderr}"
    except FileNotFoundError:
        return False, f"✗ {tool_name} not found in PATH"
    except Exception as e:
        return False, f"✗ {tool_name} error: {str(e)}"

def check_python_package(package_name):
    try:
        __import__(package_name)
        return True, f"✓ Python package {package_name} is available"
    except ImportError:
        return False, f"✗ Python package {package_name} not found"

print("🔍 Testing tool availability...")
print("=" * 50)

# Check command line tools
tools_to_check = [
    ("nmap", "--version"),
    ("nikto", "-version"),
    ("nuclei", "-version"),
    ("testssl.sh", "--version"),
    ("sqlmap", "--version"),
    ("dirb", "--help"),
    ("whatweb", "--version")
]

print("Command Line Tools:")
print("-" * 20)
all_working = True
for tool, arg in tools_to_check:
    working, message = check_tool(tool, arg)
    print(message)
    if not working:
        all_working = False

# Check Python packages
print("\nPython Packages:")
print("-" * 20)
python_packages = [
    "nmap",
    "requests", 
    "OpenSSL",
    "celery",
    "flask",
    "flask_sqlalchemy",
    "flask_cors"
]

for package in python_packages:
    working, message = check_python_package(package)
    print(message)
    if not working:
        all_working = False

print("=" * 50)
if all_working:
    print("🎉 All tools and packages are installed and working!")
else:
    print("⚠️ Some tools/packages may need additional setup")

# Check virtual environment
if 'VIRTUAL_ENV' in os.environ:
    print(f"\n📍 Running in virtual environment: {os.environ['VIRTUAL_ENV']}")
else:
    print("\n📍 Running in system Python environment")
