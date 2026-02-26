from __future__ import annotations

import ipaddress
import uuid
from typing import Any
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.auth import get_current_user, require_auth
from app.extensions import db
from app.models import JobStatus, ScanJob, ScanJobAccess, WebScanResult
from app.services.audit import record_audit_event

scans_bp = Blueprint("scans", __name__, url_prefix="/api/scans")


def normalize_target(target: str) -> str:
    return (target or "").strip()


def is_web_domain(target: str) -> bool:
    value = normalize_target(target)
    if not value:
        return False
    if value.startswith(("http://", "https://")):
        return True
    try:
        ipaddress.ip_address(value.split(":", 1)[0])
        return False
    except ValueError:
        return True


def serialize_scan_job(job: ScanJob) -> dict[str, Any]:
    return {
        "id": str(job.id),
        "target": job.target,
        "profile": job.profile,
        "status": job.status.value if job.status else "unknown",
        "progress": job.progress,
        "createdAt": job.created_at.isoformat() if job.created_at else None,
        "finishedAt": job.finished_at.isoformat() if job.finished_at else None,
        "type": "web" if job.profile == "web" else "network",
    }


def _is_admin() -> bool:
    user = get_current_user()
    return bool(user and user.role == "admin")


def _can_access_job(job_id: str) -> bool:
    user = get_current_user()
    if not user:
        return True
    if user.role == "admin":
        return True
    try:
        job_uuid = uuid.UUID(str(job_id))
    except (ValueError, TypeError):
        return False
    return ScanJobAccess.query.filter_by(job_id=job_uuid, user_id=user.id).first() is not None


def _queue_task_for_job(job: ScanJob) -> str:
    if job.profile == "web":
        from app.workers.tasks import enqueue_web_scan

        async_result = enqueue_web_scan.apply_async(args=[str(job.id), job.target, job.profile])
    else:
        from app.workers.tasks import enqueue_scan_job

        async_result = enqueue_scan_job.apply_async(args=[str(job.id), job.target, job.profile])

    config = dict(job.config or {})
    config["celery_task_id"] = async_result.id
    job.config = config
    db.session.commit()
    return async_result.id


def create_and_queue_scan(target: str, profile: str = "default", config_extra: dict[str, Any] | None = None) -> ScanJob:
    target = normalize_target(target)
    profile = (profile or "default").strip().lower()
    if profile == "default" and is_web_domain(target):
        profile = "web"
    elif profile not in {"default", "fast", "full", "quick", "detailed", "comprehensive", "safe", "web", "enhanced"}:
        profile = "default"

    job = ScanJob(
        id=uuid.uuid4(),
        target=target,
        profile=profile,
        status=JobStatus.queued,
        progress=0,
        config=config_extra or {},
    )
    db.session.add(job)
    db.session.commit()

    actor = get_current_user()
    if actor:
        db.session.add(ScanJobAccess(job_id=job.id, user_id=actor.id, access_level="owner"))
        db.session.commit()

    _queue_task_for_job(job)

    from app.routes.ws_routes import broadcast_scan_update

    broadcast_scan_update(str(job.id))
    record_audit_event(
        action="scan.create",
        resource_type="scan_job",
        resource_id=str(job.id),
        details={"target": job.target, "profile": job.profile},
    )
    return job


@scans_bp.route("/", methods=["GET"])
@require_auth()
def get_all_scans():
    try:
        status = request.args.get("status")
        profile = request.args.get("profile")
        limit = min(max(int(request.args.get("limit", 200)), 1), 1000)

        query = ScanJob.query.order_by(ScanJob.created_at.desc())
        if status:
            query = query.filter(ScanJob.status == status)
        if profile:
            query = query.filter(ScanJob.profile == profile)
        if not _is_admin():
            user = get_current_user()
            if user:
                allowed_ids = db.session.query(ScanJobAccess.job_id).filter_by(user_id=user.id)
                query = query.filter(ScanJob.id.in_(allowed_ids))

        jobs = query.limit(limit).all()
        rows = [serialize_scan_job(job) for job in jobs]

        # Enrich with web-specific data when available.
        job_ids = [job.id for job in jobs]
        if job_ids:
            web_results = (
                WebScanResult.query.filter(WebScanResult.job_id.in_(job_ids))
                .order_by(WebScanResult.created_at.desc())
                .all()
            )
            by_job = {}
            for item in web_results:
                by_job.setdefault(str(item.job_id), item)
            for row in rows:
                web_item = by_job.get(row["id"])
                if web_item:
                    row["type"] = "web"
                    row["http_status"] = web_item.http_status
                    row["issues"] = web_item.issues or []
                    row["web_scan_id"] = str(web_item.id)

        return jsonify(rows)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@scans_bp.route("/scan-jobs", methods=["GET"])
@require_auth()
def list_scan_jobs():
    return get_all_scans()


@scans_bp.route("/combined", methods=["POST", "OPTIONS"])
@require_auth()
def combined_scan():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    try:
        payload = request.get_json(silent=True) or {}
        target = normalize_target(payload.get("target", ""))
        profile = payload.get("profile", "default")
        if not target:
            return jsonify({"error": "Target is required"}), 400

        job = create_and_queue_scan(target=target, profile=profile)
        return (
            jsonify(
                {
                    "success": True,
                    "job_id": str(job.id),
                    "target": job.target,
                    "profile": job.profile,
                    "message": f"Scan for {job.target} has been queued.",
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 500


@scans_bp.route("/scan-jobs", methods=["POST"])
@require_auth()
def create_scan_job():
    return combined_scan()


@scans_bp.route("/scan-jobs/<job_id>", methods=["GET"])
@require_auth()
def get_scan_job(job_id: str):
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        if not _can_access_job(str(job.id)):
            return jsonify({"error": "Forbidden"}), 403
        payload = serialize_scan_job(job)
        payload.update(
            {
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "error": job.error or job.error_message,
            }
        )
        return jsonify(payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@scans_bp.route("/scan-jobs/<job_id>/results", methods=["GET"])
@require_auth()
def get_scan_results(job_id: str):
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        if not _can_access_job(str(job.id)):
            return jsonify({"error": "Forbidden"}), 403

        results = [
            {
                "id": result.id,
                "job_id": str(result.job_id),
                "target": result.target,
                "port": result.port,
                "protocol": result.protocol,
                "service": result.service,
                "version": result.version,
                "created_at": result.created_at.isoformat() if result.created_at else None,
            }
            for result in job.results
        ]
        return jsonify(results)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@scans_bp.route("/scan-jobs/<job_id>/logs", methods=["GET"])
@require_auth()
def get_scan_logs(job_id: str):
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        if not _can_access_job(str(job.id)):
            return jsonify({"error": "Forbidden"}), 403
        return jsonify(
            {
                "job_id": str(job.id),
                "status": job.status.value if job.status else "unknown",
                "progress": job.progress,
                "log": job.log or "",
                "error": job.error or job.error_message,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@scans_bp.route("/scan-jobs/<job_id>/retry", methods=["POST"])
@require_auth()
def retry_scan(job_id: str):
    try:
        original = ScanJob.query.get(job_id)
        if not original:
            return jsonify({"error": "Scan job not found"}), 404
        if not _can_access_job(str(original.id)):
            return jsonify({"error": "Forbidden"}), 403

        retry_job = create_and_queue_scan(target=original.target, profile=original.profile)
        retry_job.parent_scan_id = original.id
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "job_id": str(retry_job.id),
                    "target": retry_job.target,
                    "profile": retry_job.profile,
                    "message": f"Retry scan for {retry_job.target} queued.",
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@scans_bp.route("/scan-jobs/<job_id>/cancel", methods=["POST"])
@require_auth()
def cancel_scan(job_id: str):
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        if not _can_access_job(str(job.id)):
            return jsonify({"error": "Forbidden"}), 403

        config = dict(job.config or {})
        task_id = config.get("celery_task_id")
        if task_id:
            try:
                from app.workers.tasks import cel

                cel.control.revoke(task_id, terminate=True)
            except Exception as exc:
                config["cancel_warning"] = str(exc)

        job.status = JobStatus.failed
        job.progress = 0
        job.finished_at = job.finished_at or datetime.utcnow()
        prefix = "Cancelled by user request."
        job.log = f"{prefix}\n{job.log or ''}".strip()
        job.config = config
        db.session.commit()

        from app.routes.ws_routes import broadcast_scan_update

        broadcast_scan_update(str(job.id))
        record_audit_event(
            action="scan.cancel",
            resource_type="scan_job",
            resource_id=str(job.id),
            details={"task_id": task_id},
        )
        return jsonify({"success": True, "job_id": str(job.id), "status": "cancelled"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@scans_bp.route("/web-scan-jobs", methods=["POST"])
@require_auth()
def create_web_scan_job():
    try:
        payload = request.get_json(silent=True) or {}
        target = normalize_target(payload.get("url", ""))
        if not target:
            return jsonify({"error": "URL is required"}), 400

        job = create_and_queue_scan(target=target, profile="web")
        return (
            jsonify(
                {
                    "success": True,
                    "job_id": str(job.id),
                    "target": job.target,
                    "profile": job.profile,
                    "status": job.status.value,
                    "progress": job.progress,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500
