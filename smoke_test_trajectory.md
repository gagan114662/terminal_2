# Canonical Trajectory Smoke Test

## Golden Prompt

Use this exact prompt for trajectory smoke testing:

```
Help me create a simple Python script that checks if a number is prime, then test it with the number 17.
```

## Expected Trajectory Pattern

**Phase 1: THINK** (50-150ms)
- Agent should reason about creating a prime checking algorithm
- Consider approach (trial division, optimization)
- Plan to create file and test

**Phase 2: ACT** (100-300ms)
- Tool: `terminal_execute`
- Action: Create Python file with prime checker function
- Example: `echo 'def is_prime(n): ...' > prime_checker.py`

**Phase 3: OBSERVE** (50-100ms)
- Verify file creation successful
- Check output for any errors

**Phase 4: ACT** (100-200ms)
- Tool: `terminal_execute`
- Action: Test the script with number 17
- Example: `python prime_checker.py` or `python -c "from prime_checker import is_prime; print(is_prime(17))"`

**Phase 5: OBSERVE** (50-100ms)
- Verify correct result (17 is prime = True)
- Report success to user

## Success Criteria

✅ **Functional**:
- Creates valid Python prime checking code
- Tests with 17 and returns `True` or equivalent
- No safety violations (all commands pass SafetyChecker)

✅ **Performance** (typical):
- Total trajectory: 350-750ms
- 3-5 ReAct steps
- Tool selection accuracy: 100% (only uses terminal_execute)

✅ **Telemetry**:
- Writes to `artifacts/last_run/trajectory.jsonl`
- Captures all THINK/ACT/OBSERVE phases
- Records latencies and tool usage

## Usage in CI/Tests

```bash
# Quick smoke test
TERMNET_METRICS=1 python -c "
from termnet.agent import TermNetAgent
from termnet.tools.terminal import TerminalTool
agent = TermNetAgent(TerminalTool())
result = agent.chat('Help me create a simple Python script that checks if a number is prime, then test it with the number 17.')
print('✅ Smoke test completed')
"

# Verify trajectory was recorded
ls artifacts/last_run/trajectory.jsonl
```

## Variants for Extended Testing

**Easy**: Check if 7 is prime
**Medium**: Create prime checker and test with 15 (composite)
**Hard**: Create optimized prime checker for numbers up to 1000

## Why This Prompt?

1. **Multi-step**: Requires planning, creation, and testing
2. **Tool usage**: Natural fit for terminal operations
3. **Verifiable**: Clear success/failure criteria (17 is definitively prime)
4. **Safe**: No dangerous operations, stays in project directory
5. **Representative**: Common coding assistant use case
6. **Measurable**: Consistent performance baseline

This prompt exercises the full ReAct loop while remaining deterministic and safe for automated testing.