import atexit
import os, subprocess, json, signal
import psycopg2
import xmltodict
import redis
import signal
from rq import get_current_job
from models import db, Scan, ScanStatus

DB_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

r = redis.Redis.from_url(REDIS_URL)

# Ensure Redis closes on exit
def cleanup_redis():
    try:
        r.close()
    except:
        pass

atexit.register(cleanup_redis)

# Also handle signals
def signal_handler(sig, frame):
    cleanup_redis()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_nmap(target):
    out_file = "/tmp/output.xml"
    cmd = ["nmap", "-sS", "-sV", "-O", "-oX", out_file, target]
    subprocess.run(cmd, check=True)
    with open(out_file) as f:
        return xmltodict.parse(f.read())


def run_scan(target, profile="fast"):
    job = get_current_job()
    scan = Scan.query.get(job.id)
    scan.status = ScanStatus.RUNNING
    db.session.commit()

    args = ["nmap", "-T4", "-F", target] if profile == "fast" else ["nmap", "-A", target]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    r.set(f"scan:{job.id}:pid", proc.pid)

    try:
        stdout, stderr = proc.communicate()
        rc = proc.returncode
    except Exception:
        # If killed mid-scan, return early
        scan.status = ScanStatus.CANCELLED
        db.session.commit()
        r.delete(f"scan:{job.id}:pid")
        return

    r.delete(f"scan:{job.id}:pid")

    # Normal finish
    scan.status = ScanStatus.FINISHED if rc == 0 else ScanStatus.FAILED
    db.session.commit()

def save_results(job_id, parsed):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    hosts = parsed["nmaprun"].get("host", [])
    if isinstance(hosts, dict):  # single host
        hosts = [hosts]

    for host in hosts:
        addr = host["address"]["@addr"] if "address" in host else None
        if not addr:
            continue
        if "ports" in host and "port" in host["ports"]:
            ports = host["ports"]["port"]
            if isinstance(ports, dict):
                ports = [ports]
            for port in ports:
                cur.execute(
                    """INSERT INTO scan_results
                       (job_id, target, port, protocol, service, version, raw_output)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        job_id,
                        addr,
                        int(port["@portid"]),
                        port["@protocol"],
                        port["service"]["@name"] if "service" in port else "",
                        port["service"].get("@version", "") if "service" in port else "",
                        json.dumps(port),
                    ),
                )
    cur.execute("UPDATE scan_jobs SET status='finished', finished_at=now() WHERE id=%s", (job_id,))
    conn.commit()
    cur.close()
    conn.close()

def worker_loop():
    print("Worker listening for jobs...")
    while True:
        _, job_data = r.brpop("scan_jobs")
        job = json.loads(job_data)
        print(f"Picked job {job['id']} for target {job['target']}")
        try:
            parsed = run_nmap(job["target"])
            save_results(job["id"], parsed)
            print(f"Job {job['id']} finished")
        except Exception as e:
            print(f"Error on job {job['id']}: {e}")
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("UPDATE scan_jobs SET status='failed' WHERE id=%s", (job["id"],))
            conn.commit()
            cur.close()
            conn.close()

if __name__ == "__main__":
    worker_loop()
