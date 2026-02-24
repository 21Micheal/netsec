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
    
    app.register_blueprint(web_bp, url_prefix='/api')
    app.register_blueprint(scans_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(advanced_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(enhanced_bp)
    app.register_blueprint(vulnerability_bp)
    
    # Import WebSocket routes AFTER blueprints are registered
    from .routes import ws_routes
    
    with app.app_context():
        db.create_all()
    
    return app