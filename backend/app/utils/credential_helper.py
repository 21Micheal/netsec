import paramiko
import socket
from typing import Dict, List, Any, Optional
import warnings

class CredentialTester:
    def __init__(self):
        self.common_credentials = {
            'ssh': [
                {'username': 'root', 'password': 'root'},
                {'username': 'admin', 'password': 'admin'},
                {'username': 'root', 'password': 'password'},
                {'username': 'admin', 'password': 'password'},
                {'username': 'root', 'password': '123456'},
                {'username': 'test', 'password': 'test'}
            ],
            'ftp': [
                {'username': 'anonymous', 'password': ''},
                {'username': 'ftp', 'password': 'ftp'},
                {'username': 'admin', 'password': 'admin'}
            ],
            'mysql': [
                {'username': 'root', 'password': ''},
                {'username': 'root', 'password': 'root'},
                {'username': 'admin', 'password': 'admin'}
            ]
        }
    
    def test_service_credentials(self, service_info: Dict[str, Any], max_attempts: int = 5) -> Dict[str, Any]:
        """Test common default credentials for a service"""
        service_type = service_info.get('name', '').lower()
        host = service_info.get('host', '')
        port = service_info.get('port', 0)
        
        if not host or not port:
            return {'error': 'Invalid service information'}
        
        results = {
            'service': service_type,
            'host': host,
            'port': port,
            'credentials_tested': 0,
            'vulnerable_credentials': [],
            'recommendations': []
        }
        
        try:
            if 'ssh' in service_type:
                ssh_results = self._test_ssh_credentials(host, port, max_attempts)
                results.update(ssh_results)
            elif 'ftp' in service_type:
                ftp_results = self._test_ftp_credentials(host, port, max_attempts)
                results.update(ftp_results)
            elif 'mysql' in service_type:
                mysql_results = self._test_mysql_credentials(host, port, max_attempts)
                results.update(mysql_results)
            elif 'telnet' in service_type:
                telnet_results = self._test_telnet_credentials(host, port, max_attempts)
                results.update(telnet_results)
            else:
                results['error'] = f'Credential testing not supported for {service_type}'
        
        except Exception as e:
            results['error'] = f'Credential testing failed: {str(e)}'
        
        return results
    
    def _test_ssh_credentials(self, host: str, port: int, max_attempts: int) -> Dict[str, Any]:
        """Test SSH credentials"""
        vulnerable = []
        credentials = self.common_credentials.get('ssh', [])[:max_attempts]
        
        for cred in credentials:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                ssh.connect(
                    hostname=host,
                    port=port,
                    username=cred['username'],
                    password=cred['password'],
                    timeout=10,
                    banner_timeout=20
                )
                
                # Connection successful - vulnerable!
                vulnerable.append({
                    'username': cred['username'],
                    'password': cred['password'],
                    'service': 'SSH',
                    'severity': 'HIGH'
                })
                
                ssh.close()
                break  # Stop after first successful attempt
                
            except (paramiko.AuthenticationException, paramiko.SSHException):
                continue  # Authentication failed - good!
            except Exception:
                break  # Other error - stop testing
        
        return {
            'credentials_tested': len(credentials),
            'vulnerable_credentials': vulnerable,
            'recommendations': [
                'Change default credentials',
                'Use key-based authentication',
                'Implement fail2ban or similar protection'
            ] if vulnerable else []
        }
    
    def _test_ftp_credentials(self, host: str, port: int, max_attempts: int) -> Dict[str, Any]:
        """Test FTP credentials"""
        vulnerable = []
        credentials = self.common_credentials.get('ftp', [])[:max_attempts]
        
        for cred in credentials:
            try:
                from ftplib import FTP
                
                ftp = FTP()
                ftp.connect(host, port, timeout=10)
                ftp.login(cred['username'], cred['password'])
                
                # Login successful - vulnerable!
                vulnerable.append({
                    'username': cred['username'],
                    'password': cred['password'],
                    'service': 'FTP',
                    'severity': 'HIGH' if cred['username'] != 'anonymous' else 'MEDIUM'
                })
                
                ftp.quit()
                break
                
            except Exception:
                continue
        
        return {
            'credentials_tested': len(credentials),
            'vulnerable_credentials': vulnerable,
            'recommendations': [
                'Disable anonymous FTP if not required',
                'Use strong passwords',
                'Consider using SFTP instead of FTP'
            ] if vulnerable else []
        }
    
    def _test_mysql_credentials(self, host: str, port: int, max_attempts: int) -> Dict[str, Any]:
        """Test MySQL credentials"""
        vulnerable = []
        credentials = self.common_credentials.get('mysql', [])[:max_attempts]
        
        for cred in credentials:
            try:
                # Dynamically import a MySQL client to avoid static import errors when
                # 'mysql.connector' is not installed; prefer mysql-connector-python,
                # fall back to PyMySQL if available.
                mysql_connector = None
                try:
                    import mysql.connector as mysql_connector  # type: ignore
                except Exception:
                    try:
                        import pymysql as mysql_connector  # type: ignore
                    except Exception:
                        mysql_connector = None

                if mysql_connector is None:
                    # Cannot test MySQL credentials without a MySQL client library installed.
                    raise RuntimeError("No MySQL client library available (install 'mysql-connector-python' or 'PyMySQL')")

                conn = mysql_connector.connect(
                    host=host,
                    port=port,
                    user=cred['username'],
                    password=cred['password'],
                    connection_timeout=5
                )
                
                # Connection successful - vulnerable!
                vulnerable.append({
                    'username': cred['username'],
                    'password': cred['password'],
                    'service': 'MySQL',
                    'severity': 'CRITICAL'
                })
                
                conn.close()
                break
                
            except Exception:
                continue
        
        return {
            'credentials_tested': len(credentials),
            'vulnerable_credentials': vulnerable,
            'recommendations': [
                'Change default MySQL root password',
                'Remove anonymous users',
                'Restrict network access to MySQL'
            ] if vulnerable else []
        }
    
    def _test_telnet_credentials(self, host: str, port: int, max_attempts: int) -> Dict[str, Any]:
        """Test Telnet credentials"""
        vulnerable = []
        credentials = self.common_credentials.get('ssh', [])[:max_attempts]  # Reuse SSH credentials
        
        for cred in credentials:
            try:
                tn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                tn.settimeout(10)
                tn.connect((host, port))
                
                # Read banner
                banner = tn.recv(1024).decode('utf-8', errors='ignore')
                
                # Send credentials (basic telnet simulation)
                if 'login' in banner.lower():
                    tn.send((cred['username'] + '\r\n').encode())
                    response = tn.recv(1024).decode('utf-8', errors='ignore')
                    
                    if 'password' in response.lower():
                        tn.send((cred['password'] + '\r\n').encode())
                        response = tn.recv(1024).decode('utf-8', errors='ignore')
                        
                        # If we get a prompt or successful message
                        if not ('fail' in response.lower() or 'error' in response.lower()):
                            vulnerable.append({
                                'username': cred['username'],
                                'password': cred['password'],
                                'service': 'Telnet',
                                'severity': 'CRITICAL'  # Telnet is unencrypted!
                            })
                            break
                
                tn.close()
                
            except Exception:
                continue
        
        return {
            'credentials_tested': len(credentials),
            'vulnerable_credentials': vulnerable,
            'recommendations': [
                'Disable Telnet service',
                'Use SSH instead of Telnet',
                'If Telnet is required, use strong authentication'
            ] if vulnerable else []
        }