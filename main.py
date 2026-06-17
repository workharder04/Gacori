#!/usr/bin/env python3
"""Network Anomaly Detector — CLI entry point."""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Network Anomaly Detector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  demo       Run offline demo with synthetic traffic (no root needed)
  capture    Capture live packets and detect anomalies in real time
  analyze    Analyze a CSV file of pre-captured flow data
  dashboard  Launch the Flask web dashboard (http://localhost:5000)
        """,
    )
    parser.add_argument("--mode", choices=["demo", "capture", "analyze", "dashboard"],
                        default="demo", help="Operating mode (default: demo)")
    parser.add_argument("--interface", default="eth0", help="Network interface for capture mode")
    parser.add_argument("--threshold", type=float, default=3.0, help="Z-score anomaly threshold")
    parser.add_argument("--input", help="Input CSV for analyze mode")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port (default: 5000)")

    args = parser.parse_args()

    if args.mode == "demo":
        import demo
        demo.main()

    elif args.mode == "capture":
        print(f"Starting live capture on {args.interface}…  (Ctrl-C to stop)")
        from detector.capture import PacketCapture
        from detector.features import FeatureExtractor
        from detector.model import AnomalyDetector
        from detector.alerts import AlertManager
        import numpy as np

        capture = PacketCapture(interface=args.interface)
        extractor = FeatureExtractor()
        model = AnomalyDetector(zscore_threshold=args.threshold)
        alert_mgr = AlertManager()
        trained = False

        try:
            while True:
                records = capture.capture(count=100)
                flows = extractor.extract_flows(records)
                if not flows:
                    continue
                X = extractor.to_matrix(flows)
                if not trained:
                    model.fit(X)
                    trained = True
                    print("Model trained on first batch.")
                results = model.predict_flows(flows, X)
                for r in results:
                    if r["anomaly"]:
                        alert = alert_mgr.process_result(r)
                        if alert:
                            print(f"[{alert.severity.value}] {alert.src_ip} → {alert.dst_ip} "
                                  f"score={alert.anomaly_score:.4f}")
        except KeyboardInterrupt:
            print("\nStopped. Summary:", alert_mgr.summary())

    elif args.mode == "analyze":
        if not args.input:
            print("Error: --input required for analyze mode", file=sys.stderr)
            sys.exit(1)
        import pandas as pd
        import numpy as np
        from detector.model import AnomalyDetector
        from detector.features import FeatureExtractor

        df = pd.read_csv(args.input)
        feature_cols = FeatureExtractor.FEATURE_NAMES
        missing = [c for c in feature_cols if c not in df.columns]
        if missing:
            print(f"Error: CSV missing columns: {missing}", file=sys.stderr)
            sys.exit(1)

        X = df[feature_cols].values
        model = AnomalyDetector(zscore_threshold=args.threshold)
        model.fit(X)
        labels, scores = model.predict(X)
        df["anomaly"] = labels == -1
        df["anomaly_score"] = scores

        n_anom = (labels == -1).sum()
        print(f"Analyzed {len(df)} flows — {n_anom} anomalies detected ({n_anom/len(df)*100:.1f}%)")

        if args.output:
            df.to_csv(args.output, index=False)
            print(f"Results saved to {args.output}")
        else:
            print(df[df["anomaly"]][["src_ip","dst_ip","protocol","anomaly_score"]].to_string())

    elif args.mode == "dashboard":
        print(f"Starting dashboard at http://localhost:{args.port}")
        from dashboard.app import run
        run(port=args.port)


if __name__ == "__main__":
    main()
