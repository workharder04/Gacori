"""Anomaly detection: IsolationForest + Z-score ensemble."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    def __init__(self, contamination: float = 0.1, zscore_threshold: float = 3.0):
        self.contamination = contamination
        self.zscore_threshold = zscore_threshold
        self.iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        self.scaler = StandardScaler()
        self._trained = False

    def fit(self, X: np.ndarray) -> None:
        X_scaled = self.scaler.fit_transform(X)
        self.iso_forest.fit(X_scaled)
        self._trained = True

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Returns (labels, scores). Label -1 = anomaly, 1 = normal."""
        if not self._trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        X_scaled = self.scaler.transform(X)

        iso_labels = self.iso_forest.predict(X_scaled)
        iso_scores = self.iso_forest.score_samples(X_scaled)

        # Z-score per feature, flag row if any feature is an outlier
        z_scores = np.abs((X_scaled - 0) / 1)  # already standardised
        zscore_flag = (z_scores > self.zscore_threshold).any(axis=1)

        # Ensemble: anomaly if either method flags it
        ensemble_labels = np.where((iso_labels == -1) | zscore_flag, -1, 1)
        return ensemble_labels, iso_scores

    def predict_flows(
        self, flows: List[Dict[str, Any]], X: np.ndarray
    ) -> List[Dict[str, Any]]:
        labels, scores = self.predict(X)
        results = []
        for flow, label, score in zip(flows, labels, scores):
            results.append({
                **flow,
                "anomaly": label == -1,
                "anomaly_score": float(score),
            })
        return results

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({"iso": self.iso_forest, "scaler": self.scaler,
                         "contamination": self.contamination,
                         "zscore_threshold": self.zscore_threshold}, f)

    @classmethod
    def load(cls, path: str) -> "AnomalyDetector":
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(contamination=data["contamination"],
                  zscore_threshold=data["zscore_threshold"])
        obj.iso_forest = data["iso"]
        obj.scaler = data["scaler"]
        obj._trained = True
        return obj
