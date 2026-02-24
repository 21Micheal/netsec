import re
import json
from typing import Dict, List, Any
from datetime import datetime

class RiskDetectionEngine:
    def __init__(self):
        self.risk_patterns = self._load_risk_patterns()
    
    def _load_risk_patterns(self) -> Dict[str, Any]:
        return {
            "weak_ssl": {
                "patterns": ["SSLv2", "SSLv3", "TLS 1.0", "weak cipher"],
                "risk_score": 40,
                "category": "cryptography"
            },
            "exposed_services": {
                "patterns": ["anonymous", "guest", "test", "demo"],
                "risk_score": 30,
                "category": "access_control"
            },
            "information_disclosure": {
                "patterns": ["version", "debug", "test", "backup"],
                "risk_score": 25,
                "category": "information_disclosure"
            },
            "default_credentials": {
                "patterns": ["admin:admin", "root:root", "user:user"],
                "risk_score": 50,
                "category": "access_control"
            }
        }
    
    def analyze_scan_results(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive risk analysis of scan results"""
        findings = []
        total_risk = 0
        
        # Analyze network scan results
        if 'nmap_results' in scan_data:
            network_findings = self._analyze_network_scan(scan_data['nmap_results'])
            findings.extend(network_findings)
            total_risk += sum(f['risk_score'] for f in network_findings)
        
        # Analyze web scan results
        if 'web_results' in scan_data:
            web_findings = self._analyze_web_scan(scan_data['web_results'])
            findings.extend(web_findings)
            total_risk += sum(f['risk_score'] for f in web_findings)
        
        # Analyze service banners
        if 'services' in scan_data:
            service_findings = self._analyze_services(scan_data['services'])
            findings.extend(service_findings)
            total_risk += sum(f['risk_score'] for f in service_findings)
        
        return {
            "risk_score": min(total_risk, 100),
            "risk_level": self._calculate_risk_level(total_risk),
            "findings": findings,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _analyze_network_scan(self, nmap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Analyze open ports
        for host in nmap_data.get('hosts', []):
            for port in host.get('ports', []):
                if port.get('state') == 'open':
                    finding = self._analyze_port(port)
                    if finding:
                        findings.append(finding)
        
        return findings
    
    def _analyze_web_scan(self, web_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Analyze HTTP headers
        headers = web_data.get('headers', {})
        if 'server' in headers:
            server = headers['server']
            if any(old in server.lower() for old in ['apache/2.2', 'nginx/1.4', 'iis/7.0']):
                findings.append({
                    "title": "Outdated Web Server",
                    "description": f"Web server version {server} may have known vulnerabilities",
                    "risk_score": 30,
                    "category": "web_server",
                    "evidence": f"Server header: {server}"
                })
        
        # Analyze security headers
        security_headers = ['x-frame-options', 'x-content-type-options', 'strict-transport-security']
        missing_headers = [h for h in security_headers if h not in headers]
        if missing_headers:
            findings.append({
                "title": "Missing Security Headers",
                "description": "Important security headers are missing",
                "risk_score": 20,
                "category": "web_security",
                "evidence": f"Missing headers: {', '.join(missing_headers)}"
            })
        
        return findings
    
    def _analyze_port(self, port_data: Dict[str, Any]) -> Dict[str, Any]:
        port = port_data.get('port')
        service = port_data.get('service', '').lower()
        banner = port_data.get('banner', '').lower()
        
        # Check for high-risk ports
        high_risk_ports = {21: 'FTP', 23: 'Telnet', 161: 'SNMP', 389: 'LDAP'}
        if port in high_risk_ports:
            return {
                "title": f"High-Risk Service: {high_risk_ports[port]}",
                "description": f"Port {port} ({high_risk_ports[port]}) is open",
                "risk_score": 25,
                "category": "network_service",
                "evidence": f"Port {port} open with service: {service}"
            }
        
        # Check service banners for risky patterns
        for pattern_name, pattern_data in self.risk_patterns.items():
            for pattern in pattern_data['patterns']:
                if pattern.lower() in banner:
                    return {
                        "title": f"Risky Configuration: {pattern_name}",
                        "description": f"Service banner contains risky pattern: {pattern}",
                        "risk_score": pattern_data['risk_score'],
                        "category": pattern_data['category'],
                        "evidence": f"Banner contains: {pattern}"
                    }
        
        return None
    
    def _analyze_services(self, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings = []
        
        for service in services:
            # Check for default credentials (simplified)
            if service.get('default_credentials'):
                findings.append({
                    "title": "Default Credentials Possible",
                    "description": "Service may be using default credentials",
                    "risk_score": 50,
                    "category": "access_control",
                    "evidence": f"Service {service.get('name')} has default credential warning"
                })
            
            # Check for outdated versions
            if self._is_outdated_version(service.get('version', '')):
                findings.append({
                    "title": "Outdated Software Version",
                    "description": "Service is running an outdated version with potential vulnerabilities",
                    "risk_score": 35,
                    "category": "software",
                    "evidence": f"Version: {service.get('version')}"
                })
        
        return findings
    
    def _is_outdated_version(self, version: str) -> bool:
        # Simple version checking logic
        outdated_indicators = ['beta', 'alpha', 'rc1', 'rc2', '0.', '1.0', '2.0', '2010', '2012']
        return any(indicator in version.lower() for indicator in outdated_indicators)
    
    def _calculate_risk_level(self, score: int) -> str:
        if score >= 80: return "CRITICAL"
        elif score >= 60: return "HIGH" 
        elif score >= 40: return "MEDIUM"
        elif score >= 20: return "LOW"
        else: return "INFO"