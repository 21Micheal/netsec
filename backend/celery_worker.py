#!/usr/bin/env python
import os
import signal
import atexit
import eventlet
eventlet.monkey_patch()

from app.workers.tasks import cel, app

def cleanup():
    print("🛑 Shutting down Celery worker...")
    try:
        cel.connection().close()
    except:
        pass

atexit.register(cleanup)

def signal_handler(sig, frame):
    cleanup()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    argv = [
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--pool=eventlet',
        '--include=app.workers.tasks'
    ]
    
    print("🔧 Registering Celery tasks...")
    cel.worker_main(argv=argv)