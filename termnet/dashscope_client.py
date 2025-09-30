"""DashScope client (OpenAI-compatible API)."""
import json
import os
import time

import requests

BASE = os.environ.get(
    "DASHSCOPE_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",  # intl by default
)


class DashScopeClient:
    def __init__(self, api_key=None, timeout=120, retries=2, backoff=1.5):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing DASHSCOPE_API_KEY")
        self.timeout, self.retries, self.backoff = timeout, retries, backoff

    def chat(self, model: str, messages: list, **kwargs) -> dict:
        url = f"{BASE.rstrip('/')}/chat/completions"
        payload = {"model": model, "messages": messages}
        payload.update(kwargs)
        last_err = None
        for i in range(self.retries + 1):
            try:
                r = requests.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    data=json.dumps(payload),
                    timeout=self.timeout,
                )
                if r.status_code == 401:
                    raise RuntimeError(
                        f"401 Unauthorized from {url}. "
                        "Check base_url region, key scope, or header."
                    )
                if r.status_code >= 500:
                    raise RuntimeError(f"DashScope 5xx: {r.text[:200]}")
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_err = e
                if i < self.retries:
                    time.sleep(self.backoff**i)
                else:
                    raise last_err
