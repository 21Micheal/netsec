from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import ScanJob, Asset, Vulnerability
import json

insights_bp = Blueprint('insights', __name__, url_prefix='/api/insights')

@insights_bp.route('/scan/<job_id>', methods=['GET'])
def get_scan_insights(job_id):
    """Get insights for a specific scan job - FIXED VERSION"""
    try:
        from app.models import WebScanResult
        
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        print(f"🔍 Fetching insights for job {job_id}, profile: {job.profile}")
        
        insights = {}
        vulnerabilities = []
        
        # Handle web scans differently
        if job.profile == 'web' or (job.insights and 'web_results' in job.insights):
            print(f"🌐 Processing web scan insights for {job_id}")
            
            # Get web results from database
            web_results_list = WebScanResult.query.filter_by(job_id=job_id).all()
            
            if web_results_list:
                web_result = web_results_list[0]  # Take first result
                insights = {
                    'target': job.target,
                    'web_results': {
                        'url': web_result.url,
                        'http_status': web_result.http_status,
                        'headers': web_result.headers or {},
                        'cookies': web_result.cookies or {},
                        'issues': web_result.issues or []
                    },
                    'security_indicators': web_result.issues or [],
                    'summary': {
                        'http_status': web_result.http_status,
                        'headers_count': len(web_result.headers or {}),
                        'cookies_count': len(web_result.cookies or {}),
                        'security_issues': len(web_result.issues or []),
                        'risk_level': 'HIGH' if len(web_result.issues or []) > 3 else 
                                     'MEDIUM' if len(web_result.issues or []) > 0 else 
                                     'LOW'
                    }
                }
                print(f"✅ Found web results: {len(web_result.issues or [])} issues")
            else:
                print(f"❌ No web results found for job {job_id}")
                
        else:
            # Handle network scans - use insights field directly
            insights = job.insights or {}
            print(f"🔧 Processing network scan insights for {job_id}: {len(insights.get('open_ports', []))} open ports")
        
        # Get vulnerabilities
        vulnerabilities = Vulnerability.query.filter_by(scan_job_id=job_id).all()
        
        response_data = {
            "job_id": job_id,
            "target": job.target,
            "profile": job.profile,
            "status": job.status.value,
            "insights": insights,
            "vulnerabilities": [vuln.to_dict() for vuln in vulnerabilities],
            "summary": {
                "open_ports": len(insights.get('open_ports', [])),
                "services_found": len(insights.get('services', [])),
                "security_indicators": len(insights.get('security_indicators', [])),
                "risk_level": insights.get('summary', {}).get('risk_level', 'UNKNOWN')
            }
        }
        
        print(f"✅ Returning insights for {job_id}: {response_data['summary']}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error getting insights for {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@insights_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        # Total scans
        total_scans = ScanJob.query.count()
        completed_scans = ScanJob.query.filter_by(status='finished').count()
        failed_scans = ScanJob.query.filter_by(status='failed').count()
        
        # Assets and vulnerabilities
        total_assets = Asset.query.count()
        total_vulnerabilities = Vulnerability.query.count()
        critical_vulnerabilities = Vulnerability.query.filter_by(severity='CRITICAL').count()
        
        # Recent findings
        recent_vulnerabilities = Vulnerability.query.order_by(
            Vulnerability.discovered_at.desc()
        ).limit(10).all()
        
        # Service distribution
        services_found = get_service_distribution()
        
        # Risk distribution
        risk_distribution = get_risk_distribution()
        
        return jsonify({
            "scan_stats": {
                "total": total_scans,
                "completed": completed_scans,
                "failed": failed_scans,
                "success_rate": (completed_scans / total_scans * 100) if total_scans > 0 else 0
            },
            "asset_stats": {
                "total_assets": total_assets,
                "total_vulnerabilities": total_vulnerabilities,
                "critical_vulnerabilities": critical_vulnerabilities,
                "avg_risk_score": get_average_risk_score()
            },
            "recent_findings": [
                {
                    "id": str(vuln.id),
                    "title": vuln.title,
                    "severity": vuln.severity,
                    "asset": vuln.asset.ip_address if vuln.asset else 'Unknown',
                    "discovered_at": vuln.discovered_at.isoformat()
                }
                for vuln in recent_vulnerabilities
            ],
            "service_distribution": services_found,
            "risk_distribution": risk_distribution
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@insights_bp.route('/assets/risk-overview', methods=['GET'])
def get_assets_risk_overview():
    """Get risk overview for all assets"""
    try:
        assets = Asset.query.order_by(Asset.risk_score.desc()).all()
        
        return jsonify([
            {
                "id": str(asset.id),
                "ip_address": asset.ip_address,
                "hostname": asset.hostname,
                "risk_score": asset.risk_score,
                "vulnerability_count": Vulnerability.query.filter_by(asset_id=asset.id).count(),
                "last_seen": asset.last_seen.isoformat(),
                "tags": asset.tags or {}
            }
            for asset in assets
        ])
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_service_distribution():
    """Get distribution of services found across all scans"""
    # This would query your database for service distribution
    # For now, return mock data that will be populated by real scans
    return {
        "HTTP": 15,
        "HTTPS": 12,
        "SSH": 8,
        "FTP": 3,
        "MySQL": 2,
        "PostgreSQL": 1,
        "RDP": 2,
        "SMB": 4
    }

def get_risk_distribution():
    """Get risk distribution across assets"""
    assets = Asset.query.all()
    distribution = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    
    for asset in assets:
        if asset.risk_score >= 80:
            distribution["CRITICAL"] += 1
        elif asset.risk_score >= 60:
            distribution["HIGH"] += 1
        elif asset.risk_score >= 40:
            distribution["MEDIUM"] += 1
        elif asset.risk_score >= 20:
            distribution["LOW"] += 1
        else:
            distribution["INFO"] += 1
    
    return distribution

def get_average_risk_score():
    """Calculate average risk score across all assets"""
    assets = Asset.query.all()
    if not assets:
        return 0
    return sum(asset.risk_score for asset in assets) / len(assets)

@insights_bp.route('/debug/web-results/<job_id>', methods=['GET'])
def debug_web_results(job_id):
    """Debug web scan results storage"""
    try:
        from app.models import WebScanResult
        
        web_results = WebScanResult.query.filter_by(job_id=job_id).all()
        
        return jsonify({
            "job_id": job_id,
            "web_results_count": len(web_results),
            "web_results": [{
                "id": wr.id,
                "url": wr.url,
                "http_status": wr.http_status,
                "headers_count": len(wr.headers or {}),
                "cookies_count": len(wr.cookies or {}),
                "issues_count": len(wr.issues or [])
            } for wr in web_results]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500