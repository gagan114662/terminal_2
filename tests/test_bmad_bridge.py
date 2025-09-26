import os

import pytest

BMAD_ENABLED = os.getenv("BMAD_ENABLED") == "1"


@pytest.mark.skipif(not BMAD_ENABLED, reason="BMAD not enabled")
def test_bmad_event_mapping_smoke():
    from termnet.bmad_trajectory_bridge import map_event_to_step

    step = map_event_to_step({"phase": "think", "elapsed_ms": 42})
    assert step.phase in {"reason", "act", "observe"}
    assert isinstance(step.latency_ms, int)
