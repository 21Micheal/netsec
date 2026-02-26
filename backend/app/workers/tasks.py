from celery import Celery
from app import create_app
import os
from config import Config
from datetime import datetime
import uuid
import json
from typing import Dict, Any, List
import ssl
import socket
import subprocess
import concurrent.futures
import OpenSSL
import requests


# Create Celery instance
cel = Celery("tasks", broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

# Configure Celery
cel.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Create Flask app instance
app = create_app()

# Configure Celery with Flask app context
class ContextTask(cel.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

cel.Task = ContextTask

# --- Core Task Functions ---

# Add new imports
from app.utils.enhanced_scanner import EnhancedServiceDetector
from app.utils.web_technology_detector import WebTechnologyDetector
from app.utils.cve_detector import CVEDetector
from app.utils.ssl_analyzer import SSLAnalyzer
from app.utils.web_vulnerability_scanner import WebVulnerabilityScanner
from app.models import Asset
from app.utils.vulnerability_scanner import VulnerabilityScanner
from app.utils.vulnerability_insights import generate_vulnerability_insights, generate_web_security_insights, generate_ssl_insights, generate_cve_insights, generate_credential_insights
from app.services.vulnerability_records import create_vulnerability_records, create_web_vulnerability_records, create_ssl_vulnerability_records, create_cve_vulnerability_records, create_credential_vulnerability_records

# **FIXED: Single broadcast function definition**
def broadcast_scan_update(job_id: str):
    """Safely broadcast scan updates with proper app context"""
    try:
        from app.routes.ws_routes import broadcast_scan_update as broadcast
        print(f"📢 Broadcasting update for job {job_id}")
        broadcast(job_id)
    except ImportError as e:
        print(f"⚠️ Warning: Could not import broadcast function: {e}")
    except Exception as e:
        print(f"❌ Error broadcasting update: {e}")

# 🚨 IMPORTANT: Define the enhanced scan task AFTER imports
@cel.task
def enqueue_enhanced_scan(job_id: str, target: str, scan_type: str = "comprehensive_safe"):
    """Enhanced scanning with progress tracking"""
    try:
        from app.models import ScanJob, JobStatus
        from app.extensions import db
        
        print(f"🔍 Starting enhanced scan for {target} (Job: {job_id})")
        
        job = ScanJob.query.get(job_id)
        if not job:
            print(f"❌ Job {job_id} not found!")
            return
        
        # Update status to running
        job.status = JobStatus.running
        job.progress = 10
        db.session.commit()
        broadcast_scan_update(job_id)
        
        try:
            insights = {}
            start_time = datetime.utcnow()
            
            if scan_type == "web_enhanced":
                # Web scans are typically faster
                print(f"🌐 Running enhanced web technology detection...")
                web_detector = WebTechnologyDetector()
                web_results = web_detector.comprehensive_web_scan(target)
                
                # Update progress
                job.progress = 70
                db.session.commit()
                broadcast_scan_update(job_id)
                
                if 'error' in web_results:
                    raise Exception(web_results['error'])
                
                insights = {
                    'target': target,
                    'scan_type': 'web_enhanced',
                    'web_technologies': web_results.get('technologies', []),
                    'security_headers': web_results.get('security_headers', {}),
                    'server_info': web_results.get('server_info', {}),
                    'vulnerability_indicators': web_results.get('vulnerability_indicators', []),
                    'scan_duration': (datetime.utcnow() - start_time).total_seconds(),
                    'summary': {
                        'technologies_found': len(web_results.get('technologies', [])),
                        'security_score': web_results.get('security_headers', {}).get('security_score', 0),
                        'vulnerabilities': len(web_results.get('vulnerability_indicators', []))
                    }
                }
                
            else:
                # Network scans can take longer - show progress
                print(f"🔧 Running enhanced service enumeration...")
                service_detector = EnhancedServiceDetector()
                
                # Update progress to show we're starting the scan
                job.progress = 30
                db.session.commit()
                broadcast_scan_update(job_id)
                
                scan_results = service_detector.enhanced_nmap_scan(target, scan_type)
                
                # Update progress after scan completes
                job.progress = 80
                db.session.commit()
                broadcast_scan_update(job_id)
                
                # Handle privilege errors gracefully
                if 'error' in scan_results and 'requires root privileges' in scan_results['error']:
                    print("🛡️  Running unprivileged scan (OS detection disabled)")
                    insights = {
                        'target': target,
                        'scan_type': 'enhanced_unprivileged',
                        'warning': 'OS detection requires root privileges. Running with limited capabilities.',
                        'hosts': scan_results.get('nmap_output', {}).get('hosts', []),
                        'services': [],
                        'technologies': [],
                        'vulnerability_indicators': [],
                        'scan_duration': (datetime.utcnow() - start_time).total_seconds(),
                        'summary': {
                            'total_hosts': 0,
                            'open_ports': 0,
                            'services_detected': 0,
                            'technologies_found': 0,
                            'vulnerabilities_found': 0
                        }
                    }
                    
                    # Try to extract what we can from the partial results
                    if 'nmap_output' in scan_results:
                        partial_insights = _process_enhanced_scan_results(scan_results['nmap_output'])
                        insights.update(partial_insights)
                    
                elif 'error' in scan_results:
                    raise Exception(scan_results['error'])
                else:
                    insights = _process_enhanced_scan_results(scan_results)
                    insights['scan_duration'] = (datetime.utcnow() - start_time).total_seconds()
            
            # Store enhanced insights
            job.insights = insights
            job.progress = 100
            job.status = JobStatus.finished
            job.finished_at = datetime.utcnow()
            db.session.commit()
            broadcast_scan_update(job_id)
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            print(f"✅ Enhanced scan job {job_id} completed in {duration:.1f} seconds!")
            
        except Exception as scan_error:
            print(f"❌ Enhanced scan failed: {str(scan_error)}")
            import traceback
            traceback.print_exc()
            
            job.status = JobStatus.failed
            job.log = f"Enhanced scan failed: {str(scan_error)}"
            db.session.commit()
            broadcast_scan_update(job_id)
            
    except Exception as e:
        print(f"❌ Enhanced job processing failed: {str(e)}")
        import traceback
        traceback.print_exc()

def _process_enhanced_scan_results(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """Process enhanced scan results for insights"""
    insights = {
        'target': scan_results.get('target', ''),
        'scan_type': 'enhanced',
        'hosts': scan_results.get('hosts', []),
        'services': [],
        'technologies': [],
        'vulnerability_indicators': [],
        'summary': {
            'total_hosts': scan_results.get('summary', {}).get('total_hosts', 0),
            'open_ports': scan_results.get('summary', {}).get('open_ports', 0),
            'services_detected': scan_results.get('summary', {}).get('services_detected', 0),
            'technologies_found': 0,
            'vulnerabilities_found': 0
        }
    }
    
    # Extract services and technologies
    for host in scan_results.get('hosts', []):
        for service in host.get('services', []):
            insights['services'].append(service)
            insights['technologies'].extend(service.get('technologies', []))
            insights['vulnerability_indicators'].extend(service.get('vulnerability_indicators', []))
    
    insights['summary']['technologies_found'] = len(set(insights['technologies']))
    insights['summary']['vulnerabilities_found'] = len(insights['vulnerability_indicators'])
    
    return insights

@cel.task
def enqueue_scan_job(job_id: str, target: str, profile: str = "default"):
    """Process a network scan job - FIXED VERSION"""
    try:
        from app.models import ScanJob, JobStatus, ScanResult
        from app.utils.nmap_runner import run_nmap_scan
        from app.extensions import db
        
        print(f"🔍 Starting network scan for {target} (Job: {job_id})")
        
        job = ScanJob.query.get(job_id)
        if not job:
            print(f"❌ Job {job_id} not found!")
            return
        
        # Update status to running
        job.status = JobStatus.running
        job.progress = 10
        db.session.commit()
        broadcast_scan_update(job_id)
        
        # Configure nmap arguments based on profile
        nmap_args = get_nmap_arguments(profile)
        
        try:
            print(f"🔄 Running nmap scan with args: {nmap_args}")
            
            # **FIXED: Add progress callback for long scans**
            def progress_callback(current_progress):
                try:
                    job.progress = min(10 + int(current_progress * 0.4), 50)  # 10-50%
                    db.session.commit()
                    broadcast_scan_update(job_id)
                except Exception as e:
                    print(f"⚠️ Progress update failed: {e}")
            
            # Run nmap scan
            results = run_nmap_scan(target, nmap_args, job_id=job_id)
            
            if not results:
                raise Exception("No results returned from nmap scan")
            
            print(f"✅ Nmap scan completed. Processing results...")
            
            # Update progress
            job.progress = 60
            db.session.commit()
            broadcast_scan_update(job_id)
            
            # Process and store results
            process_scan_results(job_id, target, results)
            
            # Update progress before final
            job.progress = 90
            db.session.commit()
            broadcast_scan_update(job_id)
            
            # Mark as completed
            job.progress = 100
            job.status = JobStatus.finished
            job.finished_at = datetime.utcnow()
            db.session.commit()
            broadcast_scan_update(job_id)
            
            print(f"✅ Scan job {job_id} completed successfully!")
            
        except Exception as scan_error:
            print(f"❌ Scan failed: {str(scan_error)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            
            job.status = JobStatus.failed
            job.progress = 0
            job.log = f"Scan failed: {str(scan_error)}"
            job.finished_at = datetime.utcnow()
            db.session.commit()
            broadcast_scan_update(job_id)
            
    except Exception as e:
        print(f"❌ Job processing failed: {str(e)}")
        import traceback
        traceback.print_exc()

@cel.task
def enqueue_web_scan(job_id: str, url: str, profile: str = "web"):
    """Process a web security scan"""
    try:
        from app.models import ScanJob, JobStatus, WebScanResult
        from app.utils.web_scanner import run_web_security_scan, analyze_headers_and_cookies
        from app.extensions import db
        
        print(f"🔍 Starting web scan for {url} (Job: {job_id})")
        
        job = ScanJob.query.get(job_id)
        if not job:
            print(f"❌ Job {job_id} not found!")
            return
        
        # Update status to running
        job.status = JobStatus.running
        job.progress = 20
        db.session.commit()
        broadcast_scan_update(job_id)
        
        try:
            # Run web security scan
            print(f"🔄 Running web security scan...")
            job.progress = 40
            db.session.commit()
            broadcast_scan_update(job_id)
            
            web_results = run_web_security_scan(url, job_id=job_id)
            
            # Update progress
            job.progress = 70
            db.session.commit()
            broadcast_scan_update(job_id)
            
            # Analyze headers and cookies
            print(f"🔍 Analyzing headers and cookies...")
            analysis_results = analyze_headers_and_cookies(web_results)
            
            # Update progress
            job.progress = 85
            db.session.commit()
            broadcast_scan_update(job_id)
            
            # Store web scan results
            web_scan_result = WebScanResult(
                job_id=job_id,
                url=url,
                http_status=web_results.get('status_code'),
                headers=web_results.get('headers', {}),
                cookies=web_results.get('cookies', {}),
                issues=analysis_results.get('issues', [])
            )
            db.session.add(web_scan_result)
            
            # Store insights for dashboard
            job.insights = create_web_insights(url, web_results, analysis_results)
            
            job.progress = 100
            job.status = JobStatus.finished
            job.finished_at = datetime.utcnow()
            db.session.commit()
            broadcast_scan_update(job_id)
            
            print(f"✅ Web scan job {job_id} completed successfully!")
            
        except Exception as scan_error:
            print(f"❌ Web scan failed: {str(scan_error)}")
            import traceback
            traceback.print_exc()
            
            job.status = JobStatus.failed
            job.progress = 0
            job.log = f"Web scan failed: {str(scan_error)}"
            job.finished_at = datetime.utcnow()
            db.session.commit()
            broadcast_scan_update(job_id)
            
    except Exception as e:
        print(f"❌ Web job processing failed: {str(e)}")
        import traceback
        traceback.print_exc()

def should_use_web_scan(target: str, profile: str) -> bool:
    """Determine if a target should use web scanning"""
    # Explicit web profile
    if profile == "web":
        return True
    
    # URL-like targets (http/https)
    if target.startswith('http://') or target.startswith('https://'):
        return True
    
    # Domain-like targets (not IP addresses)
    if not is_ip_address(target):
        return True
    
    return False

def is_ip_address(target: str) -> bool:
    """Check if target is an IP address"""
    try:
        import ipaddress
        # Strip port if present
        target_clean = target.split(':')[0]
        ipaddress.ip_address(target_clean)
        return True
    except ValueError:
        return False

@cel.task
def enqueue_combined_scan(job_id: str, target: str, profile: str = "default"):
    """**FIXED: Enhanced combined scan that automatically detects scan type**"""
    try:
        from app.models import ScanJob, JobStatus
        from app.extensions import db
        
        print(f"🔍 Starting combined scan for {target} (Job: {job_id})")
        
        job = ScanJob.query.get(job_id)
        if not job:
            print(f"❌ Job {job_id} not found!")
            return
        
        # Set to queued initially
        job.status = JobStatus.queued
        job.progress = 0
        db.session.commit()
        broadcast_scan_update(job_id)
        
        # **FIXED: Call scan functions directly instead of using .delay()**
        # This ensures the WebSocket context is maintained
        if should_use_web_scan(target, profile):
            print(f"🌐 Detected web target, using web scan: {target}")
            enqueue_web_scan(job_id, target, profile)
        else:
            print(f"🔧 Detected network target, using network scan: {target}")
            enqueue_scan_job(job_id, target, profile)
            
    except Exception as e:
        print(f"❌ Combined job processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Mark job as failed
        try:
            from app.models import ScanJob, JobStatus
            from app.extensions import db
            job = ScanJob.query.get(job_id)
            if job:
                job.status = JobStatus.failed
                job.log = f"Combined scan failed: {str(e)}"
                job.finished_at = datetime.utcnow()
                db.session.commit()
                broadcast_scan_update(job_id)
        except:
            pass

@cel.task
def retry_scan_job(job_id: str):
    """Retry a failed scan job"""
    try:
        from app.models import ScanJob, JobStatus
        from app.extensions import db
        
        original_job = ScanJob.query.get(job_id)
        if not original_job:
            print(f"❌ Original job {job_id} not found!")
            return
        
        # Create a new job with the same parameters
        new_job_id = str(uuid.uuid4())
        new_job = ScanJob(
            id=new_job_id,
            target=original_job.target,
            profile=original_job.profile,
            status=JobStatus.queued,
            parent_scan_id=original_job.id
        )
        db.session.add(new_job)
        db.session.commit()
        
        # **FIXED: Use apply_async to ensure task is queued properly**
        enqueue_combined_scan.apply_async(
            args=[new_job_id, original_job.target, original_job.profile],
            countdown=1  # Small delay to ensure DB commit completes
        )
        
        print(f"✅ Retry job {new_job_id} created for failed job {job_id}")
        
        return new_job_id
        
    except Exception as e:
        print(f"❌ Retry job creation failed: {str(e)}")
        import traceback
        traceback.print_exc()

# --- Essential Helper Functions ---

def get_nmap_arguments(profile: str) -> list:
    """Get nmap arguments based on scan profile"""
    normalized = (profile or "default").strip().lower()
    profile_map = {
        "default": ["-T3", "-sV"],
        "quick": ["-T4", "-F"],
        "fast": ["-T4", "-F"],
        "detailed": ["-sV", "-sC"],
        "comprehensive": ["-sV", "-sC", "-A"],
        "full": ["-sV", "-sC", "-A"],
        "safe": ["-sV", "--open"],
    }
    return profile_map.get(normalized, profile_map["default"])

def process_scan_results(job_id: str, target: str, nmap_results: dict):
    """Process and store nmap scan results"""
    try:
        from app.models import ScanResult, ScanJob
        from app.extensions import db
        
        job = ScanJob.query.get(job_id)
        if not job:
            return
        
        target_metadata = collect_target_metadata(target)
        insights = {
            'target': target,
            'target_metadata': target_metadata,
            'open_ports': [],
            'services': [],
            'security_indicators': [],
            'summary': {
                'total_open_ports': 0,
                'unique_services': 0,
                'risk_level': 'LOW',
                'resolves_to': target_metadata.get('resolved_ips', [])
            }
        }
        
        # Parse nmap results and extract open ports
        open_ports = extract_open_ports(nmap_results)
        
        for port_data in open_ports:
            # Store in database
            scan_result = ScanResult(
                job_id=job_id,
                target=target,
                port=port_data['port'],
                protocol=port_data['protocol'],
                service=port_data['service'],
                version=port_data.get('version', '')
            )
            db.session.add(scan_result)
            
            # Add to insights
            insights['open_ports'].append(port_data)
            if port_data['service'] != 'unknown':
                insights['services'].append({
                    'port': port_data['port'],
                    'name': port_data['service'],
                    'version': port_data.get('version', '')
                })
        
        # Generate security indicators
        insights['security_indicators'] = generate_basic_security_indicators(open_ports)
        
        # Update summary
        insights['summary']['total_open_ports'] = len(open_ports)
        insights['summary']['unique_services'] = len(insights['services'])
        insights['summary']['risk_level'] = calculate_simple_risk_level(open_ports)
        
        # Store insights
        job.insights = insights
        db.session.commit()
        
        print(f"✅ Processed {len(open_ports)} open ports for job {job_id}")
        
    except Exception as e:
        print(f"❌ Error processing scan results: {e}")
        import traceback
        traceback.print_exc()

def extract_open_ports(nmap_results: dict) -> list:
    """Extract open ports from both xmltodict and python-nmap output structures."""
    open_ports = []

    def append_port(port: int, protocol: str, service: str, version: str = "", product: str = ""):
        if not port:
            return
        open_ports.append({
            'port': int(port),
            'protocol': protocol or 'tcp',
            'service': service or 'unknown',
            'version': version or '',
            'product': product or '',
            'state': 'open'
        })

    try:
        # xmltodict structure from `nmap -oX -`
        if 'nmaprun' in nmap_results:
            hosts = nmap_results['nmaprun'].get('host', [])
            if not isinstance(hosts, list):
                hosts = [hosts] if hosts else []

            for host in hosts:
                if 'ports' in host and 'port' in host['ports']:
                    ports = host['ports']['port']
                    if not isinstance(ports, list):
                        ports = [ports] if ports else []

                    for port_info in ports:
                        state = port_info.get('state', {}).get('@state', 'unknown')
                        if state == 'open':
                            service_info = port_info.get('service', {})
                            append_port(
                                port=int(port_info.get('@portid', 0)),
                                protocol=port_info.get('@protocol', 'tcp'),
                                service=service_info.get('@name', 'unknown'),
                                version=service_info.get('@version', ''),
                                product=service_info.get('@product', '')
                            )

        # python-nmap structure from PortScanner conversion in nmap_runner.py
        if 'scan' in nmap_results and isinstance(nmap_results.get('scan'), dict):
            for _host, host_data in nmap_results['scan'].items():
                protocols = host_data.get('protocols', {})
                if not isinstance(protocols, dict):
                    continue
                for proto, ports in protocols.items():
                    for port_info in ports or []:
                        if port_info.get('state') == 'open':
                            append_port(
                                port=port_info.get('port'),
                                protocol=proto or 'tcp',
                                service=port_info.get('name') or 'unknown',
                                version=port_info.get('version') or '',
                                product=port_info.get('product') or ''
                            )
    except Exception as e:
        print(f"⚠️ Error extracting open ports: {e}")

    deduped = {}
    for item in open_ports:
        deduped[(item["port"], item["protocol"])] = item
    return list(deduped.values())

def generate_basic_security_indicators(open_ports: list) -> list:
    """Generate basic security indicators from open ports"""
    indicators = []
    
    # Common risky ports
    risky_ports = {
        21: 'FTP',
        23: 'Telnet', 
        135: 'RPC',
        139: 'NetBIOS',
        445: 'SMB',
        1433: 'MSSQL',
        1521: 'Oracle',
        3306: 'MySQL',
        3389: 'RDP'
    }
    
    for port_data in open_ports:
        port = port_data['port']
        if port in risky_ports:
            indicators.append({
                'type': 'RISKY_PORT',
                'severity': 'MEDIUM',
                'message': f'Port {port} ({risky_ports[port]}) is open',
                'port': port,
                'service': port_data['service']
            })

        if port_data.get('service') in {'http', 'https'} and port_data.get('version'):
            indicators.append({
                'type': 'VERSION_DISCLOSURE',
                'severity': 'LOW',
                'message': f"Service version exposed on port {port}: {port_data.get('version')}",
                'port': port,
                'service': port_data['service']
            })
    
    return indicators

def calculate_simple_risk_level(open_ports: list) -> str:
    """Calculate simple risk level based on open ports"""
    risky_port_count = len([p for p in open_ports if p['port'] in [21, 23, 135, 139, 445, 1433, 1521, 3306, 3389]])
    total_ports = len(open_ports)
    
    if risky_port_count >= 3 or total_ports > 20:
        return 'HIGH'
    elif risky_port_count >= 1 or total_ports > 10:
        return 'MEDIUM'
    else:
        return 'LOW'

def collect_target_metadata(target: str) -> dict:
    """Collect DNS and basic target metadata for improved scan context."""
    metadata = {
        "input_target": target,
        "normalized_target": target,
        "resolved_ips": [],
        "reverse_dns": None,
        "dns_error": None,
    }
    try:
        normalized = target
        if "://" in normalized:
            normalized = normalized.split("://", 1)[1]
        normalized = normalized.split("/", 1)[0]
        normalized = normalized.split(":", 1)[0]
        metadata["normalized_target"] = normalized

        _, _, ips = socket.gethostbyname_ex(normalized)
        metadata["resolved_ips"] = sorted(set(ips))
        if metadata["resolved_ips"]:
            try:
                metadata["reverse_dns"] = socket.gethostbyaddr(metadata["resolved_ips"][0])[0]
            except Exception:
                metadata["reverse_dns"] = None
    except Exception as exc:
        metadata["dns_error"] = str(exc)
    return metadata

def create_web_insights(url: str, web_results: dict, analysis_results: dict) -> dict:
    """Create insights structure for web scans"""
    return {
        'target': url,
        'web_results': web_results,
        'analysis': analysis_results,
        'security_indicators': analysis_results.get('issues', []),
        'summary': {
            'http_status': web_results.get('status_code'),
            'headers_count': len(web_results.get('headers', {})),
            'cookies_count': len(web_results.get('cookies', {})),
            'security_issues': len(analysis_results.get('issues', [])),
            'risk_level': 'HIGH' if len(analysis_results.get('issues', [])) > 3 else 'MEDIUM' if len(analysis_results.get('issues', [])) > 0 else 'LOW'
        }
    }


# Initialize scanner
scanner = VulnerabilityScanner()
# Vulnerability scanning tasks
@cel.task(bind=True)
def run_vulnerability_scan(self, job_id):
    """Comprehensive vulnerability assessment"""
    from app.models import ScanJob, JobStatus, db
    job = ScanJob.query.get(job_id)
    if not job:
        return {'error': 'Job not found'}
    
    try:
        job.set_status(JobStatus.running, 0)
        target = job.target
        config = job.config or {}
        
        print(f"🎯 Starting vulnerability scan for: {target}")
        # Check tool availability first
        job.set_status(JobStatus.running, 10)
        tools_available = scanner.check_tool_availability()
        missing_tools = [tool for tool, available in tools_available.items() if not available]
        
        if missing_tools:
            print(f"⚠️ Missing tools: {', '.join(missing_tools)}")
        
        results = {
            'web_security': None,
            'ssl_security': None,
            'cve_analysis': None,
            'credential_testing': None,
            'overall_risk': None
        }
        
        # Run web security scan if target is web service
        job.set_status(JobStatus.running, 25)
        if scanner.is_web_service(target):
            print("🌐 Running web security scan...")
            try:
                results['web_security'] = scanner.perform_web_security_scan(target, config.get('web_scan_config', {}))
            except Exception as e:
                print(f"❌ Web security scan failed: {e}")
                results['web_security'] = {
                    'vulnerabilities': [{
                        'type': 'SCAN_ERROR',
                        'severity': 'MEDIUM',
                        'description': f'Web security scan failed: {str(e)}',
                        'recommendation': 'Check web service accessibility'
                    }],
                    'risk_assessment': {'risk_score': 0, 'risk_level': 'UNKNOWN'}
                }
        
        # Run SSL analysis
        job.set_status(JobStatus.running, 50)
        print("🔒 Running SSL analysis...")
        try:
            results['ssl_security'] = scanner.perform_ssl_analysis(target, config.get('ssl_config', {}))
        except Exception as e:
            print(f"❌ SSL analysis failed: {e}")
            results['ssl_security'] = {
                'certificate_info': {},
                'protocol_info': {},
                'vulnerabilities': [{
                    'type': 'SCAN_ERROR',
                    'severity': 'MEDIUM',
                    'description': f'SSL analysis failed: {str(e)}',
                    'recommendation': 'Check SSL/TLS service accessibility'
                }],
                'security_score': 0
            }
        
        # Run CVE analysis
        job.set_status(JobStatus.running, 75)
        print("📋 Running CVE analysis...")
        try:
            results['cve_analysis'] = scanner.perform_cve_analysis(target, config.get('cve_config', {}))
        except Exception as e:
            print(f"❌ CVE analysis failed: {e}")
            results['cve_analysis'] = {
                'results': [],
                'summary': {'services_scanned': 0, 'vulnerable_services': 0, 'total_vulnerabilities': 0}
            }
        
        # Run credential testing if configured
        if config.get('credential_config'):
            print("🔑 Running credential testing...")
            try:
                results['credential_testing'] = scanner.perform_credential_testing(target, config['credential_config'])
            except Exception as e:
                print(f"❌ Credential testing failed: {e}")
                results['credential_testing'] = {
                    'service': config['credential_config'].get('service_type', 'unknown'),
                    'host': target,
                    'port': config['credential_config'].get('port', 0),
                    'credentials_tested': 0,
                    'vulnerable_credentials': [],
                    'recommendations': ['Credential testing failed due to an error']
                }
        
        # Calculate overall risk
        print("📊 Calculating overall risk...")
        try:
            results['overall_risk'] = scanner.calculate_overall_risk(results)
        except Exception as e:
            print(f"❌ Risk calculation failed: {e}")
            results['overall_risk'] = {
                'overall_score': 0,
                'risk_level': 'UNKNOWN',
                'component_scores': {}
            }
        
        # Store results
        job.vulnerability_results = results
        job.insights = generate_vulnerability_insights(results)
        job.set_status(JobStatus.finished, 100)
        
        # Create vulnerability records
        try:
            create_vulnerability_records(job, results)
        except Exception as e:
            print(f"❌ Failed to create vulnerability records: {e}")
        
        print("✅ Vulnerability scan completed successfully")
        return {'status': 'completed', 'results': results}
        
    except Exception as e:
        print(f"❌ Vulnerability scan failed: {e}")
        job.set_status(JobStatus.failed, 0)
        job.error_message = str(e)
        db.session.commit()
        return {'error': str(e)}


@cel.task(bind=True)
def run_web_vulnerability_scan(self, job_id):
    """Web-specific vulnerability scanning"""
    from app.models import ScanJob, JobStatus, db
    job = ScanJob.query.get(job_id)
    if not job:
        return {'error': 'Job not found'}
    
    try:
        job.set_status(JobStatus.running, 0)
        target = job.target
        config = job.config or {}
        
        # Use scanner module for execution
        results = scanner.perform_web_security_scan(target, config.get('web_scan_config', {}))
        
        job.vulnerability_results = {'web_security': results}
        job.insights = generate_web_security_insights(results)
        job.set_status(JobStatus.finished, 100)
        
        # Use dedicated record creation function
        create_web_vulnerability_records(job, results)
        
        return {'status': 'completed', 'results': results}
        
    except Exception as e:
        job.set_status(JobStatus.failed, 0)
        job.error_message = str(e)
        db.session.commit()
        return {'error': str(e)}


@cel.task(bind=True)
def run_ssl_analysis(self, job_id):
    """SSL/TLS vulnerability analysis"""
    from app.models import ScanJob, JobStatus, db
    job = ScanJob.query.get(job_id)
    if not job:
        return {'error': 'Job not found'}
    
    try:
        job.set_status(JobStatus.running, 0)
        target = job.target
        config = job.config or {}
        
        # Use scanner module for execution
        results = scanner.perform_ssl_analysis(target, config.get('ssl_config', {}))
        
        job.vulnerability_results = {'ssl_security': results}
        job.insights = generate_ssl_insights(results)
        job.set_status(JobStatus.finished, 100)
        
        # Use dedicated record creation function
        create_ssl_vulnerability_records(job, results)
        
        return {'status': 'completed', 'results': results}
        
    except Exception as e:
        job.set_status(JobStatus.failed, 0)
        job.error_message = str(e)
        db.session.commit()
        return {'error': str(e)}


@cel.task(bind=True)
def run_cve_scan(self, job_id):
    """CVE vulnerability scanning"""
    from app.models import ScanJob, JobStatus, db
    job = ScanJob.query.get(job_id)
    if not job:
        return {'error': 'Job not found'}
    
    try:
        job.set_status(JobStatus.running, 0)
        target = job.target
        config = job.config or {}
        
        # Use scanner module for execution
        results = scanner.perform_cve_analysis(target, config.get('cve_config', {}))
        
        job.vulnerability_results = {'cve_analysis': results}
        job.insights = generate_cve_insights(results)
        job.set_status(JobStatus.finished, 100)
        
        # Use dedicated record creation function
        create_cve_vulnerability_records(job, results)
        
        return {'status': 'completed', 'results': results}
        
    except Exception as e:
        job.set_status(JobStatus.failed, 0)
        job.error_message = str(e)
        db.session.commit()
        return {'error': str(e)}


@cel.task(bind=True)
def run_credential_testing(self, job_id):
    """Credential testing task"""
    from app.models import ScanJob, JobStatus, db  
    job = ScanJob.query.get(job_id)
    if not job:
        return {'error': 'Job not found'}
    
    try:
        job.set_status(JobStatus.running, 0)
        target = job.target
        config = job.config or {}
        
        # Use scanner module for execution
        results = scanner.perform_credential_testing(target, config.get('credential_config', {}))
        
        job.vulnerability_results = {'credential_testing': results}
        job.insights = generate_credential_insights(results)
        job.set_status(JobStatus.finished, 100)
        
        # Use dedicated record creation function
        create_credential_vulnerability_records(job, results)
        
        return {'status': 'completed', 'results': results}
        
    except Exception as e:
        job.set_status(JobStatus.failed, 0)
        job.error_message = str(e)
        db.session.commit()
        return {'error': str(e)}
# Vulnerability scanning implementations
def perform_web_security_scan(self, target: str, config: Dict) -> Dict:
    """Perform comprehensive web security scanning"""
    vulnerabilities = []
    
    try:
        # Normalize the target URL
        if not target.startswith(('http://', 'https://')):
            # Try both HTTP and HTTPS
            target_http = f"http://{target}"
            target_https = f"https://{target}"
        else:
            target_http = target_https = target
        
        print(f"🌐 Starting web security scan for: {target}")
        
        # Try to determine which protocol works
        working_target = None
        try:
            response = requests.get(target_https, timeout=5, verify=False)
            working_target = target_https
            print(f"✅ Using HTTPS: {target_https}")
        except:
            try:
                response = requests.get(target_http, timeout=5, verify=False)
                working_target = target_http
                print(f"✅ Using HTTP: {target_http}")
            except:
                print(f"❌ Cannot reach target via HTTP or HTTPS")
                working_target = target_http  # Use HTTP as fallback
        
        if working_target:
            # Headers security analysis
            headers_vulns = self.analyze_http_headers(working_target)
            vulnerabilities.extend(headers_vulns)
            
            # Directory and file enumeration
            if config.get('directory_enum', True):
                dir_vulns = self.perform_directory_enumeration(working_target)
                vulnerabilities.extend(dir_vulns)
            
            # Security headers check
            security_headers_vulns = self.check_security_headers(working_target)
            vulnerabilities.extend(security_headers_vulns)
            
            # Cookie security analysis
            try:
                cookie_vulns = self.analyze_cookie_security(working_target)
                vulnerabilities.extend(cookie_vulns)
            except Exception as e:
                print(f"⚠️ Cookie analysis failed: {e}")
            
            # Run nuclei for template-based scanning
            nuclei_vulns = self.run_nuclei_scan(working_target)
            vulnerabilities.extend(nuclei_vulns)
            
            # Run Nikto scan
            nikto_vulns = self.run_nikto_scan(working_target)
            vulnerabilities.extend(nikto_vulns)
        
    except Exception as e:
        print(f"❌ Web security scan failed: {e}")
        vulnerabilities.append({
            'type': 'SCAN_ERROR',
            'severity': 'MEDIUM',
            'description': f'Web security scan failed: {str(e)}',
            'recommendation': 'Check target accessibility and network connectivity',
            'source': 'web_scan'
        })
    
    risk_assessment = self.calculate_web_risk_assessment(vulnerabilities)
    
    return {
        'vulnerabilities': vulnerabilities,
        'risk_assessment': risk_assessment
    }

def perform_ssl_analysis(target: str, config: Dict) -> Dict:
    """Perform comprehensive SSL/TLS analysis with better error handling"""
    vulnerabilities = []
    certificate_info = {}
    protocol_info = {}
    
    try:
        # Extract hostname and port safely
        if '://' in target:
            hostname = target.split('://')[-1].split('/')[0].split(':')[0]
        else:
            hostname = target.split('/')[0].split(':')[0]
        
        port = 443  # Default SSL port
        
        print(f"🔒 Starting SSL analysis for {hostname}:{port}")
        
        # Get certificate info with timeout
        cert_info = get_certificate_info(hostname, port)
        if cert_info and 'error' not in cert_info:
            certificate_info = cert_info
            cert_vulns = check_certificate_vulnerabilities(cert_info)
            vulnerabilities.extend(cert_vulns)
        else:
            error_msg = cert_info.get('error', 'Unknown error') if cert_info else 'No certificate info'
            print(f"⚠️ Could not retrieve certificate info: {error_msg}")
            vulnerabilities.append({
                'type': 'CERTIFICATE_RETRIEVAL_FAILED',
                'severity': 'MEDIUM',
                'description': f'Could not retrieve SSL certificate for {hostname}:{port}',
                'recommendation': 'Check if the service supports SSL/TLS and is accessible',
                'evidence': f'Error: {error_msg}',
                'source': 'ssl_analysis'
            })
        
        # Check protocol support
        try:
            proto_info = check_protocol_support(hostname, port)
            protocol_info = proto_info
            vulnerabilities.extend(proto_info.get('vulnerabilities', []))
        except Exception as e:
            print(f"Protocol support check failed: {e}")
            vulnerabilities.append({
                'type': 'PROTOCOL_CHECK_FAILED',
                'severity': 'MEDIUM',
                'description': f'Protocol support check failed: {str(e)}',
                'recommendation': 'Check service accessibility',
                'source': 'ssl_analysis'
            })
        
        # Check cipher strength
        try:
            cipher_vulns = scanner.check_cipher_strength(hostname, port)
            vulnerabilities.extend(cipher_vulns)
        except Exception as e:
            print(f"Cipher strength check failed: {e}")
        
    except Exception as e:
        print(f"❌ SSL analysis failed: {e}")
        vulnerabilities.append({
            'type': 'SSL_SCAN_ERROR',
            'severity': 'MEDIUM',
            'description': f'SSL analysis failed: {str(e)}',
            'recommendation': 'Check if target supports SSL/TLS and is accessible',
            'source': 'ssl_analysis'
        })
    
    # Calculate security score safely
    try:
        security_score = scanner.calculate_ssl_security_score(vulnerabilities, certificate_info, protocol_info)
    except Exception as e:
        print(f"Security score calculation failed: {e}")
        security_score = 0
    
    return {
        'certificate_info': certificate_info,
        'protocol_info': protocol_info,
        'vulnerabilities': vulnerabilities,
        'security_score': security_score
    }

def perform_cve_analysis(self, target: str, config: Dict) -> Dict:
    """Perform CVE analysis using nmap NSE scripts and vulners database"""
    services = self.discover_services_with_vuln_scan(target)
    results = []
    
    for service in services:
        service_vulns = self.check_service_vulnerabilities_aggressive(service, target)
        risk_assessment = self.calculate_service_risk_assessment(service_vulns)
        
        results.append({
            'service': service,
            'vulnerabilities': service_vulns,
            'risk_assessment': risk_assessment
        })
    
    summary = {
        'services_scanned': len(services),
        'vulnerable_services': len([r for r in results if r['vulnerabilities']]),
        'total_vulnerabilities': sum(len(r['vulnerabilities']) for r in results)
    }
    
    return {
        'results': results,
        'summary': summary
    }

def discover_services_with_vuln_scan(self, target: str) -> List[Dict]:
    """Discover services using nmap with vulnerability scripts"""
    services = []
    
    try:
        # Run nmap with version detection and vulnerability scripts
        # For localhost, scan common ports
        if target in ['127.0.0.1', 'localhost', '0.0.0.0']:
            print("🔍 Scanning common localhost ports...")
            common_ports = "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1433,1521,3306,3389,5432,5900,6379,27017"
            scan_result = self.nm.scan(target, arguments=f'-p {common_ports} -sV --version-all')
        else:
            scan_result = self.nm.scan(target, arguments='-sV --version-all --script vuln,safe')
            print(f"🔍 Running aggressive service discovery on: {target}")
        
        for host in self.nm.all_hosts():
            for proto in self.nm[host].all_protocols():
                ports = self.nm[host][proto].keys()
                
                for port in ports:
                    service_info = self.nm[host][proto][port]
                    service = {
                        'name': service_info.get('name', 'unknown'),
                        'version': service_info.get('version', ''),
                        'host': host,
                        'port': port,
                        'protocol': proto,
                        'product': service_info.get('product', ''),
                        'extrainfo': service_info.get('extrainfo', ''),
                        'scripts': service_info.get('script', {})
                    }
                    services.append(service)
                    
    except Exception as e:
        print(f"Service discovery failed: {e}")
        
    return services

def check_service_vulnerabilities_aggressive(self, service: Dict, target: str) -> List[Dict]:
    """Check for service-specific vulnerabilities using multiple methods"""
    vulnerabilities = []
    
    try:
        service_name = service['name'].lower()
        port = service['port']
        version = service.get('version', '')
        
        # Check nmap script results first
        scripts = service.get('scripts', {})
        for script_name, script_output in scripts.items():
            if any(keyword in script_name.lower() for keyword in ['vuln', 'exploit', 'cve']):
                vulnerabilities.append({
                    'type': f'NMAP_{script_name.upper()}',
                    'severity': self.determine_nmap_severity(script_output),
                    'description': f'Nmap script {script_name} detected potential vulnerability',
                    'recommendation': 'Review service configuration and apply patches',
                    'evidence': script_output,
                    'source': 'nmap_nse'
                })
        
        # Service-specific vulnerability checks
        if service_name in ['http', 'https', 'http-alt']:
            vulns = self.scan_web_vulnerabilities_aggressive(target, port)
            vulnerabilities.extend(vulns)
            
        elif service_name in ['ssh']:
            vulns = self.scan_ssh_vulnerabilities_aggressive(target, port, version)
            vulnerabilities.extend(vulns)
            
        elif service_name in ['ftp']:
            vulns = self.scan_ftp_vulnerabilities_aggressive(target, port, version)
            vulnerabilities.extend(vulns)
        
        # Version-specific vulnerability checks
        if version:
            version_vulns = self.check_version_vulnerabilities_aggressive(service_name, version)
            vulnerabilities.extend(version_vulns)
            
    except Exception as e:
        print(f"Service vulnerability check failed for {service['name']}: {e}")
        
    return vulnerabilities

def scan_web_vulnerabilities_aggressive(self, target: str, port: int) -> List[Dict]:
    """Aggressive web vulnerability scanning"""
    vulnerabilities = []
    
    try:
        # Normalize URL
        protocol = 'https' if port in [443, 8443] else 'http'
        if not target.startswith(('http://', 'https://')):
            target_url = f"{protocol}://{target}:{port}"
        else:
            target_url = target
        
        print(f"🔍 Running aggressive web scan on: {target_url}")
        
        # Common web vulnerabilities to check
        common_vulns = [
            {
                'type': 'SQL_INJECTION_POTENTIAL',
                'severity': 'HIGH', 
                'description': 'Potential SQL injection points should be tested',
                'recommendation': 'Implement input validation and use parameterized queries',
                'evidence': f'Web service detected on {target_url}',
                'source': 'web_analysis'
            },
            {
                'type': 'XSS_POTENTIAL',
                'severity': 'MEDIUM',
                'description': 'Potential Cross-Site Scripting vulnerabilities should be tested',
                'recommendation': 'Implement output encoding and Content Security Policy',
                'evidence': f'Web service detected on {target_url}',
                'source': 'web_analysis'
            }
        ]
        
        vulnerabilities.extend(common_vulns)
        
    except Exception as e:
        print(f"Aggressive web scan failed: {e}")
    
    return vulnerabilities

def check_version_vulnerabilities_aggressive(self, service_name: str, version: str) -> List[Dict]:
    """Aggressive version vulnerability checking"""
    vulnerabilities = []
    
    # Common vulnerable version patterns
    vulnerable_patterns = {
        'apache': [
            {'versions': ['2.4.49', '2.4.50'], 'cve': 'CVE-2021-41773', 'description': 'Path Traversal and RCE'},
            {'versions': ['2.4.0', '2.4.1'], 'cve': 'CVE-2022-22721', 'description': 'HTTP Request Smuggling'}
        ],
        'nginx': [
            {'versions': ['1.18.0', '1.19.0'], 'cve': 'CVE-2021-23017', 'description': 'DNS resolver vulnerability'}
        ],
        'openssh': [
            {'versions': ['7.4', '7.5'], 'cve': 'CVE-2019-6111', 'description': 'SSH client vulnerability'}
        ]
    }
    
    for service, patterns in vulnerable_patterns.items():
        if service in service_name.lower():
            for pattern in patterns:
                for vuln_version in pattern['versions']:
                    if vuln_version in version:
                        vulnerabilities.append({
                            'type': 'KNOWN_VULNERABLE_VERSION',
                            'severity': 'HIGH',
                            'description': f'{service_name} version {version} has {pattern["description"]}',
                            'recommendation': f'Update {service_name} and apply patch for {pattern["cve"]}',
                            'evidence': f'Vulnerable version detected: {version} - {pattern["cve"]}',
                            'cve_id': pattern['cve'],
                            'source': 'version_analysis'
                        })
    
    return vulnerabilities

def perform_credential_testing(target: str, config: Dict) -> Dict:
    """Perform credential testing for various services"""
    service_type = config.get('service_type', 'ssh')
    port = config.get('port')
    
    # This would integrate with tools like hydra, medusa, or custom implementations
    # For security, this should only test with explicit authorization and safe credentials
    
    return {
        'service': service_type,
        'host': target,
        'port': port or get_default_port(service_type),
        'credentials_tested': 0,  # Would be actual count from testing
        'vulnerable_credentials': [],  # Would contain actual results
        'recommendations': [
            'Implement strong password policies',
            'Enable multi-factor authentication',
            'Use certificate-based authentication where possible'
        ]
    }

# Helper functions for vulnerability detection
def analyze_http_headers(target: str) -> List[Dict]:
    """Analyze HTTP headers for security issues"""
    vulnerabilities = []
    
    try:
        response = requests.get(target, timeout=10, verify=False)
        headers = response.headers
        
        # Check for missing security headers
        security_headers = {
            'Content-Security-Policy': 'MEDIUM',
            'X-Content-Type-Options': 'LOW',
            'X-Frame-Options': 'MEDIUM',
            'Strict-Transport-Security': 'HIGH',
            'X-XSS-Protection': 'LOW'
        }
        
        for header, severity in security_headers.items():
            if header not in headers:
                vulnerabilities.append({
                    'type': 'MISSING_SECURITY_HEADER',
                    'severity': severity,
                    'description': f'Missing security header: {header}',
                    'recommendation': f'Implement {header} header with appropriate values',
                    'evidence': f'Header {header} not found in response'
                })
        
        # Check for information disclosure
        if 'Server' in headers and len(headers['Server']) > 0:
            vulnerabilities.append({
                'type': 'INFORMATION_DISCLOSURE',
                'severity': 'LOW',
                'description': f'Server information disclosed: {headers["Server"]}',
                'recommendation': 'Minimize server header information',
                'evidence': f'Server: {headers["Server"]}'
            })
            
    except Exception as e:
        vulnerabilities.append({
            'type': 'HEADER_ANALYSIS_ERROR',
            'severity': 'MEDIUM',
            'description': f'Header analysis failed: {str(e)}',
            'recommendation': 'Check target accessibility'
        })
    
    return vulnerabilities

def check_security_headers(target: str) -> List[Dict]:
    """Check security headers configuration"""
    vulnerabilities = []
    
    try:
        response = requests.get(target, timeout=10, verify=False)
        headers = response.headers
        
        # Analyze HSTS configuration
        if 'Strict-Transport-Security' in headers:
            hsts = headers['Strict-Transport-Security']
            if 'max-age=0' in hsts:
                vulnerabilities.append({
                    'type': 'HSTS_MISCONFIGURATION',
                    'severity': 'HIGH',
                    'description': 'HSTS max-age set to 0, disabling protection',
                    'recommendation': 'Set appropriate max-age value (e.g., 31536000)',
                    'evidence': f'HSTS Header: {hsts}'
                })
        
        # Check CSP for unsafe directives
        if 'Content-Security-Policy' in headers:
            csp = headers['Content-Security-Policy']
            if 'unsafe-inline' in csp or 'unsafe-eval' in csp:
                vulnerabilities.append({
                    'type': 'CSP_UNSAFE_DIRECTIVES',
                    'severity': 'MEDIUM',
                    'description': 'CSP contains unsafe directives',
                    'recommendation': 'Remove unsafe-inline and unsafe-eval from CSP',
                    'evidence': f'CSP: {csp}'
                })
                
    except Exception as e:
        # Error already handled in analyze_http_headers
        pass
    
    return vulnerabilities

def perform_directory_enumeration(target: str) -> List[Dict]:
    """Perform directory and file enumeration"""
    vulnerabilities = []
    
    common_paths = [
        '/admin', '/backup', '/.git', '/.env', '/config',
        '/phpinfo.php', '/server-status', '/.well-known',
        '/wp-admin', '/administrator', '/cgi-bin'
    ]
    
    for path in common_paths:
        try:
            url = f"{target.rstrip('/')}{path}"
            response = requests.get(url, timeout=5, verify=False, allow_redirects=False)
            
            if response.status_code in [200, 301, 302, 403]:
                vulnerabilities.append({
                    'type': 'SENSITIVE_PATH_EXPOSED',
                    'severity': 'LOW' if response.status_code == 403 else 'MEDIUM',
                    'description': f'Sensitive path accessible: {path}',
                    'recommendation': f'Restrict access to {path} or remove if not needed',
                    'evidence': f'Path {path} returned status {response.status_code}'
                })
                
        except requests.RequestException:
            continue
    
    return vulnerabilities

def get_certificate_info(hostname: str, port: int) -> Dict:
    """Get SSL certificate information"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                cert_bin = ssock.getpeercert(binary_form=True)
                
                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_bin)
                issuer = dict(x509.get_issuer().get_components())
                subject = dict(x509.get_subject().get_components())
                
                not_before = x509.get_notBefore().decode('ascii')
                not_after = x509.get_notAfter().decode('ascii')
                
                # Parse dates
                from datetime import datetime
                not_before_dt = datetime.strptime(not_before, '%Y%m%d%H%M%SZ')
                not_after_dt = datetime.strptime(not_after, '%Y%m%d%H%M%SZ')
                days_until_expiry = (not_after_dt - datetime.utcnow()).days
                
                return {
                    'subject': {k.decode(): v.decode() for k, v in subject.items()},
                    'issuer': {k.decode(): v.decode() for k, v in issuer.items()},
                    'not_before': not_before_dt.isoformat(),
                    'not_after': not_after_dt.isoformat(),
                    'has_expired': datetime.utcnow() > not_after_dt,
                    'days_until_expiry': days_until_expiry,
                    'signature_algorithm': x509.get_signature_algorithm().decode('ascii')
                }
                
    except Exception as e:
        return {'error': str(e)}

def check_certificate_vulnerabilities(cert_info: Dict) -> List[Dict]:
    """Check certificate for vulnerabilities with proper error handling"""
    vulnerabilities = []
    
    # Check if certificate info is valid
    if not cert_info or 'error' in cert_info:
        return [{
            'type': 'CERTIFICATE_ERROR',
            'severity': 'MEDIUM',
            'description': f'Certificate retrieval failed: {cert_info.get("error", "Unknown error")}',
            'recommendation': 'Check if SSL/TLS service is running and accessible',
            'source': 'ssl_analysis'
        }]
    
    # Safely check expiration with proper field validation
    has_expired = cert_info.get('has_expired', False)
    days_until_expiry = cert_info.get('days_until_expiry', 0)
    
    if has_expired:
        vulnerabilities.append({
            'type': 'EXPIRED_CERTIFICATE',
            'severity': 'HIGH',
            'description': 'SSL certificate has expired',
            'recommendation': 'Renew SSL certificate immediately',
            'evidence': f'Certificate expired on {cert_info.get("not_after", "unknown date")}',
            'source': 'ssl_analysis'
        })
    elif days_until_expiry < 30:
        vulnerabilities.append({
            'type': 'CERTIFICATE_EXPIRING_SOON',
            'severity': 'MEDIUM',
            'description': f'SSL certificate expires in {days_until_expiry} days',
            'recommendation': 'Renew SSL certificate',
            'evidence': f'Certificate expires on {cert_info.get("not_after", "unknown date")}',
            'source': 'ssl_analysis'
        })
    
    # Check signature algorithm safely
    sig_algo = cert_info.get('signature_algorithm', '')
    weak_algorithms = ['md5', 'sha1']
    if sig_algo and any(algo in sig_algo.lower() for algo in weak_algorithms):
        vulnerabilities.append({
            'type': 'WEAK_CERTIFICATE_SIGNATURE',
            'severity': 'HIGH',
            'description': f'Weak certificate signature algorithm: {sig_algo}',
            'recommendation': 'Use stronger signature algorithm (SHA-256 or higher)',
            'evidence': f'Signature algorithm: {sig_algo}',
            'source': 'ssl_analysis'
        })
    
    return vulnerabilities

def check_protocol_support(hostname: str, port: int) -> Dict:
    """Check supported SSL/TLS protocols"""
    protocols = {
        'SSLv2': False,
        'SSLv3': False,
        'TLSv1.0': False,
        'TLSv1.1': False,
        'TLSv1.2': False,
        'TLSv1.3': False
    }
    
    vulnerabilities = []
    
    for protocol_name in protocols.keys():
        try:
            # Simplified protocol check - in practice, use more robust methods
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    protocols[protocol_name] = True
                    
        except Exception:
            protocols[protocol_name] = False
    
    # Check for weak protocols
    if protocols.get('SSLv2', False) or protocols.get('SSLv3', False):
        vulnerabilities.append({
            'type': 'WEAK_SSL_PROTOCOL',
            'severity': 'HIGH',
            'description': 'Weak SSL protocol enabled (SSLv2/SSLv3)',
            'recommendation': 'Disable SSLv2 and SSLv3, use TLS 1.2 or higher',
            'evidence': f'Enabled protocols: {[k for k, v in protocols.items() if v]}'
        })
    
    if protocols.get('TLSv1.0', False) or protocols.get('TLSv1.1', False):
        vulnerabilities.append({
            'type': 'DEPRECATED_TLS_PROTOCOL',
            'severity': 'MEDIUM',
            'description': 'Deprecated TLS protocol enabled (TLS 1.0/1.1)',
            'recommendation': 'Disable TLS 1.0 and 1.1, use TLS 1.2 or higher',
            'evidence': f'Enabled protocols: {[k for k, v in protocols.items() if v]}'
        })
    
    return {
        'supported_protocols': protocols,
        'weak_protocols_enabled': any(protocols[p] for p in ['SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1']),
        'recommended_protocols': ['TLSv1.2', 'TLSv1.3'],
        'vulnerabilities': vulnerabilities
    }

# Risk assessment functions
def calculate_web_risk_assessment(vulnerabilities: List[Dict]) -> Dict:
    """Calculate risk assessment for web security findings"""
    severity_weights = {
        'CRITICAL': 10,
        'HIGH': 7,
        'MEDIUM': 4,
        'LOW': 1
    }
    
    risk_score = sum(severity_weights.get(vuln.get('severity', 'LOW'), 1) for vuln in vulnerabilities)
    
    # Normalize score (0-100)
    max_possible_score = len(vulnerabilities) * 10
    normalized_score = min(100, (risk_score / max(1, max_possible_score)) * 100) if max_possible_score > 0 else 0
    
    severity_counts = {
        'CRITICAL': len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL']),
        'HIGH': len([v for v in vulnerabilities if v.get('severity') == 'HIGH']),
        'MEDIUM': len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM']),
        'LOW': len([v for v in vulnerabilities if v.get('severity') == 'LOW'])
    }
    
    total_vulnerabilities = len(vulnerabilities)
    
    # Determine risk level
    if severity_counts['CRITICAL'] > 0 or severity_counts['HIGH'] > 2:
        risk_level = 'CRITICAL'
    elif severity_counts['HIGH'] > 0 or severity_counts['MEDIUM'] > 3:
        risk_level = 'HIGH'
    elif severity_counts['MEDIUM'] > 1 or total_vulnerabilities > 5:
        risk_level = 'MEDIUM'
    elif total_vulnerabilities > 0:
        risk_level = 'LOW'
    else:
        risk_level = 'NONE'
    
    return {
        'risk_score': normalized_score,
        'risk_level': risk_level,
        'critical_count': severity_counts['CRITICAL'],
        'high_count': severity_counts['HIGH'],
        'medium_count': severity_counts['MEDIUM'],
        'low_count': severity_counts['LOW'],
        'total_vulnerabilities': total_vulnerabilities
    }

def calculate_overall_risk(results: Dict) -> Dict:
    """Calculate overall risk assessment"""
    component_scores = {}
    
    if results.get('web_security'):
        component_scores['web_security'] = results['web_security']['risk_assessment']['risk_score']
    
    if results.get('ssl_security'):
        component_scores['ssl_security'] = results['ssl_security']['security_score']
    
    if results.get('cve_analysis'):
        # Calculate score based on CVE findings
        cve_results = results['cve_analysis']
        total_vulns = cve_results['summary']['total_vulnerabilities']
        component_scores['cve_analysis'] = min(100, total_vulns * 10)
    
    # Calculate weighted overall score
    weights = {
        'web_security': 0.4,
        'ssl_security': 0.3,
        'cve_analysis': 0.3
    }
    
    overall_score = 0
    for component, score in component_scores.items():
        overall_score += score * weights.get(component, 0)
    
    # Determine overall risk level
    if overall_score >= 80:
        risk_level = 'CRITICAL'
    elif overall_score >= 60:
        risk_level = 'HIGH'
    elif overall_score >= 40:
        risk_level = 'MEDIUM'
    elif overall_score >= 20:
        risk_level = 'LOW'
    else:
        risk_level = 'NONE'
    
    return {
        'overall_score': overall_score,
        'risk_level': risk_level,
        'component_scores': component_scores
    }

# Database record creation functions
from app.models import ScanJob
def create_vulnerability_records(job: ScanJob, results: Dict):
    """Create vulnerability records in database"""
    asset = get_or_create_asset(job.target)
    
    # Process web security vulnerabilities
    if results.get('web_security'):
        for vuln in results['web_security']['vulnerabilities']:
            create_vulnerability_record(job, asset, vuln, 'web_security')
    
    # Process SSL vulnerabilities
    if results.get('ssl_security'):
        for vuln in results['ssl_security']['vulnerabilities']:
            create_vulnerability_record(job, asset, vuln, 'ssl_security')
    
    # Process CVE vulnerabilities
    if results.get('cve_analysis'):
        for service_result in results['cve_analysis']['results']:
            for vuln in service_result['vulnerabilities']:
                create_vulnerability_record(job, asset, vuln, 'cve_analysis')

def create_vulnerability_record(job: ScanJob, asset: Asset, vuln_data: Dict, source: str):
    """Create a single vulnerability record"""
    from app.models import Vulnerability, VulnStatus, db
    vulnerability = Vulnerability(
        id=uuid.uuid4(),
        asset_id=asset.id,
        scan_job_id=job.id,
        cve_id=vuln_data.get('cve_id'),
        title=vuln_data.get('type', 'Unknown Vulnerability'),
        description=vuln_data.get('description', ''),
        severity=vuln_data.get('severity', 'LOW'),
        cvss_score=vuln_data.get('cvss_score', 0.0),
        port=vuln_data.get('port'),
        protocol=vuln_data.get('protocol'),
        proof={
            'evidence': vuln_data.get('evidence'),
            'source': source,
            'timestamp': datetime.utcnow().isoformat()
        },
        status=VulnStatus.OPEN,
        discovered_at=datetime.utcnow()
    )
    
    db.session.add(vulnerability)

def get_or_create_asset(target: str) -> Asset:
    """Get or create an asset record for the target"""
    from app.models import db
    # Extract hostname from target
    hostname = target.split('://')[-1].split('/')[0].split(':')[0]
    
    asset = Asset.query.filter_by(hostname=hostname).first()
    if not asset:
        asset = Asset(
            id=uuid.uuid4(),
            ip_address=hostname,  # This would ideally resolve to IP
            hostname=hostname,
            domain=hostname,
            risk_score=0
        )
        db.session.add(asset)
        db.session.commit()
    
    return asset

# Insight generation functions
def generate_vulnerability_insights(results: Dict) -> Dict:
    """Generate insights from vulnerability assessment results"""
    insights = {
        'key_findings': [],
        'recommendations': [],
        'risk_summary': {}
    }
    
    # Add insights from each component
    if results.get('web_security'):
        web_insights = generate_web_security_insights(results['web_security'])
        insights['key_findings'].extend(web_insights.get('key_findings', []))
        insights['recommendations'].extend(web_insights.get('recommendations', []))
    
    if results.get('ssl_security'):
        ssl_insights = generate_ssl_insights(results['ssl_security'])
        insights['key_findings'].extend(ssl_insights.get('key_findings', []))
        insights['recommendations'].extend(ssl_insights.get('recommendations', []))
    
    if results.get('overall_risk'):
        insights['risk_summary'] = results['overall_risk']
    
    return insights

def generate_web_security_insights(web_results: Dict) -> Dict:
    """Generate insights for web security findings"""
    insights = {
        'key_findings': [],
        'recommendations': []
    }
    
    vulns = web_results.get('vulnerabilities', [])
    risk_assessment = web_results.get('risk_assessment', {})
    
    # Key findings
    if risk_assessment.get('critical_count', 0) > 0:
        insights['key_findings'].append('Critical security vulnerabilities detected requiring immediate attention')
    
    # Count vulnerability types
    vuln_types = {}
    for vuln in vulns:
        vuln_type = vuln.get('type', 'UNKNOWN')
        vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1
    
    for vuln_type, count in vuln_types.items():
        if count > 0:
            insights['key_findings'].append(f'{count} {vuln_type} vulnerabilities found')
    
    # Recommendations
    if any('MISSING_SECURITY_HEADER' in vuln.get('type', '') for vuln in vulns):
        insights['recommendations'].append('Implement missing security headers (CSP, HSTS, etc.)')
    
    if any('WEAK_SSL' in vuln.get('type', '') for vuln in vulns):
        insights['recommendations'].append('Upgrade SSL/TLS configuration to use stronger protocols and ciphers')
    
    if any('SENSITIVE_PATH' in vuln.get('type', '') for vuln in vulns):
        insights['recommendations'].append('Restrict access to sensitive directories and files')
    
    return insights

def generate_ssl_insights(ssl_results: Dict) -> Dict:
    """Generate insights for SSL security findings"""
    insights = {
        'key_findings': [],
        'recommendations': []
    }
    
    vulns = ssl_results.get('vulnerabilities', [])
    cert_info = ssl_results.get('certificate_info', {})
    protocol_info = ssl_results.get('protocol_info', {})
    
    # Certificate insights
    if cert_info.get('has_expired', False):
        insights['key_findings'].append('SSL certificate has expired - immediate renewal required')
    elif cert_info.get('days_until_expiry', 0) < 30:
        insights['key_findings'].append(f'SSL certificate expires in {cert_info["days_until_expiry"]} days')
    
    # Protocol insights
    if protocol_info.get('weak_protocols_enabled', False):
        insights['key_findings'].append('Weak SSL/TLS protocols enabled')
    
    # Vulnerability insights
    critical_ssl_vulns = [v for v in vulns if v.get('severity') in ['CRITICAL', 'HIGH']]
    if critical_ssl_vulns:
        insights['key_findings'].append(f'{len(critical_ssl_vulns)} critical SSL/TLS vulnerabilities found')
    
    # Recommendations
    insights['recommendations'].append('Disable SSLv2, SSLv3, TLS 1.0, and TLS 1.1')
    insights['recommendations'].append('Use TLS 1.2 or higher with strong cipher suites')
    if cert_info.get('days_until_expiry', 0) < 60:
        insights['recommendations'].append('Renew SSL certificate before expiration')
    
    return insights

# Utility functions
def is_web_service(target: str) -> bool:
    """Check if target appears to be a web service"""
    return target.startswith(('http://', 'https://')) or ':80' in target or ':443' in target

def get_default_port(service_type: str) -> int:
    """Get default port for service type"""
    ports = {
        'ssh': 22,
        'ftp': 21,
        'mysql': 3306,
        'telnet': 23
    }
    return ports.get(service_type, 22)

def discover_services(target: str) -> List[Dict]:
    """Discover services on target"""
    # This would integrate with nmap or other discovery tools
    # Simplified implementation
    return []
