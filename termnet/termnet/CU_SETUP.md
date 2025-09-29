# Qwen Computer-Use Setup

TermNet supports Qwen-VL Computer-Use for remote claim verification via HTTP.

## Environment Variables

Set the following environment variables to enable Qwen CU:

```bash
export DASHSCOPE_API_KEY="your-api-key-here"
export QWEN_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
export CU_URL="http://localhost:5055"
```

## Provider Routing

- **Local execution** (default): Commands run via `subprocess.run()` in `termnet.cu_client.verify_claim()`
- **Qwen CU execution**: Set `use_computer=True` flag to route to `${CU_URL}/run`

## Usage

```bash
# Use local verification (default)
./scripts/tn project run "my brief"

# Use Qwen CU verification
./scripts/tn project run --use-computer "my brief"
```

## Receipt Metadata

All verification receipts include a `provider` field:
- `"provider": "local"` - Local subprocess execution
- `"provider": "qwen-vl-cu"` - Qwen VL Computer-Use HTTP proxy

## Testing

```bash
# Test local provider
PYTHONPATH=. python3 -m pytest tests/test_qwen_cu_provider.py::TestQwenCUProvider::test_verify_claim_local_smoke -v

# Test CU provider (mocked)
PYTHONPATH=. python3 -m pytest tests/test_qwen_cu_provider.py::TestQwenCUProvider::test_verify_claim_cu_mock -v
```