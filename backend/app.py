# import os, json
# from flask import Flask, request, jsonify, send_from_directory
# import psycopg2
# import redis, os, signal
# import uuid
# from flask_cors import CORS
# from models import db, ScanStatus, ScanJob as Scan, ScanResult

# from worker import queue_scan  # assuming this enqueues jobs

# DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres")
# REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# app = Flask(__name__)
# r = redis.Redis.from_url(REDIS_URL)
# CORS(app)

# def get_db():
#     return psycopg2.connect(DB_URL)

# # @app.route("/api/scans", methods=["POST"])
# # def create_scan():
# #     data = request.get_json()
# #     target = data.get("target")
# #     profile = data.get("profile", "fast")
# #     parent_scan_id = data.get("parentScanId")

# #     if not target:
# #         return jsonify({"error": "Target is required"}), 400

# #     scan = Scan(
# #         target=target,
# #         profile=profile,
# #         status="pending",
# #         parent_scan_id=parent_scan_id,  # ✅ link to original scan
# #     )
# #     db.session.add(scan)
# #     db.session.commit()

# #     # enqueue job in Redis
# #     queue_scan(scan.id, target, profile)

# #     return jsonify({
# #         "id": scan.id,
# #         "target": scan.target,
# #         "profile": scan.profile,
# #         "status": scan.status,
# #         "parentScanId": scan.parent_scan_id,
# #         "createdAt": scan.created_at
# #     }), 201

# # # app.py
# # @app.route("/api/scans", methods=["GET"])
# # def list_scans():
# #     scans = Scan.query.order_by(Scan.created_at.desc()).all()

# #     def serialize(scan):
# #         return {
# #             "id": scan.id,
# #             "target": scan.target,
# #             "profile": scan.profile,
# #             "status": scan.status,
# #             "createdAt": scan.created_at,
# #             "finishedAt": scan.finished_at,
# #             "parentScanId": scan.parent_scan_id,
# #             "retries": [serialize(r) for r in scan.retries]  # ✅ nested
# #         }

# #     top_level = [s for s in scans if not s.parent_scan_id]
# #     return jsonify([serialize(s) for s in top_level])


# # @app.route("/api/scans/<job_id>/results", methods=["GET"])
# # def get_results(job_id):
# #     conn = get_db()
# #     cur = conn.cursor()
# #     cur.execute(
# #         "SELECT port, protocol, service, version FROM scan_results WHERE job_id = %s",
# #         (job_id,),
# #     )
# #     rows = cur.fetchall()
# #     cur.close()
# #     conn.close()

# #     results = [
# #         {"port": row[0], "protocol": row[1], "service": row[2], "version": row[3]}
# #         for row in rows
# #     ]
# #     return jsonify(results)

# # @app.route("/api/scans/<scan_id>/cancel", methods=["POST"])
# # def cancel_scan(scan_id):
# #     pid_key = f"scan:{scan_id}:pid"
# #     pid = r.get(pid_key)

# #     scan = Scan.query.get(scan_id)
# #     if not scan:
# #         return jsonify({"error": "Scan not found"}), 404

# #     if not pid:
# #         # already finished or never started
# #         scan.status = ScanStatus.CANCELLED
# #         db.session.commit()
# #         return jsonify({"status": "cancelled", "id": scan_id})

# #     pid = int(pid)

# #     try:
# #         os.kill(pid, signal.SIGTERM)
# #         r.delete(pid_key)
# #         scan.status = ScanStatus.CANCELLED
# #         db.session.commit()
# #         return jsonify({"status": "cancelled", "id": scan_id})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 500
    


# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def catch_all(path):
#     return send_from_directory('frontend-build', 'index.html')

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)
