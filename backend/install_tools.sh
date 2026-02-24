#!/bin/bash

echo "🔧 Installing security tools safely..."

# Update system
sudo apt update

# Install basic tools from repositories
sudo apt install -y nmap nikto sqlmap dirb whatweb python3-pip

# Install nuclei using pre-built binary
echo "📥 Installing Nuclei..."
wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_3.0.0_linux_amd64.zip
unzip -q nuclei_3.0.0_linux_amd64.zip
sudo mv nuclei /usr/local/bin/
rm nuclei_3.0.0_linux_amd64.zip

# Install testssl.sh
echo "📥 Installing testssl.sh..."
git clone https://github.com/drwetter/testssl.sh.git
sudo ln -sf $(pwd)/testssl.sh/testssl.sh /usr/local/bin/testssl.sh

# Install Python dependencies
pip3 install python-nmap requests pyopensssl celery flask

# Verify installations
echo "✅ Verifying installations..."
nmap --version
nikto -version
nuclei -version
testssl.sh --version

echo "🎉 Installation complete!"
