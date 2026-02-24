from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from redis import Redis
from rq import Queue
import json
from .utils.json_encoder import EnhancedJSONEncoder

# Initialize extensions without app context
db = SQLAlchemy()
socketio = SocketIO(
    async_mode='eventlet',
    cors_allowed_origins="*",
    json=json,
    logger=True,  # Enable logging
    engineio_logger=True,  # Enable Engine.IO logging
    json_dumps=lambda obj: json.dumps(obj, cls=EnhancedJSONEncoder)
)


# Redis and Queue will be initialized in create_app
redis_conn = None
task_queue = None

def init_redis(redis_url):
    global redis_conn, task_queue
    redis_conn = Redis.from_url(redis_url, decode_responses=True)
    task_queue = Queue('scans', connection=redis_conn)
    socketio.message_queue = redis_url