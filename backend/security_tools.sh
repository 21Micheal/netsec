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
NUCLEI_VERSION="3.2.7"  # You can update this to the latest version
NUCLEI_URL="https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip"

# Download and install nuclei
cd /tmp
wget -q --show-progress "$NUCLEI_URL" -O nuclei.zip
unzip -q nuclei.zip
sudo mv nuclei /usr/local/bin/
rm nuclei.zip
cd -

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install --user \
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
                nikto -version | head -n1
                ;;
            "nuclei")
                nuclei -version | head -n1
                ;;
            "testssl.sh")
                testssl.sh --version | head -n1
                ;;
        esac
    else
        echo -e "${RED}✗${NC} $tool installation failed"
    fi
    echo "---"
done
