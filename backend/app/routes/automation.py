from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.auth import get_current_user, require_auth
from app.extensions import db
from app.models import ScanDiffReport, ScanJob, ScanJobAccess, ScanPlaybook, Vulnerability, WebScanResult
from app.routes.scans import create_and_queue_scan
from app.services.audit import record_audit_event

automation_bp = Blueprint("automation", __name__, url_prefix="/api/automation")


def _is_admin() -> bool:
    user = get_current_user()
    return bool(user and user.role == "admin")


def _has_job_access(job_id: str) -> bool:
    user = get_current_user()
    if not user:
        return True
    if user.role == "admin":
        return True
    try:
        job_uuid = UUID(str(job_id))
    except (ValueError, TypeError):
        return False
    return ScanJobAccess.query.filter_by(job_id=job_uuid, user_id=user.id).first() is not None


def _visible_playbooks_query():
    user = get_current_user()
    query = ScanPlaybook.query.order_by(ScanPlaybook.created_at.desc())
    if user and user.role != "admin":
        query = query.filter(ScanPlaybook.owner_id == user.id)
    return query


def _extract_signature(job: ScanJob) -> dict:
    insights = job.insights or {}
    open_ports = sorted({int(p.get("port")) for p in (insights.get("open_ports") or []) if p.get("port") is not None})
    services = sorted({s.get("name") for s in (insights.get("services") or []) if s.get("name")})
    risk = insights.get("summary", {}).get("risk_level", "UNKNOWN")

    web_results = WebScanResult.query.filter_by(job_id=job.id).all()
    web_issue_types = sorted(
        {
            issue.get("type")
            for row in web_results
            for issue in (row.issues or [])
            if isinstance(issue, dict) and issue.get("type")
        }
    )

    vulns = Vulnerability.query.filter_by(scan_job_id=job.id).all()
    vuln_titles = sorted({v.title for v in vulns if v.title})

    return {
        "open_ports": open_ports,
        "services": services,
        "risk_level": risk,
        "web_issue_types": web_issue_types,
        "vulnerability_titles": vuln_titles,
    }


def _compute_diff(old_job: ScanJob, new_job: ScanJob) -> dict:
    old_sig = _extract_signature(old_job)
    new_sig = _extract_signature(new_job)

    def set_diff(key: str):
        old_set = set(old_sig.get(key, []))
        new_set = set(new_sig.get(key, []))
        return {"added": sorted(new_set - old_set), "removed": sorted(old_set - new_set)}

    return {
        "old_job_id": str(old_job.id),
        "new_job_id": str(new_job.id),
        "generated_at": datetime.utcnow().isoformat(),
        "risk_level": {"old": old_sig.get("risk_level"), "new": new_sig.get("risk_level")},
        "open_ports": set_diff("open_ports"),
        "services": set_diff("services"),
        "web_issue_types": set_diff("web_issue_types"),
        "vulnerability_titles": set_diff("vulnerability_titles"),
    }


@automation_bp.post("/playbooks")
@require_auth()
def create_playbook():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    target = (payload.get("target") or "").strip()
    profile = (payload.get("profile") or "default").strip().lower()
    schedule_minutes = int(payload.get("schedule_minutes") or 60)
    if not name or not target:
        return jsonify({"error": "name and target are required"}), 400
    schedule_minutes = max(5, min(schedule_minutes, 10080))

    user = get_current_user()
    playbook = ScanPlaybook(
        owner_id=getattr(user, "id", None),
        name=name,
        target=target,
        profile=profile,
        schedule_minutes=schedule_minutes,
        enabled=bool(payload.get("enabled", True)),
        tags=payload.get("tags") or {},
    )
    db.session.add(playbook)
    db.session.commit()
    record_audit_event("playbook.create", "playbook", str(playbook.id), details=playbook.to_dict())
    return jsonify(playbook.to_dict()), 201


@automation_bp.get("/playbooks")
@require_auth()
def list_playbooks():
    rows = _visible_playbooks_query().all()
    return jsonify([row.to_dict() for row in rows]), 200


@automation_bp.post("/playbooks/<playbook_id>/run")
@require_auth()
def run_playbook(playbook_id: str):
    playbook = _visible_playbooks_query().filter_by(id=playbook_id).first()
    if not playbook:
        return jsonify({"error": "Playbook not found"}), 404

    job = create_and_queue_scan(
        target=playbook.target,
        profile=playbook.profile,
        config_extra={"playbook_id": str(playbook.id), "playbook_name": playbook.name},
    )
    playbook.last_run_at = datetime.utcnow()
    playbook.last_job_id = job.id
    db.session.commit()
    record_audit_event("playbook.run", "playbook", str(playbook.id), details={"job_id": str(job.id)})
    return jsonify({"playbook_id": str(playbook.id), "job_id": str(job.id)}), 201


@automation_bp.post("/run-due")
@require_auth()
def run_due_playbooks():
    if not _is_admin():
        return jsonify({"error": "Admin role required"}), 403

    now = datetime.utcnow()
    limit = max(1, min(int(request.args.get("limit", 20)), 100))
    all_enabled = ScanPlaybook.query.filter_by(enabled=True).all()
    runnable = []
    for pb in all_enabled:
        if pb.last_run_at is None:
            runnable.append(pb)
            continue
        if now - pb.last_run_at >= timedelta(minutes=pb.schedule_minutes):
            runnable.append(pb)
    runnable = runnable[:limit]

    created = []
    for pb in runnable:
        job = create_and_queue_scan(
            target=pb.target,
            profile=pb.profile,
            config_extra={"playbook_id": str(pb.id), "playbook_name": pb.name},
        )
        pb.last_run_at = now
        pb.last_job_id = job.id
        created.append({"playbook_id": str(pb.id), "job_id": str(job.id)})
    db.session.commit()
    record_audit_event("playbook.run_due", "playbook", details={"created": len(created)})
    return jsonify({"created": created, "count": len(created)}), 200


@automation_bp.get("/reports/job/<job_id>")
@require_auth()
def get_job_artifact(job_id: str):
    if not _has_job_access(job_id):
        return jsonify({"error": "Forbidden"}), 403
    job = ScanJob.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    web_rows = WebScanResult.query.filter_by(job_id=job.id).all()
    vulns = Vulnerability.query.filter_by(scan_job_id=job.id).all()
    payload = {
        "job": job.to_dict(),
        "network_results": [
            {
                "id": row.id,
                "target": row.target,
                "port": row.port,
                "protocol": row.protocol,
                "service": row.service,
                "version": row.version,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in job.results
        ],
        "web_results": [row.to_dict() for row in web_rows],
        "vulnerabilities": [v.to_dict() for v in vulns],
        "insights": job.insights or {},
        "generated_at": datetime.utcnow().isoformat(),
    }
    return jsonify(payload), 200


@automation_bp.post("/reports/diff")
@require_auth()
def create_diff_report():
    payload = request.get_json(silent=True) or {}
    old_job_id = payload.get("old_job_id")
    new_job_id = payload.get("new_job_id")
    if not old_job_id or not new_job_id:
        return jsonify({"error": "old_job_id and new_job_id are required"}), 400
    if not _has_job_access(old_job_id) or not _has_job_access(new_job_id):
        return jsonify({"error": "Forbidden"}), 403

    old_job = ScanJob.query.get(old_job_id)
    new_job = ScanJob.query.get(new_job_id)
    if not old_job or not new_job:
        return jsonify({"error": "One or both jobs not found"}), 404

    diff = _compute_diff(old_job, new_job)
    user = get_current_user()
    existing = ScanDiffReport.query.filter_by(old_job_id=old_job.id, new_job_id=new_job.id).first()
    if existing:
        existing.diff = diff
        existing.generated_by = getattr(user, "id", None)
        report = existing
    else:
        report = ScanDiffReport(
            old_job_id=old_job.id,
            new_job_id=new_job.id,
            generated_by=getattr(user, "id", None),
            diff=diff,
        )
        db.session.add(report)
    db.session.commit()
    record_audit_event("report.diff", "scan_diff", str(report.id), details={"old_job_id": old_job_id, "new_job_id": new_job_id})
    return jsonify(report.to_dict()), 201


@automation_bp.get("/reports/diff")
@require_auth()
def list_diff_reports():
    limit = max(1, min(int(request.args.get("limit", 100)), 500))
    rows = ScanDiffReport.query.order_by(ScanDiffReport.created_at.desc()).limit(limit).all()
    visible = [row.to_dict() for row in rows if _has_job_access(str(row.old_job_id)) and _has_job_access(str(row.new_job_id))]
    return jsonify(visible), 200
