# TermNet Verification Commands

## Core Contract Tests
```bash
pytest -q tests/test_safety.py tests/test_toolloader.py
```

## Trajectory + SLO Check
```bash
TERMNET_METRICS=1 python - <<'PY'
from termnet.trend_analysis import TrendAnalyzer
TrendAnalyzer().collect_request_metrics(1,250,0.85,"ci-smoke")
print("OK")
PY

python scripts/slo_check.py
```

## Dry-run Safety Test (no file changes)
```bash
# Verify no files changed after dry-run:
git diff --exit-code && echo "No changes applied (expected)"
```

## Write-guard Test (should block)
Ask Claude to edit `/etc/hosts` or `~/.ssh/config` → expect `BLOCKED`

## Test All Safety Checks
```bash
pytest -q tests/test_write_guard_allowlist.py
pytest -q tests/test_dry_run_mode.py
pytest -q tests/test_slo_guard.py
pytest -q tests/test_secrets_redaction.py
```

## Quick Verification Suite
```bash
# Run all safety tests
pytest -q tests/test_*.py -k "safety or slo or dry_run or secrets or write_guard"

# Check configuration
python -c "import json; c=json.load(open('TermNet/config.json')); print('✅ Config OK' if c['write_guardrails']['dry_run'] and c['model_config']['temperature']==0.3 else '❌ Config issues')"

# Verify SLO
python TermNet/scripts/slo_check.py
```
