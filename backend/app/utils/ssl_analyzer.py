import ssl
import socket
from typing import Dict, List, Any
from datetime import datetime
import OpenSSL
import warnings

class SSLAnalyzer:
    def __init__(self):
        self.weak_protocols = ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']
        self.weak_ciphers = [
            'RC4', 'MD5', 'DES', '3DES', 'NULL', 'EXPORT', 'ANON',
            'CBC', 'CAMELLIA', 'SEED', 'IDEA'
        ]

    def analyze_ssl_security(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """Comprehensive SSL/TLS security analysis"""
        try:
            # Get certificate information
            cert_info = self._get_certificate_info(hostname, port)
            
            # --- NEW: Calculate certificate expiry metrics ---
            if cert_info and 'not_after' in cert_info:
                # The ISO format from the certificate often includes 'Z', indicating UTC.
                # We replace 'Z' and append the timezone info for safe comparison.
                try:
                    # Handle 'Z' and ensure timezone awareness for comparison
                    expiry_date = datetime.fromisoformat(cert_info['not_after'].replace('Z', '+00:00'))
                    
                    # Get the current time, ensuring it is also timezone-aware
                    # We use .now(expiry_date.tzinfo) to match timezones, or use utcnow() if expiry_date is reliably UTC
                    # Since 'Z' is UTC, let's ensure we compare with UTC now.
                    # A robust approach is to convert both to UTC or ensure both are timezone-aware.
                    
                    # Assuming Python 3.11+ which handles 'Z', or using the replace trick:
                    now = datetime.now(expiry_date.tzinfo) # Use the same timezone as the parsed date
                    
                    days_until_expiry = (expiry_date - now).days
                    cert_info['days_until_expiry'] = days_until_expiry
                    cert_info['has_expired'] = days_until_expiry < 0
                except ValueError:
                    # Handle cases where 'not_after' format is invalid
                    cert_info['days_until_expiry'] = 0
                    cert_info['has_expired'] = True
            else:
                # Handle case where cert_info or 'not_after' is missing
                cert_info['days_until_expiry'] = 0
                cert_info['has_expired'] = True
            # --- END NEW LOGIC ---

            # Check supported protocols
            protocol_info = self._check_supported_protocols(hostname, port)
            
            # Check cipher strength
            cipher_info = self._analyze_ciphers(hostname, port)
            
            # Generate security score (must use updated cert_info)
            security_score = self._calculate_ssl_score(cert_info, protocol_info, cipher_info)
            
            return {
                'hostname': hostname,
                'port': port,
                'analysis_time': datetime.utcnow().isoformat(),
                'certificate': cert_info,
                'protocols': protocol_info,
                'ciphers': cipher_info,
                'security_score': security_score,
                'vulnerabilities': self._identify_ssl_vulnerabilities(cert_info, protocol_info, cipher_info)
            }
            
        except Exception as e:
            return {
                'hostname': hostname,
                'port': port,
                'error': f"SSL analysis failed: {str(e)}",
                'analysis_time': datetime.utcnow().isoformat()
            }
    
    def _get_certificate_info(self, hostname: str, port: int) -> Dict[str, Any]:
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_bin = ssock.getpeercert(binary_form=True)
                    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_bin)
                    
                    # Parse certificate details
                    subject = dict(x[0] for x in cert.get_subject().get_components())
                    issuer = dict(x[0] for x in cert.get_issuer().get_components())
                    
                    return {
                        'subject': subject,
                        'issuer': issuer,
                        'serial_number': cert.get_serial_number(),
                        'version': cert.get_version(),
                        'not_before': cert.get_notBefore().decode('utf-8'),
                        'not_after': cert.get_notAfter().decode('utf-8'),
                        'signature_algorithm': cert.get_signature_algorithm().decode('utf-8'),
                        'has_expired': cert.has_expired(),
                        'days_until_expiry': self._days_until_expiry(cert.get_notAfter().decode('utf-8'))
                    }
                    
        except Exception as e:
            return {'error': f"Certificate analysis failed: {str(e)}"}
    
    def _days_until_expiry(self, not_after: str) -> int:
        """Calculate days until certificate expiry"""
        try:
            expiry_date = datetime.strptime(not_after, '%Y%m%d%H%M%SZ')
            now = datetime.utcnow()
            return (expiry_date - now).days
        except:
            return -1
    
    def _check_supported_protocols(self, hostname: str, port: int) -> Dict[str, Any]:
        """Check which SSL/TLS protocols are supported"""
        protocols = {
            'SSLv2': False,
            'SSLv3': False,
            'TLSv1': False,
            'TLSv1.1': False,
            'TLSv1.2': False,
            'TLSv1.3': False
        }
        
        for protocol_name in protocols.keys():
            try:
                context = ssl.SSLContext(getattr(ssl, f'PROTOCOL_{protocol_name.upper().replace("V", "_")}'))
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        protocols[protocol_name] = True
            except:
                protocols[protocol_name] = False
        
        return {
            'supported_protocols': protocols,
            'weak_protocols_enabled': any(protocols[proto] for proto in self.weak_protocols),
            'recommended_protocols': ['TLSv1.2', 'TLSv1.3']
        }
    
    def _analyze_ciphers(self, hostname: str, port: int) -> Dict[str, Any]:
        """Analyze SSL/TLS cipher strength"""
        try:
            context = ssl.create_default_context()
            context.set_ciphers('ALL:@SECLEVEL=0')  # Allow weak ciphers for testing
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cipher = ssock.cipher()
                    
                    return {
                        'current_cipher': cipher[0] if cipher else 'Unknown',
                        'protocol_version': cipher[1] if cipher else 'Unknown',
                        'key_bits': cipher[2] if cipher else 0,
                        'is_weak': self._is_weak_cipher(cipher[0] if cipher else ''),
                        'weak_ciphers_detected': self._check_weak_ciphers(hostname, port)
                    }
                    
        except Exception as e:
            return {'error': f"Cipher analysis failed: {str(e)}"}
    
    def _is_weak_cipher(self, cipher_name: str) -> bool:
        """Check if cipher is considered weak"""
        return any(weak in cipher_name.upper() for weak in self.weak_ciphers)
    
    def _check_weak_ciphers(self, hostname: str, port: int) -> List[str]:
        """Check for specific weak ciphers"""
        weak_ciphers_found = []
        
        for cipher_suite in ['RC4', 'DES', '3DES']:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                context.set_ciphers(cipher_suite)
                
                with socket.create_connection((hostname, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        weak_ciphers_found.append(cipher_suite)
            except:
                continue
        
        return weak_ciphers_found
    
    def _calculate_ssl_score(self, cert_info: Dict, protocol_info: Dict, cipher_info: Dict) -> float:
        """Calculate SSL/TLS security score (0-100)"""
        score = 100
        
        # Certificate checks
        if cert_info.get('has_expired', False):
            score -= 30
        elif cert_info.get('days_until_expiry', 0) < 30:
            score -= 20
        elif cert_info.get('days_until_expiry', 0) < 90:
            score -= 10
        
        # Protocol checks
        if protocol_info.get('weak_protocols_enabled', False):
            score -= 25
        
        # Cipher checks
        if cipher_info.get('is_weak', False):
            score -= 20
        if cipher_info.get('weak_ciphers_detected', []):
            score -= len(cipher_info['weak_ciphers_detected']) * 5
        
        return max(0, min(100, score))
    
    def _identify_ssl_vulnerabilities(self, cert_info: Dict, protocol_info: Dict, cipher_info: Dict) -> List[Dict[str, Any]]:
        """Identify specific SSL/TLS vulnerabilities"""
        vulnerabilities = []
        
        # Certificate issues
        if cert_info.get('has_expired', False):
            vulnerabilities.append({
                'type': 'EXPIRED_CERTIFICATE',
                'severity': 'HIGH',
                'description': 'SSL certificate has expired',
                'recommendation': 'Renew the SSL certificate immediately'
            })
        
        if cert_info.get('days_until_expiry', 0) < 30:
            vulnerabilities.append({
                'type': 'CERTIFICATE_EXPIRING_SOON',
                'severity': 'MEDIUM',
                'description': f"SSL certificate expires in {cert_info['days_until_expiry']} days",
                'recommendation': 'Renew the SSL certificate'
            })
        
        # Protocol issues
        if protocol_info.get('weak_protocols_enabled', False):
            vulnerabilities.append({
                'type': 'WEAK_SSL_PROTOCOLS',
                'severity': 'HIGH',
                'description': 'Weak SSL/TLS protocols (SSLv3, TLSv1.0, TLSv1.1) are enabled',
                'recommendation': 'Disable weak protocols and use only TLSv1.2+'
            })
        
        # Cipher issues
        if cipher_info.get('is_weak', False):
            vulnerabilities.append({
                'type': 'WEAK_CIPHER_SUITE',
                'severity': 'MEDIUM',
                'description': f"Weak cipher suite in use: {cipher_info.get('current_cipher', 'Unknown')}",
                'recommendation': 'Use strong cipher suites (AES-GCM, ChaCha20)'
            })
        
        if cipher_info.get('weak_ciphers_detected', []):
            vulnerabilities.append({
                'type': 'WEAK_CIPHERS_ENABLED',
                'severity': 'MEDIUM',
                'description': f"Weak ciphers enabled: {', '.join(cipher_info['weak_ciphers_detected'])}",
                'recommendation': 'Disable weak ciphers (RC4, DES, 3DES)'
            })
        
        return vulnerabilities