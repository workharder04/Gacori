"""Flask web dashboard for real-time anomaly monitoring."""
from __future__ import annotations

import time
import threading
import random
from typing import List, Dict, Any

from flask import Flask, jsonify, render_template

from detector.capture import PacketCapture
from detector.features import FeatureExtractor
from detector.model import AnomalyDetector
from detector.alerts import AlertManager

app = Flask(__name__)

_state: Dict[str, Any] = {
    "total_packets": 0,
    "total_anomalies": 0,
    "anomaly_timeline": [],  # [{time, score}]
    "top_talkers": {},
    "recent_flows": [],
}
_alert_mgr = AlertManager()
_lock = threading.Lock()


def _background_worker():
    capture = PacketCapture(mock=True)
    extractor = FeatureExtractor()
    model = AnomalyDetector()
    trained = False

    while True:
        records = capture.capture(count=50)
        with _lock:
            _state["total_packets"] += len(records)
            for r in records:
                _state["top_talkers"][r.src_ip] = (
                    _state["top_talkers"].get(r.src_ip, 0) + 1
                )

        flows = extractor.extract_flows(records)
        if not flows:
            time.sleep(1)
            continue

        X = extractor.to_matrix(flows)

        # Inject anomalies for demo variety
        anomaly_rows = X[:2].copy()
        anomaly_rows[:, 6] *= 50  # spike packet_rate
        import numpy as np
        X_train = np.vstack([X, anomaly_rows])

        if not trained:
            model.fit(X_train)
            trained = True

        results = model.predict_flows(flows, X)

        with _lock:
            for r in results:
                if r["anomaly"]:
                    _state["total_anomalies"] += 1
                    alert = _alert_mgr.process_result(r)
                _state["anomaly_timeline"].append({
                    "time": time.strftime("%H:%M:%S"),
                    "score": round(r["anomaly_score"], 4),
                    "anomaly": r["anomaly"],
                })
                if len(_state["anomaly_timeline"]) > 60:
                    _state["anomaly_timeline"] = _state["anomaly_timeline"][-60:]

            _state["recent_flows"] = results[-20:]

        time.sleep(5)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def stats():
    with _lock:
        top = sorted(_state["top_talkers"].items(), key=lambda x: -x[1])[:5]
        return jsonify({
            "total_packets": _state["total_packets"],
            "total_anomalies": _state["total_anomalies"],
            "anomaly_rate": round(
                _state["total_anomalies"] / max(_state["total_packets"], 1) * 100, 2
            ),
            "top_talkers": [{"ip": ip, "count": c} for ip, c in top],
        })


@app.route("/api/timeline")
def timeline():
    with _lock:
        return jsonify(_state["anomaly_timeline"])


@app.route("/api/alerts")
def alerts():
    return jsonify(_alert_mgr.get_alerts(50))


@app.route("/api/alert_summary")
def alert_summary():
    return jsonify(_alert_mgr.summary())


def run(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    t = threading.Thread(target=_background_worker, daemon=True)
    t.start()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run()
