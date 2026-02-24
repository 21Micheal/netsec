"""
Enhanced scan routes - Create this file as: app/routes/enhanced_routes.py
Then register it in your app factory: app.register_blueprint(enhanced_bp)
"""

from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import ScanJob, JobStatus
import uuid

enhanced_bp = Blueprint('enhanced', __name__, url_prefix='/api/enhanced')


@enhanced_bp.route("/scan", methods=["POST", "OPTIONS"])
def create_enhanced_scan():
    """✅ Enhanced scan endpoint with proper job_id return"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        data = request.get_json()
        target = data.get("target")
        scan_type = data.get("scan_type", "comprehensive")

        if not target:
            return jsonify({"error": "Target is required"}), 400

        # Create Job entry
        job_id = str(uuid.uuid4())
        new_job = ScanJob(
            id=job_id,
            target=target,
            profile="enhanced",
            status=JobStatus.queued,
            progress=0
        )
        db.session.add(new_job)
        db.session.commit()

        print(f"✅ Created enhanced scan job {job_id} for target: {target} (type: {scan_type})")

        # Broadcast initial state
        from app.routes.ws_routes import broadcast_scan_update
        broadcast_scan_update(job_id)

        # Queue the enhanced task
        from app.workers.tasks import enqueue_enhanced_scan
        enqueue_enhanced_scan.apply_async(args=[job_id, target, scan_type])
        print(f"⚡ Queued enhanced scan task for job {job_id}")

        # ✅ CRITICAL: Return job_id for immediate subscription
        return jsonify({
            "success": True,
            "job_id": job_id,
            "target": target,
            "scan_type": scan_type,
            "message": f"Enhanced scan for {target} has been queued."
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating enhanced scan: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@enhanced_bp.route("/technologies/<job_id>", methods=["GET"])
def get_enhanced_technologies(job_id):
    """Get enhanced scan technologies/results"""
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify({
            "job_id": job_id,
            "target": job.target,
            "status": job.status.value,
            "insights": job.insights or {},
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching enhanced results: {e}")
        return jsonify({"error": str(e)}), 500