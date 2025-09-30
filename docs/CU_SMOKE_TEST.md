# CU Smoke Test: COMPLETE ✅

## Infrastructure Status

### CU Shim
- ✅ Running on `http://localhost:5055` (PID: 97261)
- ✅ Health endpoint: `{"ok":true,"service":"cu_shim","version":"1.0"}`
- ✅ Execute endpoint: Successfully ran `git status`, `python3 -m pytest -q`

### Environment
```bash
✅ CU_URL=http://localhost:5055
✅ DASHSCOPE_API_KEY=sk-c5c3...f258 (rotated)
✅ QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
✅ PYTHONPATH=termnet
```

### Test Results
1. ✅ Health check passed
2. ✅ Dry-run executed successfully
3. ✅ CU execute endpoint: `git status` → Exit 0
4. ✅ CU execute endpoint: `pytest -q` → Exit 0 (all tests passing)
5. ✅ TermNet CLI status: Ready

## Created Artifacts
- `cu_shim.py` - Local CU shim with allowlist guardrails
- `scripts/tn` - TermNet CLI wrapper
- `.logs/cu_shim.log` - CU shim logs
- `.logs/cu_shim.pid` - PID tracking

## CU Shim Allowlist (Safe Commands)
```python
{
  "git status",
  "git status --porcelain",
  "python3 -m pytest -q",
  "flake8 termnet/termnet/ tests/ scripts/",
  "ls",
  "pwd",
  "cat README.md"
}
```

## Next Steps for Full Integration

### Option 1: Keep local shim (current)
- Expand allowlist as needed in `cu_shim.py`
- Restart shim: `kill $(cat .logs/cu_shim.pid) && python3 cu_shim.py &`

### Option 2: Swap to GPU Qwen-VL (when ready)
```bash
# On GPU box (192.168.2.67)
python3 cu_qwen_server.py  # Your real CU service

# On laptop
ssh -N -L 5055:localhost:5055 root@192.168.2.67
# Then run same commands - CU_URL stays http://localhost:5055
```

### Option 3: Enhance TermNet CLI
Add `--use-computer` and `--provider` flags to `termnet/termnet/cli.py` for full CU integration.

## Summary of Completed Work

### PRs Merged
- PR #7: DMVL CI fixes (lint scope, Python 3.11, artifact upgrades)
- PR #8: Raised SLO from 85% → 95%
- PR #9: Scoped lint to changed files only

### Infrastructure
- ✅ Branch protection locked (lint + tests required)
- ✅ CU shim deployed and tested
- ✅ TermNet CLI validated
- ✅ Environment configured with rotated API key

## Green-Light Checklist

Before merging CU-related changes:

```bash
# 1. TermNet status
./scripts/tn status  # Should print "Ready"

# 2. CU health
curl -sfS $CU_URL/healthz | python3 -c "import sys,json; print('✅' if json.load(sys.stdin).get('ok') else '❌')"

# 3. Tests
python3 -m pytest -q

# 4. Lint
flake8 termnet/termnet/ tests/ scripts/

# 5. Receipts (if available)
python3 scripts/verify_receipts.py --latest
```

## Hardening Recommendations

### Security Enhancements
1. **Per-command timeout**: Cap execution at 60s
2. **Output size limit**: Max 200KB stdout
3. **Explicit denylist**: Block `rm -rf`, `sudo`, `ssh`, `curl http`, `python -c`, `>`, `|`
4. **Audit logging**: Record `{ts, cmd, cwd, exit, duration_ms, stdout_sha256}`

### GPU Switch (Zero-Downtime)
```bash
# Start real CU server on GPU host
ssh root@192.168.2.67 'cd /path/to/cu && python3 cu_qwen_server.py'

# Create SSH tunnel from laptop
ssh -N -L 5055:localhost:5055 root@192.168.2.67

# Keep CU_URL unchanged - CLI and receipts work identically
export CU_URL=http://localhost:5055
```

## CI Integration (Optional)

Add optional CU smoke test to CI:
```yaml
- name: CU Smoke Test (optional)
  if: env.CU_URL != ''
  run: |
    curl -sfS $CU_URL/healthz || echo "CU not available, skipping"
```

## Follow-Up Tasks

- [ ] Add `--use-computer` and `--provider` flags to CLI help
- [ ] Store `stdout_sha256` in receipts instead of full output
- [ ] Link receipts to `.logs/cu_shim.log` for full audit trail
- [ ] Implement per-command timeout and output size limits
- [ ] Add explicit denylist with pattern matching