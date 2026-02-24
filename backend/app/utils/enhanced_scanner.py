import subprocess
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime
import re
import time

class EnhancedServiceDetector:
    def __init__(self):
        self.service_signatures = self._load_service_signatures()
    
    def _load_service_signatures(self) -> Dict[str, Any]:
        """Load service detection signatures"""
        return {
            'web_servers': {
                'apache': ['Apache', 'Apache/2', 'httpd'],
                'nginx': ['nginx'],
                'iis': ['Microsoft-IIS', 'IIS'],
                'tomcat': ['Apache-Coyote', 'Tomcat'],
                'node': ['Node.js', 'Express']
            },
            'databases': {
                'mysql': ['MySQL', 'mariadb'],
                'postgresql': ['PostgreSQL', 'Postgres'],
                'mongodb': ['MongoDB'],
                'redis': ['Redis'],
                'elasticsearch': ['Elasticsearch']
            },
            'frameworks': {
                'wordpress': ['wp-content', 'wordpress'],
                'drupal': ['Drupal'],
                'joomla': ['Joomla'],
                'django': ['Django', 'CSRF_TOKEN'],
                'rails': ['Ruby on Rails', 'rails']
            }
        }
    
    # def enhanced_nmap_scan(self, target: str, profile: str = "comprehensive") -> Dict[str, Any]:
    #     """Enhanced nmap scan with detailed service detection"""
    #     nmap_args = self._get_enhanced_nmap_args(profile)
        
    #     try:
    #         # Run nmap with detailed output
    #         cmd = ['nmap', '-oX', '-'] + nmap_args + [target]
    #         result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
    #         if result.returncode != 0:
    #             return {"error": f"Nmap failed: {result.stderr}"}
            
    #         return self._parse_enhanced_nmap_xml(result.stdout, target)
            
    #     except subprocess.TimeoutExpired:
    #         return {"error": "Nmap scan timed out"}
    #     except Exception as e:
    #         return {"error": f"Scan failed: {str(e)}"}
    
    def _get_enhanced_nmap_args(self, profile: str) -> List[str]:
        """Get nmap arguments based on scan profile - OPTIMIZED"""
        profiles = {
            "quick": [
                "-T4", "-F",  # Fast scan - top 100 ports
                "-sV", "--version-intensity", "3",
                "--disable-arp-ping", "--unprivileged",
                "--host-timeout", "5m"  # Timeout per host
            ],
            "standard": [
                "-T4", 
                "-sV", "-sC", "--version-intensity", "5",
                "-p", "1-1000,3000-4000,5000-6000,8000-9000",  # Common service ports
                "--disable-arp-ping", "--unprivileged",
                "--host-timeout", "10m"
            ],
            "comprehensive": [
                "-T4",
                "-sV", "-sC", "--version-intensity", "7",
                "-p", "1-10000,161,162,1433,1521,3306,3389,5432",  # Extended range + common DB ports
                "--script", "banner,http-enum,http-headers,http-title,ssl-enum-ciphers,http-methods",
                "--disable-arp-ping", "--unprivileged", 
                "--host-timeout", "15m"
            ],
            "comprehensive_safe": [
                "-T4",
                "-sV", "-sC", "--version-intensity", "7",
                "-p", "1-5000,8000-9000",  # Safe range that's still comprehensive
                "--script", "banner,http-enum,http-headers,http-title,ssl-enum-ciphers,http-methods",
                "--disable-arp-ping", "--unprivileged",
                "--host-timeout", "10m"
            ],
            "web_scan": [
                "-T4",
                "-sV", "-sC", 
                "-p", "80,443,8080,8443,8000,8008,3000,5000,9000",  # Common web ports
                "--script", "http-enum,http-headers,http-title,http-methods,http-security-headers",
                "--disable-arp-ping", "--unprivileged",
                "--host-timeout", "5m"
            ],
            "service_detection": [
                "-T4",
                "-sV", "-sC", "--version-intensity", "7",
                "-p", "21-23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,1723,3306,3389,5432,5900,6379,27017",  # Common services
                "--script", "banner,ssh2-enum-algos,ssl-enum-ciphers",
                "--disable-arp-ping", "--unprivileged",
                "--host-timeout", "8m"
            ]
        }
        return profiles.get(profile, profiles["standard"])

    def enhanced_nmap_scan(self, target: str, profile: str = "comprehensive_safe") -> Dict[str, Any]:
        """
        Enhanced nmap scan combining smart port selection with robust execution.
        For comprehensive profiles, it performs a quick discovery scan first 
        to narrow down the ports for the main, in-depth nmap analysis, 
        significantly reducing scan time. Includes a 20-minute timeout.
        """
        
        # Import needed for SmartPortScanner usage
        from .smart_port_scanner import SmartPortScanner
        
        # --- SMART PORT DISCOVERY LOGIC ---
        if profile in ['comprehensive', 'comprehensive_safe']:
            smart_scanner = SmartPortScanner()
            print("🔍 Performing quick port discovery...")
            
            # Use a quick, lightweight scan to find open ports
            open_ports = smart_scanner.quick_port_discovery(target)
            
            if open_ports:
                print(f"🎯 Found {len(open_ports)} open ports, focusing scan on them")
                # Build custom port range based on discovery
                port_range = ','.join(map(str, open_ports))
                
                # Get the standard arguments (which may include a default port range)
                nmap_args = self._get_enhanced_nmap_args('standard')
                
                # Remove any existing '-p' argument to use our custom range
                nmap_args = [arg for arg in nmap_args if not arg.startswith('-p')]
                nmap_args.extend(['-p', port_range])
            else:
                print("🔄 No open ports found quickly, using standard comprehensive range")
                # Use the original profile arguments if quick discovery fails
                nmap_args = self._get_enhanced_nmap_args(profile)
        else:
            # For non-comprehensive profiles (e.g., standard, quick), use the profile's default arguments
            nmap_args = self._get_enhanced_nmap_args(profile)
        # --- END SMART PORT DISCOVERY LOGIC ---

        # --- NMAP EXECUTION LOGIC ---
        try:
            print(f"🔄 Running nmap with {len(nmap_args)} args: {' '.join(nmap_args)}")
            print(f"🎯 Target: {target}, Profile: {profile}")
            
            # Construct the full command
            cmd = ['nmap', '-oX', '-'] + nmap_args + [target]
            
            # Run with a 20-minute timeout
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
            
            scan_duration = time.time() - start_time
            print(f"⏱️  Scan completed in {scan_duration:.1f} seconds")
            
            # Check for common errors
            if "requires root privileges" in result.stderr:
                print("⚠️  Root privileges required, using fallback arguments")
                return self._fallback_scan(target, profile)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                return {"error": f"Nmap failed: {error_msg}"}
            
            # Parse the XML output
            return self._parse_enhanced_nmap_xml(result.stdout, target)
            
        except subprocess.TimeoutExpired:
            print("⏰ Nmap scan timed out")
            return {"error": "Nmap scan timed out after 20 minutes"}
        except Exception as e:
            print(f"💥 Scan failed: {str(e)}")
            return {"error": f"Scan failed: {str(e)}"}

    def _fallback_scan(self, target: str, profile: str) -> Dict[str, Any]:
        """Fallback scan when root privileges aren't available"""
        print("🛡️  Using fallback scan without privileged operations")
        
        # Use faster, safer arguments
        fallback_args = [
            "-T4", 
            "-sV", "--version-intensity", "5",
            "-p", "1-1000,3000-4000,8000-9000",  # Limited port range
            "--disable-arp-ping", "--unprivileged",
            "--host-timeout", "5m"
        ]
        
        cmd = ['nmap', '-oX', '-'] + fallback_args + [target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10min timeout
        
        if result.returncode == 0:
            return self._parse_enhanced_nmap_xml(result.stdout, target)
        else:
            return {"error": f"Fallback scan failed: {result.stderr.strip()}"}
    
    def _parse_enhanced_nmap_xml(self, xml_output: str, target: str) -> Dict[str, Any]:
        """Parse nmap XML output with enhanced service detection"""
        try:
            root = ET.fromstring(xml_output)
            scan_data = {
                "target": target,
                "scan_time": datetime.utcnow().isoformat(),
                "nmap_version": root.get('version', ''),
                "scan_args": root.get('args', ''),
                "hosts": [],
                "summary": {
                    "total_hosts": 0,
                    "up_hosts": 0,
                    "open_ports": 0,
                    "services_detected": 0
                }
            }
            
            for host in root.findall('host'):
                host_data = self._parse_host(host)
                if host_data:
                    scan_data["hosts"].append(host_data)
                    if host_data["status"] == "up":
                        scan_data["summary"]["up_hosts"] += 1
                    scan_data["summary"]["open_ports"] += len(host_data.get("ports", []))
                    scan_data["summary"]["services_detected"] += len(host_data.get("services", []))
            
            scan_data["summary"]["total_hosts"] = len(scan_data["hosts"])
            return scan_data
            
        except Exception as e:
            return {"error": f"XML parsing failed: {str(e)}"}
    
    def _parse_host(self, host_elem) -> Dict[str, Any]:
        """Parse individual host data with enhanced service information"""
        host_data = {
            "address": "",
            "hostnames": [],
            "status": "unknown",
            "os_info": {},
            "ports": [],
            "services": []
        }
        
        # Get address
        address_elem = host_elem.find('address')
        if address_elem is not None:
            host_data["address"] = address_elem.get('addr', '')
        
        # Get hostnames
        for hostname_elem in host_elem.findall('hostnames/hostname'):
            host_data["hostnames"].append({
                "name": hostname_elem.get('name', ''),
                "type": hostname_elem.get('type', '')
            })
        
        # Get status
        status_elem = host_elem.find('status')
        if status_elem is not None:
            host_data["status"] = status_elem.get('state', 'unknown')
        
        # Get OS information
        os_elem = host_elem.find('os')
        if os_elem is not None:
            host_data["os_info"] = self._parse_os_info(os_elem)
        
        # Get ports and services
        ports_elem = host_elem.find('ports')
        if ports_elem is not None:
            ports_data = self._parse_ports(ports_elem)
            host_data["ports"] = ports_data["ports"]
            host_data["services"] = ports_data["services"]
        
        return host_data
    
    def _parse_os_info(self, os_elem) -> Dict[str, Any]:
        """Parse OS fingerprinting information"""
        os_info = {
            "matches": [],
            "fingerprint": ""
        }
        
        for os_match in os_elem.findall('osmatch'):
            match_data = {
                "name": os_match.get('name', ''),
                "accuracy": os_match.get('accuracy', ''),
                "line": os_match.get('line', '')
            }
            os_info["matches"].append(match_data)
        
        os_class = os_elem.find('osclass')
        if os_class is not None:
            os_info.update({
                "type": os_class.get('type', ''),
                "vendor": os_class.get('vendor', ''),
                "os_family": os_class.get('osfamily', ''),
                "accuracy": os_class.get('accuracy', '')
            })
        
        return os_info
    
    def _parse_ports(self, ports_elem) -> Dict[str, Any]:
        """Parse port and service information with enhanced detection"""
        ports = []
        services = []
        
        for port_elem in ports_elem.findall('port'):
            port_data = self._parse_port(port_elem)
            if port_data:
                ports.append(port_data)
                
                # Enhanced service detection
                service_info = self._enhance_service_detection(port_data)
                if service_info:
                    services.append(service_info)
        
        return {"ports": ports, "services": services}
    
    def _parse_port(self, port_elem) -> Dict[str, Any]:
        """Parse individual port information"""
        port_data = {
            "port": int(port_elem.get('portid', 0)),
            "protocol": port_elem.get('protocol', ''),
            "state": "unknown",
            "service": {},
            "script_outputs": []
        }
        
        # Get port state
        state_elem = port_elem.find('state')
        if state_elem is not None:
            port_data["state"] = state_elem.get('state', 'unknown')
        
        # Get service information
        service_elem = port_elem.find('service')
        if service_elem is not None:
            port_data["service"] = {
                "name": service_elem.get('name', ''),
                "product": service_elem.get('product', ''),
                "version": service_elem.get('version', ''),
                "extrainfo": service_elem.get('extrainfo', ''),
                "ostype": service_elem.get('ostype', ''),
                "method": service_elem.get('method', ''),
                "conf": service_elem.get('conf', '')
            }
        
        # Get script outputs
        for script_elem in port_elem.findall('script'):
            script_data = {
                "id": script_elem.get('id', ''),
                "output": script_elem.get('output', ''),
                "elements": {}
            }
            port_data["script_outputs"].append(script_data)
        
        return port_data
    
    def _enhance_service_detection(self, port_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enhanced service detection with technology stack analysis"""
        if port_data["state"] != "open":
            return None
        
        service = port_data.get("service", {})
        service_name = service.get("name", "").lower()
        product = service.get("product", "").lower()
        version = service.get("version", "")
        
        # Detect technology stack
        technologies = self._detect_technologies(service_name, product, version)
        vulnerabilities = self._check_common_vulnerabilities(product, version)
        
        if not technologies and not vulnerabilities:
            return None
        
        return {
            "port": port_data["port"],
            "protocol": port_data["protocol"],
            "base_service": service_name,
            "product": product,
            "version": version,
            "technologies": technologies,
            "vulnerability_indicators": vulnerabilities,
            "confidence": service.get("conf", "0")
        }
    
    def _detect_technologies(self, service_name: str, product: str, version: str) -> List[str]:
        """Detect specific technologies and frameworks"""
        technologies = []
        full_text = f"{service_name} {product} {version}".lower()
        
        # Check web servers
        for server, patterns in self.service_signatures['web_servers'].items():
            if any(pattern.lower() in full_text for pattern in patterns):
                technologies.append(server)
        
        # Check databases
        for db, patterns in self.service_signatures['databases'].items():
            if any(pattern.lower() in full_text for pattern in patterns):
                technologies.append(db)
        
        # Check frameworks (requires additional probing)
        if service_name in ['http', 'https', 'www', 'http-alt']:
            frameworks = self._detect_web_frameworks(full_text)
            technologies.extend(frameworks)
        
        return list(set(technologies))
    
    def _detect_web_frameworks(self, service_info: str) -> List[str]:
        """Detect web application frameworks"""
        frameworks = []
        
        # Simple pattern matching - in real implementation, you'd make HTTP requests
        framework_patterns = {
            'wordpress': ['wp-content', 'wordpress'],
            'drupal': ['drupal'],
            'joomla': ['joomla'],
            'django': ['django', 'csrf_token'],
            'rails': ['rails', 'ruby on rails'],
            'laravel': ['laravel'],
            'spring': ['spring', 'spring boot']
        }
        
        for framework, patterns in framework_patterns.items():
            if any(pattern in service_info for pattern in patterns):
                frameworks.append(framework)
        
        return frameworks
    
    def _check_common_vulnerabilities(self, product: str, version: str) -> List[Dict[str, Any]]:
        """Check for common vulnerability indicators"""
        vulnerabilities = []
        
        # Outdated version patterns
        outdated_versions = {
            'apache': ['2.2', '2.0', '1.3'],
            'nginx': ['0.7', '0.8', '1.0', '1.2'],
            'mysql': ['5.0', '5.1', '5.5'],
            'php': ['5.', '7.0', '7.1']
        }
        
        for software, versions in outdated_versions.items():
            if software in product.lower():
                for old_version in versions:
                    if old_version in version:
                        vulnerabilities.append({
                            "type": "OUTDATED_SOFTWARE",
                            "severity": "HIGH",
                            "message": f"Outdated {software} version: {version}",
                            "software": software,
                            "version": version
                        })
                        break
        
        return vulnerabilities