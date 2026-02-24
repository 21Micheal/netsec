from flask import Blueprint, request, jsonify, current_app
from . import db
from app import socketio
from .models import ScanJob, ScanResult, JobStatus
from uuid import UUID
from .workers.tasks import enqueue_scan_job, enqueue_web_scan
from sqlalchemy import desc
from uuid import UUID

api_bp = Blueprint("api", __name__)

@api_bp.route("/scans", methods=["POST"])
def create_scan():
    data = request.get_json() or {}
    target = data.get("target")
    profile = data.get("profile", "default")
    if not target:
        return jsonify({"error": "target is required"}), 400

    job = ScanJob(target=target, profile=profile)
    db.session.add(job)
    db.session.commit()

    # enqueue async task
    enqueue_scan_job.delay(str(job.id), target, profile)

    return jsonify({"jobId": str(job.id), "status": job.status.value}), 201

@api_bp.route("/ping")
def ping():
    socketio.emit("scan_update", {"message": "pong"})
    return {"message": "pong"}

@api_bp.route("/scans", methods=["GET"])
def list_scans():
    jobs = ScanJob.query.order_by(desc(ScanJob.created_at)).all()
    return jsonify([
        {
            "id": str(job.id),
            "target": job.target,
            "profile": job.profile,
            "status": job.status.value,
            "createdAt": job.created_at.isoformat() if job.created_at else None,
            "finishedAt": job.finished_at.isoformat() if job.finished_at else None,
            "progress": job.progress   # ✅ include progress
        }
        for job in jobs
    ])


@api_bp.route("/scans/<job_id>/results", methods=["GET"])
def get_results(job_id):
    """
    Return structured scan results for a given job_id.

    Response format:
    {
      "job": { "id": "...", "target": "...", "profile": "...", "status": "...", "createdAt": "...", "finishedAt": "..." },
      "hosts": {
         "<ip-or-hostname>": [
             { "port": 22, "protocol": "tcp", "service": "ssh", "version": "OpenSSH 8.2", "raw": { ... } },
             ...
         ],
         ...
      }
    }
    """
    # validate UUID
    try:
        UUID(job_id)
    except Exception:
        return jsonify({"error": "invalid job id"}), 400

    # ensure job exists
    job = ScanJob.query.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404

    # fetch results grouped by target
    rows = (
        ScanResult.query
        .filter_by(job_id=job_id)
        .order_by(ScanResult.target.asc(), ScanResult.port.asc())
        .all()
    )

    hosts = {}
    for r in rows:
        key = r.target or "unknown"
        if key not in hosts:
            hosts[key] = []
        hosts[key].append({
            "port": r.port,
            "protocol": r.protocol,
            "service": r.service,
            "version": r.version,
            "raw": r.raw_output
        })

    resp = {
        "job": {
            "id": str(job.id),
            "target": job.target,
            "profile": job.profile,
            "status": job.status.value,
            "createdAt": job.created_at.isoformat() if job.created_at else None,
            "finishedAt": job.finished_at.isoformat() if job.finished_at else None
        },
        "hosts": hosts
    }
    return jsonify(resp)

#web scan endpoints would go here
@api_bp.route("/webscans", methods=["POST"])
def create_web_scan():
    data = request.get_json() or {}
    url = data.get("url")
    profile = data.get("profile", "default")
    if not url:
        return jsonify({"error": "url is required"}), 400

    job = ScanJob(target=url, profile=profile)
    db.session.add(job)
    db.session.commit()

    # enqueue web scan
    enqueue_web_scan.delay(str(job.id), url, profile)

    return jsonify({"jobId": str(job.id), "status": job.status.value}), 201

@api_bp.route("/webscans/<job_id>/results", methods=["GET"])
def webscan_results(job_id):
    try:
        UUID(job_id)
    except Exception:
        return jsonify({"error": "invalid job id"}), 400

    # fetch latest result row for job
    sql = "SELECT url, http_status, headers, cookies, issues, created_at FROM web_scan_results WHERE job_id = %s ORDER BY created_at DESC LIMIT 1"
    res = db.session.execute(sql, (job_id,))
    row = res.fetchone()
    if not row:
        # no results yet (still running)
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "job not found"}), 404
        return jsonify({"job": {"id": str(job.id), "status": job.status.value}}), 200

    url, http_status, headers, cookies, issues, created_at = row
    return jsonify({
        "job": {"id": job_id, "status": ScanJob.query.get(job_id).status.value},
        "url": url,
        "http_status": http_status,
        "headers": headers,
        "cookies": cookies,
        "issues": issues,
        "created_at": created_at.isoformat() if created_at else None
    })
