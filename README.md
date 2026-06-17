# Network Anomaly Detector

A real-time network anomaly detection system using an ensemble of **IsolationForest** and **Z-score** methods, with a live Flask web dashboard.

## Features

- **Unsupervised ML detection** — IsolationForest trained on flow-level features
- **Statistical detection** — Z-score outlier flagging per feature
- **Ensemble logic** — flag a flow as anomalous if *either* method triggers
- **Alert management** — severity levels (LOW / MEDIUM / HIGH / CRITICAL) with rate-limiting
- **Live dashboard** — dark-themed web UI with real-time charts (Chart.js)
- **CLI** — four modes: `demo`, `capture`, `analyze`, `dashboard`
- **No-root demo** — synthetic traffic generator, no scapy / root required

## Quick Start

```bash
pip install -r requirements.txt

# Run the standalone demo (no root needed)
python demo.py

# Or via main CLI
python main.py --mode demo
```

## Modes

| Mode | Description |
|------|-------------|
| `demo` | Synthetic traffic, injected anomalies, coloured terminal output |
| `capture` | Live packet capture on a real interface (requires root + scapy) |
| `analyze` | Analyze a pre-captured CSV of flow data |
| `dashboard` | Launch the Flask web UI at `http://localhost:5000` |

```bash
# Live capture on eth0
sudo python main.py --mode capture --interface eth0

# Analyze a CSV
python main.py --mode analyze --input data/sample_traffic.csv --output results.csv

# Web dashboard
python main.py --mode dashboard --port 5000
```

## Project Structure

```
├── detector/
│   ├── capture.py      # Packet capture (scapy or mock)
│   ├── features.py     # Flow-level feature extraction
│   ├── model.py        # IsolationForest + Z-score ensemble
│   └── alerts.py       # Alert severity & history
├── dashboard/
│   ├── app.py          # Flask API + background worker
│   └── templates/
│       └── index.html  # Dark-themed live dashboard
├── data/
│   └── sample_traffic.csv  # 50-row sample with injected anomalies
├── demo.py             # Standalone demo script
├── main.py             # CLI entry point
└── requirements.txt
```

## Detected Anomaly Types

- **Port scans** — high unique source ports, tiny packets, extreme packet rate
- **Flood attacks** — extreme packet rate and byte rate
- **Data exfiltration** — large sustained flows with unusual timing

## Dashboard

Start with `python main.py --mode dashboard` then open `http://localhost:5000`.

The dashboard shows:
- Live packet & anomaly counters
- Anomaly score timeline chart
- Top talkers bar chart
- Recent alerts table with severity badges
