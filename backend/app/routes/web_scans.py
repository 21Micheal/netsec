from flask import Blueprint, request, jsonify
from app.models import ScanJob, WebScanResult
from app.extensions import db, socketio
# from app.workers.tasks import enqueue_web_scan
import uuid

web_bp = Blueprint("web_scans", __name__)

@web_bp.route("/web-scans", methods=["POST", "OPTIONS"])
def start_web_scan():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        data = request.get_json()
        url = data.get("url")
        profile = data.get("profile", "web")

        if not url:
            return jsonify({"error": "URL is required"}), 400

        # Create the scan job
        job = ScanJob(
            id=uuid.uuid4(),
            target=url,
            profile=profile,
            status="queued",
        )
        db.session.add(job)
        db.session.commit()

        # Emit socket event for new scan
        socketio.emit("scan_update", {
            "job_id": str(job.id),
            "status": job.status.value,
            "progress": job.progress,
            "target": job.target,
            "profile": job.profile
        })

        # Queue the web scan task
        from app.workers.tasks import enqueue_web_scan
        enqueue_web_scan.delay(str(job.id), url, profile)
        
        return jsonify({
            "id": str(job.id),
            "job_id": str(job.id),
            "target": job.target,
            "profile": job.profile,
            "status": job.status.value,
            "progress": job.progress,
            "created_at": job.created_at.isoformat()
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@web_bp.route("/web-scans/results/<job_id>", methods=["GET", "OPTIONS"])
def get_web_scan_results(job_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        results = WebScanResult.query.filter_by(job_id=job_id).all()
        return jsonify([{
            "id": r.id,
            "job_id": str(r.job_id),
            "url": r.url,
            "http_status": r.http_status,
            "headers": r.headers,
            "cookies": r.cookies,
            "issues": r.issues,
            "created_at": r.created_at.isoformat() if r.created_at else None
        } for r in results])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Additional endpoint to get all web scan jobs
@web_bp.route("/web-scans/jobs", methods=["GET", "OPTIONS"])
def get_web_scan_jobs():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        # Get only web scan jobs
        jobs = ScanJob.query.filter(ScanJob.profile == 'web').order_by(ScanJob.created_at.desc()).all()
        return jsonify([{
            'id': str(job.id),
            'target': job.target,
            'profile': job.profile,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'finished_at': job.finished_at.isoformat() if job.finished_at else None
        } for job in jobs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500