import json

from termnet.trajectory_logger import TrajectoryStep, log_step, now_iso


def test_trajectory_logger_jsonl(tmp_path, monkeypatch):
    outdir = tmp_path / "artifacts" / "last_run"
    monkeypatch.setenv("TERMNET_ARTIFACTS_DIR", str(outdir))
    outdir.mkdir(parents=True, exist_ok=True)

    log_step(
        TrajectoryStep(
            run_id="test-run",
            trace_id="test-trace",
            step_index=0,
            phase="reason",
            timestamp=now_iso(),
            latency_ms=123,
        )
    )

    f = outdir / "trajectory.jsonl"
    assert f.exists()
    line = f.read_text().strip().splitlines()[0]
    obj = json.loads(line)
    assert obj["run_id"] == "test-run"
    assert obj["phase"] == "reason"
    assert isinstance(obj["latency_ms"], int)
