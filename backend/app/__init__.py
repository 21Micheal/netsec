from flask import Flask, request
from flask_cors import CORS
from redis import Redis
from rq import Queue
import os
import random, time
import json
from .utils.json_encoder import EnhancedJSONEncoder
from .extensions import db, socketio, redis_conn
from config import Config
from app.models import User
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

redis_conn = Redis.from_url(Config.REDIS_URL, decode_responses=True)
task_queue = Queue('scans', connection=redis_conn)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.url_map.strict_slashes = False 
    
    # Configure CORS
    CORS(app, 
         resources={r"/*": {
             "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True
         }}, intercept_exceptions=False
    )
    
    db.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        message_queue=Config.REDIS_URL,
        async_mode='eventlet'
    )
    
    # Import and register blueprints INSIDE create_app
    from app.routes.scans import scans_bp
    from app.routes.web_scans import web_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.advanced_scans import advanced_bp
    from app.routes.insights_routes import insights_bp 
    from app.routes.enhanced_scans import enhanced_bp
    from app.routes.vulnerability import vulnerability_bp
    from app.routes.tools import tools_bp
    from app.routes.auth import auth_bp
    from app.routes.audit import audit_bp
    from app.routes.automation import automation_bp
    
    app.register_blueprint(web_bp, url_prefix='/api')
    app.register_blueprint(scans_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(advanced_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(enhanced_bp)
    app.register_blueprint(vulnerability_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(automation_bp)
    
    # Import WebSocket routes AFTER blueprints are registered
    from .routes import ws_routes

    @app.get("/api/health")
    def healthcheck():
        return {"status": "ok", "service": "netsec-backend"}, 200
    
    with app.app_context():
        _initialize_database_with_retries()
        _ensure_runtime_schema()
        bootstrap_admin_username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "").strip().lower()
        bootstrap_admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
        if bootstrap_admin_username and bootstrap_admin_password and not User.query.filter_by(username=bootstrap_admin_username).first():
            admin = User(username=bootstrap_admin_username, role="admin", is_active=True)
            admin.set_password(bootstrap_admin_password)
            db.session.add(admin)
            db.session.commit()
    
    return app


def _initialize_database_with_retries(max_attempts: int = 12, delay_seconds: float = 1.5) -> None:
    """Wait for database connectivity before issuing schema operations."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            db.session.execute(text("SELECT 1"))
            db.create_all()
            return
        except OperationalError as exc:
            db.session.rollback()
            last_error = exc
            if attempt == max_attempts:
                raise
            print(f"Database not ready (attempt {attempt}/{max_attempts}), retrying in {delay_seconds}s...")
            time.sleep(delay_seconds)

    if last_error:
        raise last_error


def _ensure_runtime_schema() -> None:
    """Apply lightweight runtime schema fixes for environments without migrations."""
    inspector = inspect(db.engine)
    if "users" in inspector.get_table_names():
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        statements = []
        if "is_active" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;")
        if "created_at" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT NOW();")
        if "last_login_at" not in user_columns:
            statements.append("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;")

        if statements:
            with db.engine.begin() as conn:
                for statement in statements:
                    conn.execute(text(statement))
