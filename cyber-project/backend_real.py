# backend_real.py
# Real honeypot backend with CORS + Private Network Access headers (for local dev)
# Usage: python backend_real.py
# NOTE: For demo/lab only. Do NOT expose this to the public internet.

from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from datetime import datetime
import socket, threading, csv, os, time

# ---------- CONFIG ----------
CSV_FILE = "attempts.csv"
LOG_LOCK = threading.Lock()
LOG = []
PORTS = [2222, 8080, 50022]  # default listen ports (change if needed)
BANNER_MAP = {
    2222: "SSH-2.0-OpenSSH_7.9p1 Fake\r\n",
    8080: "HTTP/1.1 200 OK\r\nServer: tiny-demo\r\n\r\n",
    50022: "FakeService v0.1\r\n",
}
RECV_PREVIEW_MAX = 300
# ----------------------------

app = Flask(__name__)
# allow only the frontend origin (safer than '*')
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})


# Force CORS + Private Network Access headers (fallback; safe for local dev)
@app.after_request
def _add_cors_headers(response):
    # allow frontend origin
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    # Critical for Chrome Private Network Access when origin != loopback
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


# Respond to preflight OPTIONS for any /api/* route
@app.route("/api/<path:anypath>", methods=["OPTIONS"])
def _handle_options(anypath):
    resp = make_response(("", 200))
    resp.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Private-Network"] = "true"
    return resp


# ---------- helpers ----------
def now_ts():
    return datetime.utcnow().isoformat() + "Z"


def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "timestamp",
                    "src_ip",
                    "src_port",
                    "dst_port",
                    "recv_preview",
                    "banner_sent",
                ]
            )


def append_csv_row(row):
    ensure_csv()
    with LOG_LOCK:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    row["timestamp"],
                    row["src_ip"],
                    row["src_port"],
                    row["dst_port"],
                    row["recv_preview"],
                    row["banner_sent"],
                ]
            )
        LOG.append(row)
        if len(LOG) > 5000:
            LOG.pop(0)


# ---------- honeypot listener logic ----------
_LISTENERS = {}  # port -> {"thread", "stop"}
_LISTEN_ENABLED = True


def handle_connection(client_sock, addr, dst_port):
    client_sock.settimeout(2.0)
    src_ip, src_port = addr[0], addr[1]
    recv_preview = ""
    banner_sent = BANNER_MAP.get(dst_port, "Welcome\r\n")
    try:
        data = client_sock.recv(4096)
        if data:
            try:
                recv_preview = (
                    data[:RECV_PREVIEW_MAX]
                    .decode(errors="replace")
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                )
            except Exception:
                recv_preview = "<binary>"
    except Exception:
        pass

    try:
        client_sock.sendall(banner_sent.encode())
    except Exception:
        pass
    try:
        client_sock.close()
    except Exception:
        pass

    row = {
        "timestamp": now_ts(),
        "src_ip": src_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "recv_preview": recv_preview,
        "banner_sent": banner_sent.replace("\n", "\\n"),
    }
    append_csv_row(row)
    print(
        f"{row['timestamp']}  {src_ip}:{src_port} -> {dst_port}  recv='{recv_preview[:80]}'"
    )


def serve_port(port, stop_event):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", port))
        s.listen(50)
    except Exception as e:
        print(f"[!] failed to bind port {port}: {e}")
        return
    print(f"[+] listening on 0.0.0.0:{port}")
    s.settimeout(1.0)
    while not stop_event.is_set():
        try:
            client, addr = s.accept()
            t = threading.Thread(
                target=handle_connection, args=(client, addr, port), daemon=True
            )
            t.start()
        except socket.timeout:
            continue
        except Exception as e:
            print("listener error:", e)
            break
    try:
        s.close()
    except:
        pass
    print(f"[+] stopped listener on port {port}")


def ensure_listening_started():
    for p in PORTS:
        if p in _LISTENERS:
            continue
        stop_ev = threading.Event()
        t = threading.Thread(target=serve_port, args=(p, stop_ev), daemon=True)
        _LISTENERS[p] = {"thread": t, "stop": stop_ev}
        t.start()


def stop_listeners():
    global _LISTENERS, _LISTEN_ENABLED
    for p, info in list(_LISTENERS.items()):
        info["stop"].set()
    _LISTENERS.clear()
    _LISTEN_ENABLED = False


# ---------- Flask API ----------
@app.route("/api/log", methods=["GET"])
def api_log():
    with LOG_LOCK:
        rows = LOG[-500:]
    return jsonify({"rows": rows})


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.json or {}
    dst = int(data.get("dst_port", PORTS[0] if PORTS else 2222))
    row = {
        "timestamp": now_ts(),
        "src_ip": f"192.168.1.{int(time.time())%250 + 2}",
        "src_port": 40000 + (int(time.time()) % 25000),
        "dst_port": dst,
        "recv_preview": "SIM_ATTACK_PAYLOAD",
        "banner_sent": BANNER_MAP.get(dst, "Welcome").replace("\n", "\\n"),
    }
    append_csv_row(row)
    return jsonify({"ok": True})


@app.route("/api/listen", methods=["POST"])
def api_listen():
    global _LISTEN_ENABLED
    data = request.json or {}
    listen = bool(data.get("listen", True))
    if listen:
        if not _LISTEN_ENABLED:
            _LISTEN_ENABLED = True
            ensure_listening_started()
    else:
        if _LISTEN_ENABLED:
            _LISTEN_ENABLED = False
            stop_listeners()
    return jsonify({"ok": True, "listen": _LISTEN_ENABLED})


@app.route("/api/config", methods=["GET"])
def api_config():
    return jsonify({"ports": PORTS, "listening": _LISTEN_ENABLED})


@app.route("/api/download", methods=["GET"])
def api_download():
    if not os.path.exists(CSV_FILE):
        return jsonify({"ok": False, "error": "no file"}), 404
    try:
        return send_file(
            CSV_FILE,
            mimetype="text/csv",
            as_attachment=True,
            download_name="attempts.csv",
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------- startup ----------
if __name__ == "__main__":
    print("[*] backend_real starting...")
    ensure_csv()
    ensure_listening_started()

    # rotate CSV if large
    def csv_maintenance():
        while True:
            try:
                if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 5_000_000:
                    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                    os.rename(CSV_FILE, CSV_FILE + "." + ts)
                    ensure_csv()
            except Exception:
                pass
            time.sleep(60)

    t = threading.Thread(target=csv_maintenance, daemon=True)
    t.start()

    app.run(port=5000, debug=False, host="0.0.0.0")
