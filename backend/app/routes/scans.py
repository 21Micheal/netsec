from flask import Blueprint, request, jsonify
from app.extensions import db, socketio
from app.models import ScanJob, JobStatus, ScanResult, WebScanResult, ScanType

import uuid, time
from datetime import datetime
import re

scans_bp = Blueprint('scans', __name__, url_prefix='/api/scans')

# Don't import tasks at module level - import inside functions when needed

@scans_bp.route("/", methods=["GET"])
def get_all_scans():
    try:
        # Get network scans
        jobs = ScanJob.query.order_by(ScanJob.created_at.desc()).all()
        # Get web scans
        web_results = WebScanResult.query.order_by(WebScanResult.created_at.desc()).all()

        scans = []
        processed_jobs = set()  # Track jobs we've already processed

        # Process network scans first
        for job in jobs:
            scan_data = {
                "id": str(job.id),
                "target": job.target,
                "profile": job.profile,
                "status": job.status.value if job.status else "unknown",
                "progress": job.progress,
                "createdAt": job.created_at.isoformat() if job.created_at else None,
                "finishedAt": job.finished_at.isoformat() if job.finished_at else None,
                "type": "network",
            }
            scans.append(scan_data)
            processed_jobs.add(job.id)

        # Add web scans - only if not already included as network scans
        for web_scan in web_results:
            # If this web scan already has a job entry, enhance it with web-specific data
            if web_scan.job_id in processed_jobs:
                # Find and update the existing job with web scan details
                for scan in scans:
                    if scan["id"] == str(web_scan.job_id):
                        scan.update({
                            "type": "web",  # Change type to web since we have web results
                            "http_status": web_scan.http_status,
                            "issues": web_scan.issues or [],
                            "web_scan_id": str(web_scan.id)  # Add web scan ID for reference
                        })
                        break
            else:
                # Create new entry for orphaned web scans (shouldn't happen normally)
                scans.append({
                    "id": str(web_scan.id),
                    "target": web_scan.url,
                    "profile": "web",
                    "status": "finished",
                    "progress": 100,
                    "createdAt": web_scan.created_at.isoformat() if web_scan.created_at else None,
                    "finishedAt": web_scan.created_at.isoformat() if web_scan.created_at else None,
                    "type": "web",
                    "http_status": web_scan.http_status,
                    "issues": web_scan.issues or [],
                    "web_scan_id": str(web_scan.id)
                })

        # Sort by newest first
        scans.sort(key=lambda s: s["createdAt"] or "", reverse=True)

        # DEBUG: Log the final scan list
        print(f"📊 Returning {len(scans)} scans:")
        for scan in scans:
            print(f"  - {scan['id']}: {scan['target']} ({scan['type']}) - {scan['status']}")

        return jsonify(scans)
        
    except Exception as e:
        print(f"❌ Error fetching scans: {e}")
        return jsonify({"error": str(e)}), 500


@scans_bp.route("/combined", methods=["POST", "OPTIONS"])
def combined_scan():
    """✅ FIXED: Consistent job_id return with proper status code"""
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        data = request.get_json()
        target = data.get("target")
        profile = data.get("profile", "default")

        if not target:
            return jsonify({"error": "Target is required"}), 400

        # Auto-detect if target is a web domain (not IP address)
        if profile == "default" and is_web_domain(target):
            profile = "web"
            print(f"🌐 Auto-detected web target: {target}")

        # Create Job entry
        job_id = str(uuid.uuid4())
        new_job = ScanJob(
            id=job_id,
            target=target,
            profile=profile,
            status=JobStatus.queued,
            progress=0  # Explicitly set to 0
        )
        db.session.add(new_job)
        db.session.commit()

        print(f"✅ Created scan job {job_id} for target: {target} (profile: {profile})")

        # Broadcast initial state
        from app.routes.ws_routes import broadcast_scan_update
        broadcast_scan_update(job_id)

        # Enqueue the appropriate task using apply_async instead of delay
        if profile == "web":
            from app.workers.tasks import enqueue_web_scan
            enqueue_web_scan.apply_async(args=[job_id, target, profile])
            print(f"🌐 Queued web scan task for job {job_id}")
        else:
            from app.workers.tasks import enqueue_scan_job
            enqueue_scan_job.apply_async(args=[job_id, target, profile])
            print(f"🔧 Queued network scan task for job {job_id}")

        # ✅ CRITICAL: Return consistent response with 201 status
        return jsonify({
            "success": True,  # Add success field
            "job_id": job_id,
            "target": target,
            "profile": profile,
            "message": f"Scan for {target} has been queued.",
            "auto_detected_profile": profile
        }), 201  # Changed from 200 to 201
        
    except Exception as e:
        print(f"❌ Error creating scan: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@scans_bp.route('/scan-jobs', methods=['POST'])
def create_scan_job():
    """✅ FIXED: Consistent job_id return with proper status code"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({'error': 'Target is required'}), 400

        job_id = str(uuid.uuid4())
        job = ScanJob(
            id=job_id,
            target=data['target'],
            profile=data.get('profile', 'default'),
            status=JobStatus.queued,
            progress=0
        )
        
        db.session.add(job)
        db.session.commit()

        print(f"✅ Created scan job {job_id} for target: {data['target']}")

        # Broadcast initial state
        from app.routes.ws_routes import broadcast_scan_update
        broadcast_scan_update(job_id)

        # Queue the task using apply_async
        from app.workers.tasks import enqueue_scan_job
        enqueue_scan_job.apply_async(args=[job_id, job.target, job.profile])

        # ✅ CRITICAL: Return consistent response
        return jsonify({
            'success': True,
            'job_id': job_id,  # Primary key
            'id': job_id,  # Keep for backward compatibility
            'target': job.target,
            'profile': job.profile,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'finished_at': job.finished_at,
            'message': f'Scan job for {job.target} has been queued.'
        }), 201
        
    except Exception as e:
        print(f"❌ Error creating scan job: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# Helper function
def is_web_domain(target: str) -> bool:
    """Check if target is a web domain (not an IP address)"""
    try:
        # Check if it's a URL
        if target.startswith('http://') or target.startswith('https://'):
            return True
        
        # Check if it's an IP address
        import ipaddress
        target_clean = target.split(':')[0]  # Remove port if present
        ipaddress.ip_address(target_clean)
        return False  # It's an IP, not a domain
    except ValueError:
        # Not an IP address, probably a domain
        return True

@scans_bp.route('/scan-jobs/<job_id>', methods=['GET'])
def get_scan_job(job_id):
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify({
            'id': str(job.id),
            'target': job.target,
            'profile': job.profile,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'finished_at': job.finished_at.isoformat() if job.finished_at else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scans_bp.route('/scan-jobs/<job_id>/results', methods=['GET'])
def get_scan_results(job_id):
    try:
        job = ScanJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        results = [{
            'id': result.id,
            'job_id': str(result.job_id),
            'target': result.target,
            'port': result.port,
            'protocol': result.protocol,
            'service': result.service,
            'version': result.version,
            'discovered_at': result.discovered_at.isoformat() if result.discovered_at else None
        } for result in job.results]

        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@scans_bp.route('/scan-jobs/<job_id>/retry', methods=['POST'])
def retry_scan(job_id):
    try:
        original = ScanJob.query.get(job_id)
        if not original:
            return jsonify({'error': 'Scan job not found'}), 404

        # Create a new scan job with the same parameters
        retry_job = ScanJob(
            id=uuid.uuid4(),
            target=original.target,
            profile=original.profile,
            status=JobStatus.queued,
            parent_scan_id=original.id
        )
        
        db.session.add(retry_job)
        db.session.commit()

        # Use broadcast function
        from app.routes.ws_routes import broadcast_scan_update
        broadcast_scan_update(str(retry_job.id))

        # Queue the task
        from app.workers.tasks import enqueue_scan_job
        enqueue_scan_job.delay(str(retry_job.id), retry_job.target, retry_job.profile)

        return jsonify({
            'id': str(retry_job.id),
            'target': retry_job.target,
            'profile': retry_job.profile,
            'status': retry_job.status.value,
            'progress': retry_job.progress,
            'created_at': retry_job.created_at.isoformat(),
            'finished_at': retry_job.finished_at
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@scans_bp.route('/web-scan-jobs', methods=['POST'])
def create_web_scan_job():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400

        job = ScanJob(
            id=uuid.uuid4(),
            target=data['url'],
            profile=data.get('profile', 'web'),
            status=JobStatus.queued
        )
        
        db.session.add(job)
        db.session.commit()

        # Use broadcast function
        from app.routes.ws_routes import broadcast_scan_update
        broadcast_scan_update(str(job.id))

        # Queue the web scan task
        from app.workers.tasks import enqueue_web_scan
        enqueue_web_scan.delay(str(job.id), job.target, job.profile)

        return jsonify({
            'id': str(job.id),
            'target': job.target,
            'profile': job.profile,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'finished_at': job.finished_at
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    

