from flask import Blueprint, request, jsonify
from app.extensions import db, socketio
from app.services.asset_manager import AssetManager
from app.models import ScanJob, Asset, Vulnerability, IntelligenceReport
from app.services.risk_detector import RiskDetectionEngine
from app.services.report_generator import ReportGenerator
from app.utils.advanced_scanners import AdvancedReconnaissance
import uuid
from datetime import datetime
import json
from typing import Dict, Any

advanced_bp = Blueprint('advanced', __name__, url_prefix='/api/advanced')

@advanced_bp.route('/comprehensive-scan', methods=['POST'])
def start_comprehensive_scan():
    """Start a comprehensive security assessment"""
    try:
        data = request.get_json()
        target = data.get('target')
        scan_type = data.get('scan_type', 'full')
        
        if not target:
            return jsonify({"error": "Target is required"}), 400
        
        # Create scan job
        job_id = str(uuid.uuid4())
        job = ScanJob(
            id=job_id,
            target=target,
            profile=f"comprehensive_{scan_type}",
            status="queued"
        )
        db.session.add(job)
        db.session.commit()
        
        # Start comprehensive scan
        from app.workers.tasks import enqueue_comprehensive_scan
        enqueue_comprehensive_scan.delay(job_id, target, scan_type)
        
        return jsonify({
            "job_id": job_id,
            "message": f"Comprehensive security assessment started for {target}",
            "scan_type": scan_type
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@advanced_bp.route('/assets', methods=['GET'])
def get_assets():
    """Get all discovered assets with risk scores"""
    try:
        asset_manager = AssetManager()
        assets = asset_manager.get_assets_with_risk()
        
        return jsonify(assets)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@advanced_bp.route('/assets/<asset_id>', methods=['GET'])
def get_asset_details(asset_id):
    """Get detailed information about a specific asset"""
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({"error": "Asset not found"}), 404
        
        # Get related vulnerabilities
        vulnerabilities = Vulnerability.query.filter_by(asset_id=asset_id).all()
        
        # Get scan history
        scan_jobs = ScanJob.query.filter_by(asset_id=asset_id)\
            .order_by(ScanJob.created_at.desc())\
            .limit(10)\
            .all()
        
        return jsonify({
            "asset": asset.to_dict(),
            "vulnerabilities": [vuln.to_dict() for vuln in vulnerabilities],
            "scan_history": [job.to_dict() for job in scan_jobs]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@advanced_bp.route('/risk-assessment/<job_id>', methods=['GET'])
def get_risk_assessment(job_id):
    """Get risk assessment for a completed scan"""
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if job.status != 'finished':
            return jsonify({"error": "Scan not completed"}), 400
        
        # Generate or retrieve risk assessment
        risk_engine = RiskDetectionEngine()
        
        # Collect scan results (you'll need to implement this based on your data structure)
        scan_data = collect_scan_data(job_id)
        
        risk_assessment = risk_engine.analyze_scan_results(scan_data)
        
        return jsonify({
            "job_id": job_id,
            "target": job.target,
            "risk_assessment": risk_assessment,
            "generated_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@advanced_bp.route('/generate-report/<job_id>', methods=['POST'])
def generate_report(job_id):
    """Generate comprehensive security report"""
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        report_type = request.json.get('report_type', 'comprehensive')
        
        # Collect data and generate report
        scan_data = collect_scan_data(job_id)
        risk_engine = RiskDetectionEngine()
        risk_assessment = risk_engine.analyze_scan_results(scan_data)
        
        report_gen = ReportGenerator()
        report_data = report_gen.generate_comprehensive_report(scan_data, risk_assessment)
        
        # Save report to database
        report = IntelligenceReport(
            target=job.target,
            report_type=report_type,
            data=report_data,
            risk_assessment=risk_assessment,
            recommendations=report_data.get('recommendations', [])
        )
        db.session.add(report)
        db.session.commit()
        
        # Generate PDF if requested
        pdf_path = None
        if request.json.get('include_pdf'):
            pdf_path = report_gen.generate_pdf_report(report_data)
        
        return jsonify({
            "report_id": str(report.id),
            "report_data": report_data,
            "pdf_url": f"/api/reports/{report.id}/pdf" if pdf_path else None,
            "message": "Report generated successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @advanced_bp.route('/assets', methods=['GET'])
# def get_assets():
#     """Get all discovered assets with risk scores"""
#     try:
#         assets = Asset.query.order_by(Asset.risk_score.desc()).all()
        
#         return jsonify([{
#             "id": str(asset.id),
#             "ip_address": asset.ip_address,
#             "hostname": asset.hostname,
#             "domain": asset.domain,
#             "risk_score": asset.risk_score,
#             "first_seen": asset.first_seen.isoformat(),
#             "last_seen": asset.last_seen.isoformat(),
#             "tags": asset.tags or {},
#             "vulnerability_count": len(asset.vulnerabilities)
#         } for asset in assets])
        
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

def collect_scan_data(job_id: str) -> Dict[str, Any]:
    """Collect all scan data for a job (implement based on your data structure)"""
    # This would query your database for nmap results, web scan results, etc.
    # Placeholder implementation
    return {
        "target": "example.com",
        "nmap_results": {},
        "web_results": {},
        "services": []
    }