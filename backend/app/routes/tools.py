from __future__ import annotations

import socket
import ssl
from datetime import datetime
from urllib.parse import urlparse

import requests
from flask import Blueprint, jsonify, request

from app.auth import require_auth
from app.services.audit import record_audit_event

tools_bp = Blueprint("tools", __name__, url_prefix="/api/tools")


def _normalize_host(target: str) -> str:
    value = (target or "").strip()
    if not value:
        return value
    if "://" in value:
        value = urlparse(value).hostname or value
    return value.split("/", 1)[0].split(":", 1)[0]


@tools_bp.post("/dns")
@require_auth()
def dns_lookup():
    payload = request.get_json(silent=True) or {}
    target = _normalize_host(payload.get("target", ""))
    if not target:
        return jsonify({"error": "target is required"}), 400

    try:
        host, aliases, ips = socket.gethostbyname_ex(target)
        response = jsonify(
            {
                "target": target,
                "canonical_name": host,
                "aliases": aliases,
                "ips": sorted(set(ips)),
            }
        )
        record_audit_event("tool.dns_lookup", "tool", details={"target": target})
        return response
    except Exception as exc:
        return jsonify({"target": target, "error": str(exc)}), 400


@tools_bp.post("/tcp")
@require_auth()
def tcp_probe():
    payload = request.get_json(silent=True) or {}
    target = _normalize_host(payload.get("target", ""))
    ports = payload.get("ports") or [22, 80, 443, 3306, 5432]
    timeout = min(max(int(payload.get("timeout", 2)), 1), 10)

    if not target:
        return jsonify({"error": "target is required"}), 400

    results = []
    for port in ports[:100]:
        try:
            port_int = int(port)
        except (TypeError, ValueError):
            continue

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        started = datetime.utcnow()
        try:
            status = sock.connect_ex((target, port_int))
            latency_ms = (datetime.utcnow() - started).total_seconds() * 1000
            results.append(
                {
                    "port": port_int,
                    "open": status == 0,
                    "latency_ms": round(latency_ms, 2),
                }
            )
        finally:
            sock.close()

    record_audit_event("tool.tcp_probe", "tool", details={"target": target, "ports": ports[:100]})
    return jsonify({"target": target, "results": results})


@tools_bp.post("/http-headers")
@require_auth()
def http_headers():
    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        response = requests.get(url, timeout=10, allow_redirects=True, verify=False)
        response = jsonify(
            {
                "url": url,
                "final_url": response.url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }
        )
        record_audit_event("tool.http_headers", "tool", details={"url": url, "status_code": response.status_code})
        return response
    except Exception as exc:
        return jsonify({"url": url, "error": str(exc)}), 400


@tools_bp.post("/tls")
@require_auth()
def tls_info():
    payload = request.get_json(silent=True) or {}
    host = _normalize_host(payload.get("host") or payload.get("target") or "")
    port = int(payload.get("port", 443))

    if not host:
        return jsonify({"error": "host is required"}), 400

    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as secure_sock:
                cert = secure_sock.getpeercert()
                cipher = secure_sock.cipher()
                payload = jsonify(
                    {
                        "host": host,
                        "port": port,
                        "cipher": cipher[0] if cipher else None,
                        "protocol": secure_sock.version(),
                        "subject": dict(x[0] for x in cert.get("subject", [])),
                        "issuer": dict(x[0] for x in cert.get("issuer", [])),
                        "not_before": cert.get("notBefore"),
                        "not_after": cert.get("notAfter"),
                    }
                )
                record_audit_event("tool.tls_info", "tool", details={"host": host, "port": port})
                return payload
    except Exception as exc:
        return jsonify({"host": host, "port": port, "error": str(exc)}), 400
