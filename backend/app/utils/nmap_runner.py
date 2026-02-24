# app/utils/nmap_runner.py
import subprocess
import shutil
import time
import xmltodict
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional imports (import at runtime to avoid hard dependency)
try:
    import nmap  # python-nmap (PortScanner)
except Exception:
    nmap = None

# Import socketio lazily to avoid circular imports when module loaded in different contexts
def _get_socketio():
    try:
        # app package should expose socketio at app.socketio or similar
        from app import socketio
        return socketio
    except Exception:
        return None


def _emit_log(job_id: Optional[str], line: str):
    """Emit a log line via socketio to room job_{job_id} if socketio is available."""
    if not job_id:
        return
    socketio = _get_socketio()
    if not socketio:
        return
    try:
        room = f"job_{job_id}"
        socketio.emit("scan_log", {"job_id": str(job_id), "log_line": line}, room=room)
    except Exception:
        # Never fail because of logging
        pass


def run_nmap_scan(target: str, args: Optional[List[str]] = None,
                  job_id: Optional[str] = None, timeout: int = 600) -> Dict[str, Any]:
    """
    Primary helper to run an nmap scan.
    Tries python-nmap PortScanner first (if installed), then falls back to running 'nmap' binary with -oX -.

    Parameters:
    - target: host or domain to scan (string)
    - args: list of additional nmap arguments, e.g. ["-sV", "-p", "1-1024"]
    - job_id: optional job UUID used for emitting socket logs
    - timeout: overall timeout in seconds for the scan subprocess (fallback)

    Returns:
    - A dictionary with the parsed nmap output. The exact schema:
      - If python-nmap used: return of PortScanner.get_nmap_last_output() isn't available; instead return structured data via PortScanner object converted sensibly.
      - If fallback used: parsed xml->dict output via xmltodict (matching nmap XML schema).
    Raises:
    - RuntimeError for fatal errors (binary missing, parse failure)
    """

    args = args or []

    # 1) Try python-nmap (PortScanner) if available
    if nmap is not None:
        try:
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] Using python-nmap PortScanner")
            pc = nmap.PortScanner()
            # portscanner expects a string target and options as a single string
            opts = " ".join(args)
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] Running nmap via python-nmap: {opts} {target}")
            # Run synchronously; python-nmap will call the binary internally if available
            pc.scan(targets=target, arguments=opts)
            # Convert PortScanner object into dict (safe, best-effort)
            out = {
                "nmap_version": getattr(pc, "nmap_version", None),
                "scaninfo": pc.scaninfo(),
                "scan": {},
            }
            for host in pc.all_hosts():
                out["scan"][host] = {
                    "hostname": pc[host].hostname(),
                    "state": pc[host].state(),
                    "protocols": {},
                }
                for proto in pc[host].all_protocols():
                    out["scan"][host]["protocols"][proto] = []
                    for port in pc[host][proto].keys():
                        portinfo = pc[host][proto][port]
                        out["scan"][host]["protocols"][proto].append({
                            "port": port,
                            "state": portinfo.get("state"),
                            "name": portinfo.get("name"),
                            "product": portinfo.get("product"),
                            "version": portinfo.get("version"),
                            "extrainfo": portinfo.get("extrainfo"),
                            "conf": portinfo.get("conf"),
                            "cpe": portinfo.get("cpe"),
                        })
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] python-nmap scan complete")
            return out
        except Exception as e:
            # Fall through to subprocess fallback but include a helpful log
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] python-nmap failed: {e}; falling back to subprocess")
            # continue to fallback

    # 2) Fallback: ensure nmap binary exists
    nmap_path = shutil.which("nmap")
    if not nmap_path:
        _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] nmap binary not found in PATH")
        raise RuntimeError("nmap binary not found and python-nmap not usable")

    # Build command: nmap -oX - <args> <target>
    cmd = [nmap_path, "-oX", "-"] + args + [target]
    _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] Running nmap subprocess: {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output lines, emit logs and collect XML
        xml_chunks: List[str] = []
        start = time.time()
        while True:
            line = proc.stdout.readline()
            if line == "" and proc.poll() is not None:
                break
            if line:
                xml_chunks.append(line)
                # emit line to websocket logs
                _emit_log(job_id, line.rstrip("\n"))
            # Timeout safety
            if timeout and (time.time() - start) > timeout:
                proc.kill()
                raise RuntimeError("nmap subprocess timed out")

        rc = proc.wait()
        xml_text = "".join(xml_chunks)

        if rc != 0 and not xml_text.strip():
            raise RuntimeError(f"nmap subprocess failed with return code {rc}")

        # Parse XML output into python dict using xmltodict
        try:
            parsed = xmltodict.parse(xml_text)
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] nmap XML parsed successfully")
            # return the raw parsed dict (matches nmap XML schema)
            return parsed
        except Exception as e:
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] xmltodict parse failed: {e}")
            # If xml parsing fails, provide original output in a fallback structure
            return {"raw_output": xml_text, "error": f"xml parse failed: {e}"}

    except Exception as e:
        _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] nmap subprocess error: {e}")
        raise


def run_nmap_scan_fallback(target: str, args: Optional[List[str]] = None,
                           job_id: Optional[str] = None, timeout: int = 600) -> Dict[str, Any]:
    """
    Explicit fallback runner: runs the nmap binary via subprocess and returns XML parsed to dict.
    Equivalent to the fallback portion of run_nmap_scan but exposed separately.
    """
    args = args or []
    nmap_path = shutil.which("nmap")
    if not nmap_path:
        _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] nmap binary not found for fallback")
        raise RuntimeError("nmap binary not found")

    cmd = [nmap_path, "-oX", "-"] + args + [target]
    _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] fallback: running {' '.join(cmd)}")

    try:
        out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        xml_text = out.stdout
        try:
            parsed = xmltodict.parse(xml_text)
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] fallback: xml parsed ok")
            return parsed
        except Exception as e:
            _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] fallback: xml parse failed: {e}")
            return {"raw_output": xml_text, "error": f"xml parse failed: {e}"}
    except subprocess.TimeoutExpired:
        _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] fallback: nmap timed out")
        raise
    except Exception as e:
        _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] fallback: nmap error: {e}")
        raise


def run_nmap_scan_original(target: str, args: Optional[List[str]] = None,
                           job_id: Optional[str] = None, timeout: int = 600) -> Dict[str, Any]:
    """
    Legacy/original runner that returns a best-effort parse using grepable output (-oG -).
    Useful when XML parsing is not desired or for very quick summaries.

    Returns structure:
    {
      "hosts": [
         {"host": "1.2.3.4", "status": "up", "ports": [{"port":80,"state":"open","service":"http"}, ...]}
      ],
      "raw": "<original text>"
    }
    """
    args = args or []
    nmap_path = shutil.which("nmap")
    if not nmap_path:
        _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] original: nmap binary not found")
        raise RuntimeError("nmap binary not found")

    cmd = [nmap_path, "-oG", "-"] + args + [target]
    _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] original: running {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        raw_lines = []
        hosts = []
        for line in proc.stdout:
            raw_lines.append(line)
            _emit_log(job_id, line.rstrip("\n"))

            line = line.strip()
            # parse host lines like:
            # Host: 127.0.0.1 ()  Status: Up
            # Ports: 22/open/tcp//ssh///
            if line.startswith("Host:"):
                parts = line.split()
                # Host: <ip> (<dns>)  Status: Up
                try:
                    ip = parts[1]
                    status = "unknown"
                    if "Status:" in parts:
                        status_index = parts.index("Status:")
                        status = parts[status_index + 1]
                    hosts.append({"host": ip, "status": status, "ports": []})
                except Exception:
                    pass
            elif line.startswith("Ports:") or "Ports:" in line:
                # Some lines contain ports after Hosts entries; try to parse
                # Example Ports line: "Ports: 80/open/tcp//http///, 22/open/tcp//ssh///"
                try:
                    # naive parse: find last host and attach ports
                    if not hosts:
                        continue
                    ports_part = line.split("Ports:")[-1].strip()
                    port_entries = [p.strip() for p in ports_part.split(",") if p.strip()]
                    for pentry in port_entries:
                        # pentry example: "80/open/tcp//http///"
                        parts = pentry.split("/")
                        portnum = int(parts[0]) if parts and parts[0].isdigit() else None
                        state = parts[1] if len(parts) > 1 else None
                        proto = parts[2] if len(parts) > 2 else None
                        service = parts[4] if len(parts) > 4 else None
                        hosts[-1]["ports"].append({
                            "port": portnum,
                            "state": state,
                            "proto": proto,
                            "service": service
                        })
                except Exception:
                    # Continue; best-effort parsing
                    pass

        proc.wait()
        raw = "".join(raw_lines)
        return {"hosts": hosts, "raw": raw}
    except Exception as e:
        _emit_log(job_id, f"[{datetime.utcnow().isoformat()}] original runner error: {e}")
        raise


def run_nmap_scan_threaded(target: str, ports: Optional[list[int]] = None,
                           job_id: Optional[str] = None,
                           max_workers: int = 100, timeout: float = 0.5):
    """
    Fast threaded TCP port sweep (non-nmap).
    Quickly checks which ports are open before running a full nmap scan.
    """
    _emit_log(job_id, f"[ThreadedScan] Starting quick TCP sweep on {target}")
    open_ports = []
    ports = ports or list(range(1, 1025))  # Default: top 1024 ports

    def scan_port(port):
        try:
            with socket.create_connection((target, port), timeout=timeout):
                return port
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_port, p): p for p in ports}
        for fut in as_completed(futures):
            port = fut.result()
            if port:
                open_ports.append(port)
                _emit_log(job_id, f"[ThreadedScan] Port {port} is open")

    _emit_log(job_id, f"[ThreadedScan] Finished sweep, found {len(open_ports)} open ports.")
    return {"open_ports": open_ports, "target": target, "method": "threaded_tcp"}