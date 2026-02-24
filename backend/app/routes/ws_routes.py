import json
from flask import request
from flask_socketio import join_room, leave_room, emit
from ..extensions import socketio
from ..models import db, ScanJob
from datetime import datetime
import uuid

# Track connected clients to prevent duplicates
connected_clients = set()

# --- Utility Functions ---
def make_serializable(obj):
    """Recursively convert non-serializable objects to serializable formats"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif hasattr(obj, 'value'):
        return obj.value
    else:
        try:
            return str(obj)
        except:
            return None

def safe_emit(event, data, room=None):
    """Emit safely, converting data to a serializable format"""
    try:
        serializable_data = make_serializable(data)
        socketio.emit(event, serializable_data, room=room)
        print(f"[WebSocket] Emitted {event} to room {room or 'default'}")
    except Exception as e:
        print(f"[WebSocket Error] Emit failed for event '{event}': {e}")

# --- WebSocket Event Handlers ---
@socketio.on("connect")
def handle_connect():
    client_id = request.sid
    if client_id in connected_clients:
        print(f"[WebSocket] Client {client_id} already connected, ignoring")
        return
        
    connected_clients.add(client_id)
    print(f"[WebSocket] Client connected: {client_id}")
    safe_emit("connected", {
        "message": "Connected to WebSocket server.", 
        "timestamp": datetime.utcnow().isoformat()
    })

@socketio.on("disconnect")
def handle_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        connected_clients.remove(client_id)
    print(f"[WebSocket] Client disconnected: {client_id}")

@socketio.on("subscribe")
def handle_subscribe(data):
    """Client subscribes to updates for a specific scan job."""
    job_id = data.get("job_id")
    if not job_id:
        safe_emit("error", {"error": "Missing job_id"})
        return

    room_name = f"job_{job_id}"
    join_room(room_name)
    print(f"[WebSocket] Client {request.sid} subscribed to {room_name}")
    
    # Send initial status if available
    job = ScanJob.query.filter_by(id=job_id).first()
    if job:
        payload = {
            "job_id": str(job.id),
            "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
            "progress": job.progress,
            "target": job.target,
            "profile": job.profile,
        }
        safe_emit("scan_update", payload, room=request.sid)
    else:
        safe_emit("error", {"error": f"Job {job_id} not found"}, room=request.sid)

@socketio.on("unsubscribe")
def handle_unsubscribe(data):
    job_id = data.get("job_id")
    if not job_id:
        return safe_emit("error", {"error": "Missing job_id"})

    room_name = f"job_{job_id}"
    leave_room(room_name)
    print(f"[WebSocket] Client {request.sid} unsubscribed from {room_name}")
    safe_emit("unsubscribed", {"room": room_name, "job_id": job_id}, room=request.sid)

@socketio.on("ping")
def handle_ping():
    safe_emit("pong", {
        "message": "Still alive!", 
        "timestamp": datetime.utcnow().isoformat()
    }, room=request.sid)

# --- Background Broadcast Helper ---
def broadcast_scan_update(job_id: str):
    """
    Called by Celery workers or Flask routes to push live scan updates
    to connected clients.
    """
    try:
        job = ScanJob.query.filter_by(id=job_id).first()
        if not job:
            print(f"[WebSocket] Tried to broadcast nonexistent job {job_id}")
            return

        room_name = f"job_{job_id}"
        payload = {
            "job_id": str(job.id),
            "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
            "progress": job.progress,
            "target": job.target,
            "profile": job.profile,
        }
        safe_emit("scan_update", payload, room=room_name)
        print(f"[WebSocket] Broadcast update for {room_name}: {payload['status']} (progress: {payload['progress']}%)")
    except Exception as e:
        print(f"[WebSocket Error] broadcast_scan_update failed: {e}")