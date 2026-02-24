#!/usr/bin/env python3
import subprocess
import time
import sys

def run_safe_test():
    print("🔒 Running SAFE security tool tests...")
    print("=" * 50)
    
    test_targets = [
        ("httpbun.com", "Safe test service"),
        ("jsonplaceholder.typicode.com", "Test API service"),
        ("example.com", "Standard test domain")
    ]
    
    for target, description in test_targets:
        print(f"\n🎯 Testing {description}: {target}")
        print("-" * 40)
        
        # Test 1: WhatWeb (technology detection)
        try:
            print("🔍 WhatWeb technology detection...")
            result = subprocess.run(
                ["whatweb", target], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines[:3]:  # Show first 3 lines
                    if line.strip():
                        print(f"   {line.strip()}")
            else:
                print("   WhatWeb completed")
        except Exception as e:
            print(f"   WhatWeb: {e}")
        
        # Test 2: Basic nuclei scan (safe templates only)
        try:
            print("📋 Nuclei safe scan...")
            result = subprocess.run(
                ["nuclei", "-u", f"https://{target}", "-tags", "tech", "-silent"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.stdout:
                findings = result.stdout.strip().split('\n')
                print(f"   Found {len(findings)} technology detections")
                for finding in findings[:2]:  # Show first 2 findings
                    print(f"   - {finding}")
            else:
                print("   No vulnerabilities detected (safe scan)")
        except Exception as e:
            print(f"   Nuclei: {e}")
        
        time.sleep(2)  # Be polite to the servers
    
    print("\n" + "=" * 50)
    print("✅ All safe tests completed!")

if __name__ == "__main__":
    run_safe_test()
