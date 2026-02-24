from flask import Blueprint, jsonify
from app.models import ScanJob, JobStatus
from app import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Get counts by status
        status_counts = db.session.query(
            ScanJob.status,
            func.count(ScanJob.id)
        ).group_by(ScanJob.status).all()
        
        # Convert to dictionary
        counts_dict = {status.value: count for status, count in status_counts}
        
        stats = {
            'activeScans': counts_dict.get('running', 0),
            'completedJobs': counts_dict.get('finished', 0),
            'alerts': counts_dict.get('failed', 0),
            'totalScans': sum(counts_dict.values()),
            'queuedScans': counts_dict.get('queued', 0),
        }
        
        # Calculate system load based on active scans
        system_load = min(100, stats['activeScans'] * 15)
        stats['systemLoad'] = system_load
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/recent-scans', methods=['GET'])
def get_recent_scans():
    """Get recent scans for dashboard"""
    try:
        scans = ScanJob.query.order_by(ScanJob.created_at.desc()).limit(10).all()
        
        return jsonify([{
            'id': str(scan.id),
            'target': scan.target,
            'profile': scan.profile,
            'status': scan.status.value,
            'progress': scan.progress,
            'createdAt': scan.created_at.isoformat(),
            'finishedAt': scan.finished_at.isoformat() if scan.finished_at else None,
            'duration': scan.duration,
            'type': 'web' if scan.profile == 'web' else 'network'
        } for scan in scans])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500