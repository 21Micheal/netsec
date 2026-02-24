import requests
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
import os
from pathlib import Path

class CVEDetector:
    def __init__(self):
        self.cve_db_path = "cve_database.sqlite"
        self.nvd_api_base = "https://services.nvd.nist.gov/rest/json/cves/1.0"
        self._init_database()
    
    def _init_database(self):
        """Initialize local CVE database"""
        if not os.path.exists(self.cve_db_path):
            conn = sqlite3.connect(self.cve_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cve_entries (
                    cve_id TEXT PRIMARY KEY,
                    description TEXT,
                    cvss_score REAL,
                    severity TEXT,
                    published_date TEXT,
                    last_modified TEXT,
                    products TEXT,
                    raw_data TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_vulnerabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT,
                    version TEXT,
                    cve_id TEXT,
                    FOREIGN KEY (cve_id) REFERENCES cve_entries (cve_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ CVE database initialized")
    
    def check_service_vulnerabilities(self, service_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for CVEs in a service based on product and version"""
        vulnerabilities = []
        
        product = service_info.get('product', '').lower()
        version = service_info.get('version', '')
        
        if not product or not version:
            return vulnerabilities
        
        # Clean version string
        version = self._clean_version(version)
        
        # Check common software patterns
        vulnerabilities.extend(self._check_common_software(product, version))
        
        # Check local database
        vulnerabilities.extend(self._check_local_cve_db(product, version))
        
        # Check online sources (with rate limiting)
        if len(vulnerabilities) < 5:  # Only check online if we don't have many results
            try:
                online_vulns = self._check_online_sources(product, version)
                vulnerabilities.extend(online_vulns)
            except Exception as e:
                print(f"⚠️ Online CVE check failed: {e}")
        
        return vulnerabilities
    
    def _clean_version(self, version: str) -> str:
        """Clean and normalize version strings"""
        # Remove extra text and keep version numbers
        version = re.sub(r'[^\d\.]', ' ', version)
        version = re.sub(r'\s+', ' ', version).strip()
        
        # Extract first version-like pattern
        match = re.search(r'(\d+\.\d+(?:\.\d+)?)', version)
        if match:
            return match.group(1)
        
        return version
    
    def _check_common_software(self, product: str, version: str) -> List[Dict[str, Any]]:
        """Check for vulnerabilities in common software"""
        vulnerabilities = []
        
        # Common software vulnerability patterns
        common_vulns = {
            'apache': self._check_apache_vulnerabilities,
            'nginx': self._check_nginx_vulnerabilities,
            'mysql': self._check_mysql_vulnerabilities,
            'php': self._check_php_vulnerabilities,
            'openssh': self._check_ssh_vulnerabilities,
            'wordpress': self._check_wordpress_vulnerabilities
        }
        
        for software, check_func in common_vulns.items():
            if software in product:
                vulns = check_func(version)
                vulnerabilities.extend(vulns)
        
        return vulnerabilities
    
    def _check_apache_vulnerabilities(self, version: str) -> List[Dict[str, Any]]:
        """Check Apache HTTP Server vulnerabilities"""
        vulns = []
        
        # Known vulnerable versions
        vulnerable_versions = {
            '2.4.49': 'CVE-2021-41773 - Path Traversal',
            '2.4.50': 'CVE-2021-42013 - Path Traversal',
            '2.2.': 'Multiple CVEs - End of life',
            '2.0.': 'Multiple CVEs - End of life'
        }
        
        for vuln_version, description in vulnerable_versions.items():
            if version.startswith(vuln_version):
                vulns.append({
                    'cve_id': description.split(' - ')[0],
                    'description': description,
                    'severity': 'HIGH',
                    'cvss_score': 7.5,
                    'product': 'Apache HTTP Server',
                    'version': version,
                    'source': 'known_vulnerability'
                })
        
        return vulns
    
    def _check_nginx_vulnerabilities(self, version: str) -> List[Dict[str, Any]]:
        """Check Nginx vulnerabilities"""
        vulns = []
        
        # Known vulnerable versions
        if version.startswith('1.20.0'):
            vulns.append({
                'cve_id': 'CVE-2021-23017',
                'description': 'DNS resolver vulnerability allowing cache poisoning',
                'severity': 'MEDIUM',
                'cvss_score': 6.5,
                'product': 'Nginx',
                'version': version,
                'source': 'known_vulnerability'
            })
        
        return vulns
    
    def _check_mysql_vulnerabilities(self, version: str) -> List[Dict[str, Any]]:
        """Check MySQL vulnerabilities"""
        vulns = []
        
        # Old versions with known issues
        if version.startswith('5.0') or version.startswith('5.1'):
            vulns.append({
                'cve_id': 'Multiple CVEs',
                'description': f'MySQL {version} has multiple known vulnerabilities - End of life',
                'severity': 'HIGH',
                'cvss_score': 8.0,
                'product': 'MySQL',
                'version': version,
                'source': 'end_of_life'
            })
        
        return vulns
    
    def _check_php_vulnerabilities(self, version: str) -> List[Dict[str, Any]]:
        """Check PHP vulnerabilities"""
        vulns = []
        
        # PHP 5.x end of life
        if version.startswith('5.'):
            vulns.append({
                'cve_id': 'Multiple CVEs',
                'description': f'PHP {version} is end of life with multiple unpatched vulnerabilities',
                'severity': 'HIGH',
                'cvss_score': 9.0,
                'product': 'PHP',
                'version': version,
                'source': 'end_of_life'
            })
        
        return vulns
    
    def _check_ssh_vulnerabilities(self, version: str) -> List[Dict[str, Any]]:
        """Check SSH vulnerabilities"""
        vulns = []
        
        # Old SSH versions
        if version.startswith('1.') or version.startswith('2.0'):
            vulns.append({
                'cve_id': 'Multiple CVEs',
                'description': f'SSH {version} has known cryptographic weaknesses',
                'severity': 'MEDIUM',
                'cvss_score': 5.5,
                'product': 'OpenSSH',
                'version': version,
                'source': 'weak_crypto'
            })
        
        return vulns
    
    def _check_wordpress_vulnerabilities(self, version: str) -> List[Dict[str, Any]]:
        """Check WordPress vulnerabilities"""
        vulns = []
        
        # Known vulnerable WordPress versions
        vulnerable_wp = {
            '4.0': 'Multiple XSS and privilege escalation vulnerabilities',
            '4.7': 'REST API content injection vulnerability',
            '5.0': 'Multiple security issues in early releases'
        }
        
        for wp_version, description in vulnerable_wp.items():
            if version.startswith(wp_version):
                vulns.append({
                    'cve_id': 'WordPress Security Advisory',
                    'description': f'WordPress {version}: {description}',
                    'severity': 'MEDIUM',
                    'cvss_score': 6.0,
                    'product': 'WordPress',
                    'version': version,
                    'source': 'wordpress_advisory'
                })
        
        return vulns
    
    def _check_local_cve_db(self, product: str, version: str) -> List[Dict[str, Any]]:
        """Check local CVE database"""
        vulns = []
        
        try:
            conn = sqlite3.connect(self.cve_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT cve_id, description, cvss_score, severity 
                FROM cve_entries 
                WHERE products LIKE ? OR products LIKE ?
            ''', (f'%{product}%', f'%{product} {version}%'))
            
            for row in cursor.fetchall():
                vulns.append({
                    'cve_id': row[0],
                    'description': row[1],
                    'cvss_score': row[2],
                    'severity': row[3],
                    'product': product,
                    'version': version,
                    'source': 'local_db'
                })
            
            conn.close()
        except Exception as e:
            print(f"⚠️ Local CVE database error: {e}")
        
        return vulns
    
    def _check_online_sources(self, product: str, version: str) -> List[Dict[str, Any]]:
        """Check online CVE databases (with rate limiting)"""
        vulns = []
        
        # Simulate online check - in production, you'd integrate with NVD API
        # This is a placeholder for actual API integration
        
        return vulns
    
    def calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall risk score based on vulnerabilities"""
        if not vulnerabilities:
            return {
                'risk_score': 0,
                'risk_level': 'LOW',
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0
            }
        
        severity_weights = {
            'CRITICAL': 10,
            'HIGH': 7,
            'MEDIUM': 4,
            'LOW': 1
        }
        
        counts = {severity: 0 for severity in severity_weights.keys()}
        total_score = 0
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'LOW')
            cvss_score = vuln.get('cvss_score', 0)
            
            if severity in counts:
                counts[severity] += 1
                total_score += severity_weights[severity] * (cvss_score / 10 if cvss_score else 1)
        
        # Normalize score
        max_possible_score = len(vulnerabilities) * 10
        risk_score = min(100, (total_score / max_possible_score * 100) if max_possible_score > 0 else 0)
        
        # Determine risk level
        if risk_score >= 80 or counts['CRITICAL'] > 0:
            risk_level = 'CRITICAL'
        elif risk_score >= 60 or counts['HIGH'] > 2:
            risk_level = 'HIGH'
        elif risk_score >= 40 or counts['MEDIUM'] > 3:
            risk_level = 'MEDIUM'
        elif risk_score >= 20:
            risk_level = 'LOW'
        else:
            risk_level = 'INFO'
        
        return {
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'critical_count': counts['CRITICAL'],
            'high_count': counts['HIGH'],
            'medium_count': counts['MEDIUM'],
            'low_count': counts['LOW'],
            'total_vulnerabilities': len(vulnerabilities)
        }