#!/bin/bash
echo "🏠 Testing Security Tools on LOCALHOST"
echo "======================================"

# Check if Python servers are running
echo "1. Checking local services..."
netstat -tulpn | grep -E ':8080|:8888' || echo "   Starting test servers..." && python3 -m http.server 8080 > /dev/null 2>&1 &

sleep 2

echo ""
echo "2. Testing NMAP..."
nmap -sV -p 8080,8888 127.0.0.1 | grep -E 'PORT|open|Service'

echo ""
echo "3. Testing WhatWeb..."
whatweb http://127.0.0.1:8080

echo ""
echo "4. Testing Nikto (quick scan)..."
timeout 20 nikto -h http://127.0.0.1:8080 -Tuning 1 2>/dev/null | grep -E 'Target|End Time|error' || echo "   Nikto completed or timed out"

echo ""
echo "5. Testing Nuclei (local, should be fast)..."
timeout 15 nuclei -u http://127.0.0.1:8080 -t technologies/ -silent

echo ""
echo "6. Testing testssl.sh (on non-SSL service)..."
testssl.sh --color 0 127.0.0.1:8080 2>/dev/null | head -3 || echo "   SSL test failed (expected for HTTP service)"

echo ""
echo "✅ Local tests completed!"
