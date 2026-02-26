from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.auth import generate_access_token, get_current_user, require_admin, require_auth
from app.extensions import db
from app.models import User
from app.services.audit import record_audit_event

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/bootstrap-status")
def bootstrap_status():
    return jsonify({"bootstrap_required": User.query.count() == 0}), 200


@auth_bp.post("/register")
@require_admin
def register_user():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip().lower()
    password = payload.get("password") or ""
    role = (payload.get("role") or "analyst").strip().lower()

    if not username or len(password) < 10:
        return jsonify({"error": "username and a 10+ char password are required"}), 400
    if role not in {"admin", "analyst"}:
        return jsonify({"error": "role must be admin or analyst"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 409

    user = User(username=username, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    record_audit_event(
        action="auth.register",
        resource_type="user",
        resource_id=str(user.id),
        details={"username": user.username, "role": user.role},
    )
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.post("/bootstrap")
def bootstrap_admin():
    if User.query.count() > 0:
        return jsonify({"error": "bootstrap already completed"}), 409

    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "admin").strip().lower()
    password = payload.get("password") or ""
    if len(password) < 10:
        return jsonify({"error": "password must be at least 10 chars"}), 400

    user = User(username=username, role="admin", is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    token = generate_access_token(user)

    return jsonify({"message": "bootstrap complete", "token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip().lower()
    password = payload.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password) or not user.is_active:
        record_audit_event(
            action="auth.login",
            resource_type="session",
            status="failed",
            details={"username": username, "reason": "invalid_credentials"},
        )
        return jsonify({"error": "invalid credentials"}), 401

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    token = generate_access_token(user)
    record_audit_event(
        action="auth.login",
        resource_type="session",
        resource_id=str(user.id),
        details={"username": user.username},
    )
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.get("/me")
@require_auth()
def me():
    user = get_current_user()
    if not user:
        return jsonify({"authenticated": False}), 200
    return jsonify({"authenticated": True, "user": user.to_dict()}), 200


@auth_bp.get("/users")
@require_admin
def list_users():
    users = User.query.order_by(User.created_at.asc()).all()
    return jsonify([user.to_dict() for user in users]), 200
