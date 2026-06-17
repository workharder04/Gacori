"""Alert management with severity levels and history."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    timestamp: float
    severity: Severity
    src_ip: str
    dst_ip: str
    protocol: str
    anomaly_score: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "protocol": self.protocol,
            "anomaly_score": round(self.anomaly_score, 4),
            "details": self.details,
        }


class AlertManager:
    def __init__(self, max_history: int = 1000, rate_limit_secs: float = 1.0):
        self._history: List[Alert] = []
        self.max_history = max_history
        self.rate_limit_secs = rate_limit_secs
        self._last_alert_time: Dict[str, float] = {}

    def _severity_from_score(self, score: float) -> Severity:
        # IsolationForest scores: more negative = more anomalous
        if score < -0.3:
            return Severity.CRITICAL
        elif score < -0.2:
            return Severity.HIGH
        elif score < -0.1:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    def process_result(self, result: Dict[str, Any]) -> Alert | None:
        if not result.get("anomaly"):
            return None

        key = f"{result['src_ip']}-{result['dst_ip']}"
        now = time.time()
        if now - self._last_alert_time.get(key, 0) < self.rate_limit_secs:
            return None
        self._last_alert_time[key] = now

        alert = Alert(
            timestamp=now,
            severity=self._severity_from_score(result["anomaly_score"]),
            src_ip=result["src_ip"],
            dst_ip=result["dst_ip"],
            protocol=result["protocol"],
            anomaly_score=result["anomaly_score"],
            details={
                "packet_count": result.get("packet_count"),
                "byte_rate": round(result.get("byte_rate", 0), 2),
                "packet_rate": round(result.get("packet_rate", 0), 2),
            },
        )
        self._history.append(alert)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
        return alert

    def get_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._history[-limit:]]

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s.value: 0 for s in Severity}
        for a in self._history:
            counts[a.severity.value] += 1
        return counts
