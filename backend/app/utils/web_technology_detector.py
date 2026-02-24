import requests
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import ssl
import socket
from datetime import datetime

class WebTechnologyDetector:
    def __init__(self):
        self.technology_patterns = self._load_technology_patterns()
    
    def _load_technology_patterns(self) -> Dict[str, Any]:
        """Load technology detection patterns"""
        return {
            'cms': {
                'wordpress': [
                    r'wp-content', r'wp-includes', r'wordpress',
                    r'/wp-admin/', r'name="generator" content="WordPress'
                ],
                'drupal': [
                    r'drupal', r'sites/all/', r'/sites/default/',
                    r'name="Generator" content="Drupal'
                ],
                'joomla': [
                    r'joomla', r'/media/jui/', r'/media/system/',
                    r'name="generator" content="Joomla'
                ]
            },
            'frameworks': {
                'django': [r'csrf_token', r'django', r'__admin__'],
                'rails': [r'rails', r'csrf-param', r'ruby on rails'],
                'laravel': [r'laravel', r'csrf-token'],
                'express': [r'express', r'x-powered-by: express'],
                'spring': [r'spring', r'jsessionid']
            },
            'frontend': {
                'react': [r'react', r'__next', r'react-dom'],
                'vue': [r'vue', r'vue-router', r'vuex'],
                'angular': [r'angular', r'ng-', r'angularjs']
            },
            'servers': {
                'apache': [r'apache', r'server: apache'],
                'nginx': [r'nginx', r'server: nginx'],
                'iis': [r'microsoft-iis', r'server: microsoft-iis'],
                'tomcat': [r'apache-coyote', r'tomcat']
            }
        }
    
    def comprehensive_web_scan(self, url: str) -> Dict[str, Any]:
        """Comprehensive web technology detection"""
        try:
            # Ensure URL has scheme
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            results = {
                'url': url,
                'scan_time': datetime.utcnow().isoformat(),
                'technologies': [],
                'security_headers': {},
                'ssl_info': {},
                'server_info': {},
                'content_analysis': {},
                'vulnerability_indicators': []
            }
            
            # Test both HTTP and HTTPS
            for protocol in ['https', 'http']:
                test_url = f"{protocol}://{url.split('://')[-1]}" if '://' in url else f"{protocol}://{url}"
                
                try:
                    response = self._make_request(test_url)
                    if response:
                        results.update(self._analyze_response(response, test_url))
                        break
                except Exception as e:
                    continue
            
            # Additional security checks
            results['vulnerability_indicators'] = self._check_web_vulnerabilities(results)
            
            return results
            
        except Exception as e:
            return {'error': f'Web scan failed: {str(e)}'}
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with proper headers"""
        try:
            response = requests.get(
                url,
                timeout=10,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                verify=False
            )
            return response
        except Exception:
            return None
    
    def _analyze_response(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """Analyze HTTP response for technology detection"""
        analysis = {
            'final_url': response.url,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text[:5000],  # First 5000 chars for analysis
            'technologies': self._detect_technologies(response),
            'security_headers': self._analyze_security_headers(response.headers),
            'server_info': self._analyze_server_info(response.headers),
            'content_analysis': self._analyze_content(response.text)
        }
        
        # Get SSL info for HTTPS
        if url.startswith('https://'):
            domain = response.url.split('://')[1].split('/')[0]
            analysis['ssl_info'] = self._get_ssl_info(domain)
        
        return analysis
    
    def _detect_technologies(self, response: requests.Response) -> List[Dict[str, Any]]:
        """Detect web technologies from response"""
        technologies = []
        headers = response.headers
        content = response.text.lower()
        server_header = headers.get('Server', '').lower()
        x_powered_by = headers.get('X-Powered-By', '').lower()
        
        # Check all technology categories
        for category, techs in self.technology_patterns.items():
            for tech, patterns in techs.items():
                confidence = 0
                
                # Check headers
                if any(pattern in server_header for pattern in patterns):
                    confidence += 30
                if any(pattern in x_powered_by for pattern in patterns):
                    confidence += 20
                
                # Check content
                if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                    confidence += 50
                
                if confidence > 0:
                    technologies.append({
                        'name': tech,
                        'category': category,
                        'confidence': min(confidence, 100),
                        'evidence': self._get_evidence(tech, response)
                    })
        
        return technologies
    
    def _get_evidence(self, technology: str, response: requests.Response) -> List[str]:
        """Get evidence for detected technology"""
        evidence = []
        content = response.text.lower()
        headers = {k.lower(): v for k, v in response.headers.items()}
        
        patterns = []
        for category_techs in self.technology_patterns.values():
            if technology in category_techs:
                patterns = category_techs[technology]
                break
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                evidence.append(f"Content pattern: {pattern}")
            if any(pattern in header.lower() for header in [headers.get('server', ''), headers.get('x-powered-by', '')]):
                evidence.append(f"Header pattern: {pattern}")
        
        return evidence[:3]  # Return top 3 evidence items
    
    def _analyze_security_headers(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze security headers"""
        security_headers = {
            'Content-Security-Policy': headers.get('Content-Security-Policy'),
            'X-Frame-Options': headers.get('X-Frame-Options'),
            'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
            'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
            'X-XSS-Protection': headers.get('X-XSS-Protection'),
            'Referrer-Policy': headers.get('Referrer-Policy'),
            'Permissions-Policy': headers.get('Permissions-Policy')
        }
        
        # Calculate security score
        present_headers = [h for h in security_headers.values() if h]
        score = (len(present_headers) / len(security_headers)) * 100
        
        return {
            'headers': {k: v for k, v in security_headers.items() if v},
            'missing_headers': [k for k, v in security_headers.items() if not v],
            'security_score': round(score, 2)
        }
    
    def _analyze_server_info(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze server information"""
        server = headers.get('Server', '')
        powered_by = headers.get('X-Powered-By', '')
        
        return {
            'server': server,
            'x_powered_by': powered_by,
            'server_disclosed': bool(server),
            'technology_disclosed': bool(powered_by)
        }
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze page content"""
        analysis = {
            'content_length': len(content),
            'has_forms': '<form' in content.lower(),
            'has_inputs': '<input' in content.lower(),
            'has_javascript': '<script' in content.lower(),
            'has_comments': '<!--' in content,
            'estimated_technologies': []
        }
        
        # Simple content-based technology detection
        if 'react' in content.lower():
            analysis['estimated_technologies'].append('react')
        if 'vue' in content.lower():
            analysis['estimated_technologies'].append('vue')
        if 'angular' in content.lower():
            analysis['estimated_technologies'].append('angular')
        
        return analysis
    
    def _get_ssl_info(self, domain: str) -> Dict[str, Any]:
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'valid_from': cert['notBefore'],
                        'valid_until': cert['notAfter'],
                        'san': cert.get('subjectAltName', [])
                    }
        except Exception as e:
            return {'error': str(e)}
    
    def _check_web_vulnerabilities(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for common web vulnerabilities"""
        vulnerabilities = []
        
        # Check for missing security headers
        security_headers = scan_results.get('security_headers', {})
        missing_headers = security_headers.get('missing_headers', [])
        
        for header in missing_headers:
            if header == 'Strict-Transport-Security':
                vulnerabilities.append({
                    'type': 'MISSING_HSTS',
                    'severity': 'HIGH',
                    'message': 'Missing HSTS header - allows SSL stripping attacks',
                    'recommendation': 'Implement Strict-Transport-Security with max-age'
                })
            elif header == 'Content-Security-Policy':
                vulnerabilities.append({
                    'type': 'MISSING_CSP',
                    'severity': 'MEDIUM',
                    'message': 'Missing Content Security Policy header',
                    'recommendation': 'Implement CSP to prevent XSS attacks'
                })
        
        # Check server information disclosure
        server_info = scan_results.get('server_info', {})
        if server_info.get('server_disclosed'):
            vulnerabilities.append({
                'type': 'SERVER_INFO_DISCLOSURE',
                'severity': 'LOW',
                'message': f'Server version disclosed: {server_info.get("server")}',
                'recommendation': 'Hide server version information'
            })
        
        return vulnerabilities