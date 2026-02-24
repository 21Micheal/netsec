#!/bin/bash

set -e  # Exit on any error

echo "🔧 Starting security tools installation..."
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    print_status "Virtual environment detected: $VIRTUAL_ENV"
    PIP_CMD="pip"
else
    print_warning "No virtual environment detected, using system pip"
    PIP_CMD="pip3"
fi

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root. It will use sudo when needed."
    exit 1
fi

# Update package list
print_status "Updating package list..."
sudo apt update

# Install basic tools from repositories
print_status "Installing basic security tools..."
sudo apt install -y \
    nmap \
    nikto \
    sqlmap \
    dirb \
    whatweb \
    python3-pip \
    python3-venv \
    git \
    wget \
    unzip \
    curl

# Install testssl.sh
print_status "Installing testssl.sh..."
if [ -d "testssl.sh" ]; then
    print_warning "testssl.sh directory already exists, pulling latest changes..."
    cd testssl.sh
    git pull
    cd ..
else
    git clone --depth 1 https://github.com/drwetter/testssl.sh.git
fi

# Create symlink for testssl.sh
if [ -f "/usr/local/bin/testssl.sh" ]; then
    print_warning "testssl.sh symlink already exists, updating..."
    sudo rm /usr/local/bin/testssl.sh
fi

sudo ln -sf "$(pwd)/testssl.sh/testssl.sh" /usr/local/bin/testssl.sh
sudo chmod +x /usr/local/bin/testssl.sh

# Install Nuclei (pre-built binary method - no Go required)
print_status "Installing Nuclei..."
NUCLEI_VERSION="3.2.7"
NUCLEI_URL="https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip"

# Download and install nuclei
cd /tmp
wget -q "$NUCLEI_URL" -O nuclei.zip
unzip -q nuclei.zip
sudo mv nuclei /usr/local/bin/
rm nuclei.zip
cd -

# Install Python dependencies (without --user flag in venv)
print_status "Installing Python dependencies..."
$PIP_CMD install \
    python-nmap \
    requests \
    pyopenssl \
    celery \
    flask \
    flask-sqlalchemy \
    flask-cors

# Create additional symlinks for common tools
print_status "Creating tool symlinks..."

# Ensure testssl.sh is executable
chmod +x testssl.sh/testssl.sh

# Verify installations
echo ""
echo "✅ Verifying installations..."
echo "============================="

tools=("nmap" "nikto" "sqlmap" "dirb" "whatweb" "nuclei" "testssl.sh")
for tool in "${tools[@]}"; do
    if command -v $tool &> /dev/null; then
        echo -e "${GREEN}✓${NC} $tool installed successfully"
        
        # Show version for some tools
        case $tool in
            "nmap")
                nmap --version | head -n1
                ;;
            "nikto")
                nikto -version 2>/dev/null | head -n1 || echo "Version check not available"
                ;;
            "nuclei")
                nuclei -version 2>/dev/null | head -n1
                ;;
            "testssl.sh")
                testssl.sh --version 2>/dev/null | head -n1
                ;;
        esac
    else
        echo -e "${RED}✗${NC} $tool installation failed"
    fi
    echo "---"
done

# Create a test script to verify everything works
print_status "Creating verification script..."
cat > test_tools.py << 'EOF'
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
EOF

chmod +x test_tools.py

# Create a usage example script
print_status "Creating usage examples..."
cat > security_scan_example.sh << 'EOF'
#!/bin/bash
echo "🔍 Security Tools Usage Examples"
echo "================================"
echo ""
echo "1. Basic NMAP scan:"
echo "   nmap -sV 127.0.0.1"
echo ""
echo "2. Nikto web scan:"
echo "   nikto -h http://localhost:8080"
echo ""
echo "3. SSL analysis with testssl.sh:"
echo "   testssl.sh example.com"
echo ""
echo "4. Nuclei vulnerability scan:"
echo "   nuclei -u http://example.com"
echo ""
echo "5. Directory brute force with dirb:"
echo "   dirb http://example.com"
echo ""
echo "6. Web technology detection with whatweb:"
echo "   whatweb example.com"
echo ""
echo "All tools are now ready to use!"
EOF

chmod +x security_scan_example.sh

echo ""
echo "🎉 Installation complete!"
echo "========================"
echo ""
echo "📚 Next steps:"
echo "1. Run: python3 test_tools.py to verify all tools work"
echo "2. Check: ./security_scan_example.sh for usage examples"
echo "3. Test your vulnerability scanner with a simple target"
echo ""
echo "🔧 Tools installed:"
echo "   - nmap, nikto, sqlmap, dirb, whatweb"
echo "   - nuclei, testssl.sh"
echo "   - All required Python packages"
