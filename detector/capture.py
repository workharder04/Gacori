"""Network packet capture — uses scapy when available, falls back to mock data."""
from __future__ import annotations

import time
import random
from dataclasses import dataclass, field
from typing import List, Callable, Optional


@dataclass
class PacketRecord:
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packet_size: int


class PacketCapture:
    def __init__(self, interface: str = "eth0", mock: bool = False):
        self.interface = interface
        self.mock = mock
        self._records: List[PacketRecord] = []
        self._running = False

        if not mock:
            try:
                import scapy.all  # noqa: F401
                self._backend = "scapy"
            except ImportError:
                self._backend = "mock"
        else:
            self._backend = "mock"

    def _mock_packet(self) -> PacketRecord:
        protocols = ["TCP", "UDP", "ICMP"]
        normal_ips = [f"192.168.1.{i}" for i in range(1, 20)]
        return PacketRecord(
            timestamp=time.time(),
            src_ip=random.choice(normal_ips),
            dst_ip=random.choice(normal_ips),
            src_port=random.randint(1024, 65535),
            dst_port=random.choice([80, 443, 22, 53, 8080]),
            protocol=random.choice(protocols),
            packet_size=random.randint(64, 1500),
        )

    def capture(self, count: int = 100, callback: Optional[Callable] = None) -> List[PacketRecord]:
        """Capture packets (real or mock)."""
        records: List[PacketRecord] = []

        if self._backend == "scapy":
            from scapy.all import sniff

            def handle(pkt):
                rec = self._parse_scapy(pkt)
                if rec:
                    records.append(rec)
                    if callback:
                        callback(rec)

            sniff(iface=self.interface, count=count, prn=handle, store=False)
        else:
            for _ in range(count):
                rec = self._mock_packet()
                records.append(rec)
                if callback:
                    callback(rec)
                time.sleep(0.01)

        self._records.extend(records)
        return records

    def _parse_scapy(self, pkt) -> Optional[PacketRecord]:
        try:
            from scapy.all import IP, TCP, UDP, ICMP

            if not pkt.haslayer(IP):
                return None
            ip = pkt[IP]
            proto = "OTHER"
            sport, dport = 0, 0

            if pkt.haslayer(TCP):
                proto, sport, dport = "TCP", pkt[TCP].sport, pkt[TCP].dport
            elif pkt.haslayer(UDP):
                proto, sport, dport = "UDP", pkt[UDP].sport, pkt[UDP].dport
            elif pkt.haslayer(ICMP):
                proto = "ICMP"

            return PacketRecord(
                timestamp=float(pkt.time),
                src_ip=ip.src,
                dst_ip=ip.dst,
                src_port=sport,
                dst_port=dport,
                protocol=proto,
                packet_size=len(pkt),
            )
        except Exception:
            return None
