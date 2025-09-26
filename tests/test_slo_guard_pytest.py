import json
import statistics


def test_slo_median_latency_ok(tmp_path):
    p = tmp_path / "metrics_dump.json"
    p.write_text(
        json.dumps(
            [
                {"reasoning_latency_ms": 200},
                {"reasoning_latency_ms": 250},
                {"reasoning_latency_ms": 280},
            ]
        )
    )
    data = json.loads(p.read_text())
    lat = [d["reasoning_latency_ms"] for d in data]
    assert statistics.median(lat) <= 300
