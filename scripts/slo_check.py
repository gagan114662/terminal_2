#!/usr/bin/env python3
import json
import statistics
import sys
from pathlib import Path

ART = Path("artifacts/last_run/metrics_dump.json")
lat = []
if ART.exists():
    try:
        data = json.loads(ART.read_text() or "[]")
        lat = [d.get("reasoning_latency_ms", 0) for d in data if isinstance(d, dict)]
    except Exception:
        pass

if not lat:
    print("✅ Latency OK: median=0ms (no metrics yet)")
    sys.exit(0)

m = statistics.median(lat[-10:])
threshold = int(sys.argv[1] if len(sys.argv) > 1 else 300)
if m > threshold:
    print(f"❌ Latency regression: median={m}ms > {threshold}ms")
    sys.exit(1)
print(f"✅ Latency OK: median={m}ms")
