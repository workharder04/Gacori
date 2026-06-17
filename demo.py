#!/usr/bin/env python3
"""
Standalone demo — no root, no scapy required.
Generates synthetic traffic, injects anomalies, runs detection, prints results.
"""
import time
import random
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ── ANSI colours ────────────────────────────────────────────────────────────
R  = "\033[91m"; Y = "\033[93m"; G = "\033[92m"
C  = "\033[96m"; B = "\033[94m"; W = "\033[97m"; M = "\033[95m"
DIM = "\033[2m";  RESET = "\033[0m"; BOLD = "\033[1m"

FEATURE_NAMES = [
    "packet_count", "mean_pkt_size", "std_pkt_size", "max_pkt_size",
    "min_pkt_size", "flow_duration", "packet_rate", "byte_rate", "unique_src_ports",
]


def generate_normal(n=300, seed=42):
    rng = np.random.default_rng(seed)
    return np.column_stack([
        rng.integers(10, 200, n),                      # packet_count
        rng.normal(512, 100, n).clip(64, 1500),        # mean_pkt_size
        rng.normal(80, 20, n).clip(0, 400),            # std_pkt_size
        rng.integers(512, 1500, n),                    # max_pkt_size
        rng.integers(64, 256, n),                      # min_pkt_size
        rng.uniform(0.5, 30, n),                       # flow_duration
        rng.uniform(1, 50, n),                         # packet_rate
        rng.uniform(500, 50_000, n),                   # byte_rate
        rng.integers(1, 5, n),                         # unique_src_ports
    ])


def generate_anomalies(n=20, seed=7):
    rng = np.random.default_rng(seed)
    kind = rng.integers(0, 3, n)
    rows = []
    for k in kind:
        if k == 0:   # port scan — many src ports, tiny packets
            rows.append([5000, 64, 0, 64, 64, 1.0, 5000, 320_000, 4000])
        elif k == 1: # flood — huge packet rate & byte rate
            rows.append([9999, 1400, 10, 1500, 1300, 0.1, 99990, 1_400_000, 1])
        else:        # exfiltration — large packets, slow, sustained
            rows.append([50, 1490, 5, 1500, 1480, 3600, 0.014, 74_500, 1])
    return np.array(rows, dtype=float)


def fake_ip():
    return f"10.0.{random.randint(0,5)}.{random.randint(1,254)}"


def print_header():
    print(f"\n{BOLD}{C}{'━'*60}{RESET}")
    print(f"{BOLD}{W}  🔍  Network Anomaly Detector — Demo{RESET}")
    print(f"{C}{'━'*60}{RESET}\n")


def print_section(title):
    print(f"\n{BOLD}{B}▶ {title}{RESET}")
    print(f"{DIM}{'─'*50}{RESET}")


def main():
    print_header()

    print_section("Generating synthetic network traffic")
    normal = generate_normal(300)
    anomalies = generate_anomalies(20)
    X_train = np.vstack([normal, anomalies[:10]])
    X_test  = np.vstack([normal[:50], anomalies[10:]])
    labels_true = np.array([1]*50 + [-1]*10)

    print(f"  {G}✓{RESET} Training samples : {BOLD}{len(X_train)}{RESET}")
    print(f"  {G}✓{RESET} Test samples      : {BOLD}{len(X_test)}{RESET}  ({Y}10 injected anomalies{RESET})")

    print_section("Training IsolationForest + Z-score ensemble")
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    iso = IsolationForest(contamination=0.1, n_estimators=100, random_state=42)
    iso.fit(X_train_s)

    iso_labels = iso.predict(X_test_s)
    iso_scores = iso.score_samples(X_test_s)

    zscore_flag = (np.abs(X_test_s) > 3.0).any(axis=1)
    ensemble    = np.where((iso_labels == -1) | zscore_flag, -1, 1)

    tp = ((ensemble == -1) & (labels_true == -1)).sum()
    fp = ((ensemble == -1) & (labels_true ==  1)).sum()
    fn = ((ensemble ==  1) & (labels_true == -1)).sum()
    tn = ((ensemble ==  1) & (labels_true ==  1)).sum()
    precision = tp / max(tp + fp, 1)
    recall    = tp / max(tp + fn, 1)
    f1        = 2 * precision * recall / max(precision + recall, 1e-9)

    print(f"  {G}✓{RESET} Model trained successfully")
    print(f"\n  {BOLD}Performance on test set:{RESET}")
    print(f"    Precision : {BOLD}{G}{precision:.1%}{RESET}")
    print(f"    Recall    : {BOLD}{G}{recall:.1%}{RESET}")
    print(f"    F1 Score  : {BOLD}{G}{f1:.1%}{RESET}")
    print(f"    TP={tp}  FP={fp}  FN={fn}  TN={tn}")

    print_section("Top detected anomalies")
    anomaly_indices = np.where(ensemble == -1)[0]
    print(f"  {R}⚠{RESET}  {len(anomaly_indices)} anomalous flows detected\n")

    types = ["port_scan", "flood_attack", "data_exfil"]
    header = f"  {'#':<4} {'Src IP':<18} {'Dst IP':<18} {'Score':>8}  {'Type':<15}  {'Severity'}"
    print(f"{DIM}{header}{RESET}")
    print(f"  {DIM}{'─'*75}{RESET}")

    for rank, idx in enumerate(anomaly_indices[:10], 1):
        score  = iso_scores[idx]
        atype  = types[(rank - 1) % 3]
        sev    = R+"CRITICAL"+RESET if score < -0.3 else Y+"HIGH"+RESET if score < -0.2 else C+"MEDIUM"+RESET
        src    = fake_ip()
        dst    = fake_ip()
        print(f"  {rank:<4} {src:<18} {dst:<18} {score:>8.4f}  {atype:<15}  {sev}")

    print_section("Alert summary")
    critical = sum(1 for i in anomaly_indices if iso_scores[i] < -0.3)
    high     = sum(1 for i in anomaly_indices if -0.3 <= iso_scores[i] < -0.2)
    medium   = sum(1 for i in anomaly_indices if -0.2 <= iso_scores[i] < -0.1)
    low      = sum(1 for i in anomaly_indices if iso_scores[i] >= -0.1)

    print(f"  {R}CRITICAL{RESET} : {critical}")
    print(f"  {Y}HIGH    {RESET} : {high}")
    print(f"  {C}MEDIUM  {RESET} : {medium}")
    print(f"  {G}LOW     {RESET} : {low}")

    print(f"\n{C}{'━'*60}{RESET}")
    print(f"  {G}Demo complete.{RESET}  Run {BOLD}python main.py --mode dashboard{RESET} for the live UI.")
    print(f"{C}{'━'*60}{RESET}\n")


if __name__ == "__main__":
    main()
