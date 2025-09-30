#!/usr/bin/env python3
import csv
import json
import os
from datetime import datetime

# Load current summary
if os.path.exists("artifacts/verify_summary.json"):
    with open("artifacts/verify_summary.json") as f:
        data = json.load(f)

    # Append to history
    os.makedirs("artifacts", exist_ok=True)
    history_file = "artifacts/history.csv"

    fieldnames = [
        "timestamp",
        "rag_results",
        "rag_confidence",
        "react_steps",
        "react_insights",
        "analyze_files",
        "analyze_entities",
        "semantic_hits",
        "orchestrator_steps",
    ]

    file_exists = os.path.exists(history_file)
    with open(history_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(),
                "rag_results": data.get("rag", {}).get("results", 0),
                "rag_confidence": data.get("rag", {}).get("confidence", 0.0),
                "react_steps": data.get("react", {}).get("steps", 0),
                "react_insights": data.get("react", {}).get("insights", 0),
                "analyze_files": data.get("analyze", {}).get("files", 0),
                "analyze_entities": data.get("analyze", {}).get("entities", 0),
                "semantic_hits": data.get("semantic", {}).get("hits", 0),
                "orchestrator_steps": data.get("orchestrator", {}).get("plan_steps", 0),
            }
        )

    print("✅ Metrics added to trend history")
    print(f"History file: {history_file}")
else:
    print("❌ No verify_summary.json found - run 'make verify' first")
