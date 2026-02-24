import subprocess
import time
from typing import List, Dict, Any

class SmartPortScanner:
    """Smart port scanner that balances speed and comprehensiveness"""
    
    def __init__(self):
        self.common_ports = {
            'web_ports': [80, 443, 8080, 8443, 8000, 3000, 5000],
            'database_ports': [1433, 1521, 3306, 5432, 27017, 6379],
            'remote_access': [21, 22, 23, 3389, 5900],
            'network_services': [25, 53, 110, 111, 135, 139, 161, 162, 445, 993, 995],
            'application_ports': [8000, 8008, 8080, 8081, 8090, 8443, 8888, 9000, 9090]
        }
    
    def get_optimized_port_range(self, scan_type: str) -> str:
        """Get optimized port ranges for different scan types"""
        ranges = {
            'quick': '1-1000',
            'standard': '1-1000,3000-4000,8000-9000',
            'web': '80,443,8080,8443,8000,3000,5000,8008,8081,8090,8888,9000,9090',
            'comprehensive': '1-10000',
            'services': '21-23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,1723,3306,3389,5432,5900,6379,27017,8000-9000'
        }
        return ranges.get(scan_type, ranges['standard'])
    
    def quick_port_discovery(self, target: str) -> List[int]:
        """Quick port discovery to identify active ports first"""
        try:
            # Fast ping scan to identify responsive hosts
            cmd = ['nmap', '-T4', '-sn', target, '-oX', '-']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # If host is up, do a very fast port scan
                cmd = ['nmap', '-T4', '-F', '--open', target, '-oX', '-']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                # Parse and return open ports
                return self._parse_open_ports(result.stdout)
            return []
            
        except Exception as e:
            print(f"Quick discovery failed: {e}")
            return []
    
    def _parse_open_ports(self, xml_output: str) -> List[int]:
        """Parse nmap XML to extract open ports"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_output)
            open_ports = []
            
            for host in root.findall('host'):
                for port in host.findall('ports/port'):
                    state = port.find('state')
                    if state is not None and state.get('state') == 'open':
                        port_id = port.get('portid')
                        if port_id and port_id.isdigit():
                            open_ports.append(int(port_id))
            
            return open_ports
        except Exception:
            return []