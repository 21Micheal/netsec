import asyncio
import aiohttp
import subprocess
import json
from typing import List, Dict, Any
from datetime import datetime
import shodan
import censys
import os

class AdvancedReconnaissance:
    def __init__(self):
        self.shodan_api = os.getenv('SHODAN_API_KEY')
        self.censys_api_id = os.getenv('CENSYS_API_ID')
        self.censys_api_secret = os.getenv('CENSYS_API_SECRET')
    
    async def shodan_lookup(self, target: str) -> Dict[str, Any]:
        """Get Shodan intelligence for target"""
        if not self.shodan_api:
            return {"error": "Shodan API key not configured"}
        
        try:
            api = shodan.Shodan(self.shodan_api)
            result = api.host(target)
            return {
                "ports": result.get('ports', []),
                "vulnerabilities": result.get('vulns', []),
                "services": result.get('data', []),
                "isp": result.get('isp'),
                "location": result.get('location', {}),
                "last_update": result.get('last_update')
            }
        except shodan.APIError as e:
            return {"error": f"Shodan lookup failed: {str(e)}"}
    
    async def censys_lookup(self, target: str) -> Dict[str, Any]:
        """Get Censys intelligence for target"""
        if not self.censys_api_id or not self.censys_api_secret:
            return {"error": "Censys API credentials not configured"}
        
        try:
            # Censys ASM integration for attack surface management
            return {
                "services": [],
                "certificates": [],
                "risk_score": 0,
                "notes": "Censys integration placeholder"
            }
        except Exception as e:
            return {"error": f"Censys lookup failed: {str(e)}"}
    
    async def subdomain_enumeration(self, domain: str) -> List[str]:
        """Perform subdomain enumeration using multiple techniques"""
        subdomains = set()
        
        # Using subfinder
        try:
            result = subprocess.run(
                ['subfinder', '-d', domain, '-silent'],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                subdomains.update(result.stdout.strip().split('\n'))
        except Exception as e:
            print(f"Subfinder failed: {e}")
        
        # Using assetfinder
        try:
            result = subprocess.run(
                ['assetfinder', '--subs-only', domain],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                subdomains.update(result.stdout.strip().split('\n'))
        except Exception as e:
            print(f"Assetfinder failed: {e}")
        
        return list(subdomains)
    
    async def port_scan_advanced(self, target: str, profile: str = "comprehensive") -> Dict[str, Any]:
        """Advanced port scanning with service detection"""
        nmap_args = {
            "quick": ["-T4", "-F"],
            "standard": ["-sV", "-sC", "-O"],
            "comprehensive": ["-sV", "-sC", "-A", "-O", "--script=vuln"],
            "udp": ["-sU", "--top-ports", "100"]
        }
        
        from .nmap_runner import run_nmap_scan
        return run_nmap_scan(target, nmap_args.get(profile, ["-sV", "-sC"]))
    
    async def web_tech_detection(self, url: str) -> Dict[str, Any]:
        """Detect web technologies"""
        try:
            result = subprocess.run(
                ['whatweb', '--color=never', url],
                capture_output=True, text=True, timeout=60
            )
            return {
                "technologies": result.stdout.strip(),
                "error": None if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {"error": f"WhatWeb failed: {str(e)}"}

class VulnerabilityAssessor:
    def __init__(self):
        self.cve_db = {}  # Would integrate with real CVE database
    
    def assess_risk(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk based on scan findings"""
        risk_score = 0
        findings = []
        
        # Analyze open ports
        open_ports = scan_results.get('open_ports', [])
        for port in open_ports:
            if port in [21, 22, 23, 80, 443, 3389]:
                risk_score += 10
                findings.append(f"Common service port {port} open")
            
            if port in [135, 139, 445, 1433, 1521, 3306, 5432]:
                risk_score += 20
                findings.append(f"Database/service port {port} open")
        
        # Analyze services
        services = scan_results.get('services', [])
        for service in services:
            if 'ftp' in service.get('name', '').lower() and 'anonymous' in service.get('banner', '').lower():
                risk_score += 30
                findings.append("Anonymous FTP access enabled")
            
            if 'ssh' in service.get('name', '').lower() and service.get('version'):
                risk_score += 15
                findings.append(f"SSH version exposed: {service.get('version')}")
        
        return {
            "risk_score": min(risk_score, 100),
            "risk_level": self._get_risk_level(risk_score),
            "findings": findings,
            "recommendations": self._generate_recommendations(findings)
        }
    
    def _get_risk_level(self, score: int) -> str:
        if score >= 80: return "CRITICAL"
        elif score >= 60: return "HIGH"
        elif score >= 40: return "MEDIUM"
        elif score >= 20: return "LOW"
        else: return "INFO"
    
    def _generate_recommendations(self, findings: List[str]) -> List[str]:
        recommendations = []
        for finding in findings:
            if 'FTP' in finding:
                recommendations.append("Disable anonymous FTP access or use FTPS")
            if 'SSH' in finding:
                recommendations.append("Update SSH to latest version and disable weak ciphers")
            if 'Database' in finding:
                recommendations.append("Restrict database access to specific IP ranges")
        return recommendations