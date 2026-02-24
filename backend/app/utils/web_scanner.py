import requests
import socket
from typing import Dict, Any, List
from urllib.parse import urlparse
import ssl
import time
from datetime import datetime

def run_web_security_scan(url: str, job_id: str = None) -> Dict[str, Any]:
    """
    Enhanced web security scanner with better logging
    """
    print(f"🌐 Starting web scan for: {url}")
    
    try:
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc
        
        print(f"🔧 Testing domain: {base_domain}")
        
        results = {
            'url': url,
            'base_domain': base_domain,
            'scan_time': datetime.utcnow().isoformat(),
            'accessible': False,
            'error': None,
            'status_code': None,
            'headers': {},
            'cookies': {},
            'security_headers': {},
            'ssl_info': {},
            'response_time': None,
        }
        
        # Test both HTTP and HTTPS
        protocols_to_test = ['https', 'http']
        
        for protocol in protocols_to_test:
            test_url = f"{protocol}://{base_domain}"
            print(f"🔄 Testing {test_url}...")
            
            try:
                start_time = time.time()
                
                response = requests.get(
                    test_url,
                    timeout=10,
                    allow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    },
                    verify=False
                )
                
                response_time = time.time() - start_time
                
                print(f"✅ {test_url} responded with status: {response.status_code}")
                
                results.update({
                    'accessible': True,
                    'final_url': response.url,
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'cookies': {cookie.name: cookie.value for cookie in response.cookies},
                    'response_time': response_time,
                    'content_length': len(response.content),
                    'used_protocol': protocol
                })
                
                # Extract security headers
                results['security_headers'] = extract_security_headers(response.headers)
                print(f"🔒 Security headers score: {results['security_headers'].get('score', 0)}")
                
                break  # Stop after first successful protocol
                
            except requests.exceptions.SSLError as e:
                print(f"⚠️ SSL Error for {test_url}: {e}")
                results['error'] = f"SSL Error: {str(e)}"
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"⚠️ Connection Error for {test_url}: {e}")
                results['error'] = f"Connection Error: {str(e)}"
                continue
            except requests.exceptions.Timeout as e:
                print(f"⚠️ Timeout for {test_url}: {e}")
                results['error'] = f"Timeout: {str(e)}"
                continue
            except Exception as e:
                print(f"⚠️ Other error for {test_url}: {e}")
                results['error'] = f"Request failed: {str(e)}"
                continue
        
        print(f"📊 Web scan completed: accessible={results['accessible']}, status={results['status_code']}")
        return results
        
    except Exception as e:
        print(f"❌ Web scan failed completely: {e}")
        return {
            'url': url,
            'accessible': False,
            'error': f"Scan failed: {str(e)}",
            'scan_time': datetime.utcnow().isoformat()
        }
def extract_security_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    """Extract and analyze security headers"""
    security_headers = {}
    missing_headers = []
    
    important_headers = [
        'Content-Security-Policy',
        'X-Frame-Options', 
        'X-Content-Type-Options',
        'Strict-Transport-Security',
        'X-XSS-Protection',
        'Referrer-Policy',
        'Permissions-Policy'
    ]
    
    for header in important_headers:
        if header in headers:
            security_headers[header] = headers[header]
        else:
            missing_headers.append(header)
    
    security_headers['missing_headers'] = missing_headers
    security_headers['score'] = len(security_headers) - len(missing_headers)  # Simple score
    
    return security_headers

def get_ssl_info(domain: str) -> Dict[str, Any]:
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
                    'version': cert.get('version', 'Unknown'),
                    'san': cert.get('subjectAltName', [])
                }
    except Exception as e:
        return {'error': str(e)}

def detect_technologies(headers: Dict[str, str], content: str) -> List[str]:
    """Simple technology detection based on headers and content"""
    technologies = []
    content_lower = content.lower()
    
    # Server detection
    server = headers.get('Server', '').lower()
    if 'apache' in server:
        technologies.append('Apache')
    elif 'nginx' in server:
        technologies.append('Nginx')
    elif 'iis' in server:
        technologies.append('IIS')
    
    # Framework detection from headers and content
    if 'x-powered-by' in headers:
        powered_by = headers['x-powered-by'].lower()
        if 'php' in powered_by:
            technologies.append('PHP')
        if 'asp.net' in powered_by:
            technologies.append('ASP.NET')
    
    # Content-based detection
    if 'wp-content' in content_lower or 'wordpress' in content_lower:
        technologies.append('WordPress')
    if 'react' in content_lower:
        technologies.append('React')
    if 'vue' in content_lower:
        technologies.append('Vue.js')
    if 'angular' in content_lower:
        technologies.append('Angular')
    
    return technologies

def analyze_headers_and_cookies(web_results: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced header and cookie analysis"""
    issues = []
    warnings = []
    
    headers = web_results.get('headers', {})
    cookies = web_results.get('cookies', {})
    security_headers = web_results.get('security_headers', {})
    
    # Check for missing security headers
    missing_headers = security_headers.get('missing_headers', [])
    for header in missing_headers:
        if header == 'Strict-Transport-Security':
            issues.append({
                'type': 'MISSING_HSTS',
                'severity': 'HIGH',
                'message': 'Missing HSTS header - allows SSL stripping attacks',
                'recommendation': 'Implement Strict-Transport-Security header'
            })
        elif header == 'Content-Security-Policy':
            issues.append({
                'type': 'MISSING_CSP',
                'severity': 'MEDIUM', 
                'message': 'Missing Content Security Policy header',
                'recommendation': 'Implement CSP to prevent XSS attacks'
            })
        else:
            warnings.append({
                'type': f'MISSING_{header.upper().replace("-", "_")}',
                'severity': 'LOW',
                'message': f'Missing {header} security header',
                'recommendation': f'Consider implementing {header} header'
            })
    
    # Check for insecure cookies
    for cookie_name, cookie_value in cookies.items():
        # This is a simplified check - in reality you'd need to parse Set-Cookie headers
        warnings.append({
            'type': 'COOKIE_DETECTED',
            'severity': 'INFO',
            'message': f'Cookie detected: {cookie_name}',
            'recommendation': 'Ensure cookies have Secure and HttpOnly flags when appropriate'
        })
    
    # Check server information disclosure
    server = headers.get('Server', '')
    if server and server not in ['', 'None']:
        warnings.append({
            'type': 'SERVER_INFO_DISCLOSURE',
            'severity': 'LOW',
            'message': f'Server version disclosed: {server}',
            'recommendation': 'Consider hiding server version information'
        })
    
    return {
        'issues': issues,
        'warnings': warnings,
        'security_score': security_headers.get('score', 0),
        'total_issues': len(issues) + len(warnings)
    }