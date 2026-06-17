"""Aggregate raw packets into flow-level feature vectors."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Any

import numpy as np

from .capture import PacketRecord


class FeatureExtractor:
    """Groups packets by (src_ip, dst_ip, dst_port, protocol) flows."""

    FEATURE_NAMES = [
        "packet_count",
        "mean_packet_size",
        "std_packet_size",
        "max_packet_size",
        "min_packet_size",
        "flow_duration",
        "packet_rate",
        "byte_rate",
        "unique_src_ports",
    ]

    def extract_flows(self, records: List[PacketRecord]) -> List[Dict[str, Any]]:
        flows: Dict[tuple, List[PacketRecord]] = defaultdict(list)

        for r in records:
            key = (r.src_ip, r.dst_ip, r.dst_port, r.protocol)
            flows[key].append(r)

        feature_rows = []
        for (src_ip, dst_ip, dst_port, protocol), pkts in flows.items():
            sizes = [p.packet_size for p in pkts]
            times = [p.timestamp for p in pkts]
            duration = max(times) - min(times) if len(times) > 1 else 0.001
            pkt_rate = len(pkts) / duration
            byte_rate = sum(sizes) / duration

            feature_rows.append({
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "dst_port": dst_port,
                "protocol": protocol,
                "packet_count": len(pkts),
                "mean_packet_size": float(np.mean(sizes)),
                "std_packet_size": float(np.std(sizes)),
                "max_packet_size": float(np.max(sizes)),
                "min_packet_size": float(np.min(sizes)),
                "flow_duration": duration,
                "packet_rate": pkt_rate,
                "byte_rate": byte_rate,
                "unique_src_ports": len({p.src_port for p in pkts}),
            })

        return feature_rows

    def to_matrix(self, flows: List[Dict[str, Any]]) -> np.ndarray:
        return np.array([[f[name] for name in self.FEATURE_NAMES] for f in flows])
