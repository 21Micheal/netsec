from __future__ import annotations

from functools import wraps
from typing import Iterable

from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer

from app.extensions import db
from app.models import User


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="netsec-auth")


def generate_access_token(user: User) -> str:
    return _serializer().dumps({"sub": str(user.id), "username": user.username, "role": user.role})


def verify_access_token(token: str):
    try:
        payload = _serializer().loads(
            token,
            max_age=current_app.config.get("ACCESS_TOKEN_TTL_SECONDS", 43200),
        )
        return payload
    except (BadSignature, BadTimeSignature):
        return None


def _resolve_user_from_request():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    payload = verify_access_token(token)
    if not payload:
        return None
    user = User.query.get(payload.get("sub"))
    if not user or not user.is_active:
        return None
    return user


def get_current_user():
    if hasattr(g, "current_user"):
        return g.current_user
    user = _resolve_user_from_request()
    g.current_user = user
    return user


def require_auth(roles: Iterable[str] | None = None):
    role_set = set(roles or [])

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            auth_required = current_app.config.get("AUTH_REQUIRED", False)

            if not user:
                if role_set:
                    return jsonify({"error": "Authentication required"}), 401
                if auth_required:
                    return jsonify({"error": "Authentication required"}), 401
                g.current_user = None
                return fn(*args, **kwargs)

            if role_set and user.role not in role_set:
                return jsonify({"error": "Forbidden"}), 403

            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_admin(fn):
    return require_auth(roles={"admin"})(fn)


def actor_snapshot():
    user = get_current_user()
    if not user:
        return {"actor_id": None, "actor_username": "anonymous"}
    return {"actor_id": user.id, "actor_username": user.username}


def commit_with_rollback():
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False
