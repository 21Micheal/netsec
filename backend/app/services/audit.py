from __future__ import annotations

from typing import Any

from flask import g

from app.extensions import db
from app.models import AuditEvent


def record_audit_event(
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    status: str = "success",
    details: dict[str, Any] | None = None,
) -> None:
    actor = getattr(g, "current_user", None)
    event = AuditEvent(
        actor_id=getattr(actor, "id", None),
        actor_username=getattr(actor, "username", "anonymous") if actor else "anonymous",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        details=details or {},
    )
    db.session.add(event)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
