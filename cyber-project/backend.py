from flask import Flask, jsonify, request
from datetime import datetime
import random, threading

app = Flask(__name__)
LOG = []  # in-memory log only


def now_ts():
    return datetime.utcnow().isoformat() + "Z"


@app.route("/api/log", methods=["GET"])
def get_log():
    return jsonify({"rows": LOG[-500:]})


@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.json or {}
    dst = int(data.get("dst_port", random.choice([22, 80, 2222])))
    row = {
        "timestamp": now_ts(),
        "src_ip": f"192.168.1.{random.randint(2,250)}",
        "src_port": random.randint(1024, 65535),
        "dst_port": dst,
        "recv_preview": "SIM_ATTACK_PAYLOAD",
    }
    LOG.append(row)  # <- fixed indent, no extra spaces
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(port=5000)
