from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.auth import require_admin
from app.models import AuditEvent

audit_bp = Blueprint("audit", __name__, url_prefix="/api/audit")


@audit_bp.get("/events")
@require_admin
def list_events():
    limit = min(max(int(request.args.get("limit", 200)), 1), 1000)
    action = request.args.get("action")
    actor = request.args.get("actor")

    query = AuditEvent.query.order_by(AuditEvent.created_at.desc())
    if action:
        query = query.filter(AuditEvent.action == action)
    if actor:
        query = query.filter(AuditEvent.actor_username == actor)

    events = query.limit(limit).all()
    return jsonify([event.to_dict() for event in events]), 200
