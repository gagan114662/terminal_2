"""Auditor Agent: JSON-only verdict, hard gate for code review."""
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

AUDIT_SYSTEM = (
    "You are Qwen-VL acting as a rigorous code auditor for software changes.\n"
    "Task: Critique for correctness, security, policy compliance, "
    "over-engineering, edge cases, and tests.\n"
    "If the output includes unguarded destructive shell commands "
    "(e.g., 'rm -rf', 'dd if=/dev/zero', raw 'chmod -R 777', "
    "curl|bash without signature verification), "
    "the verdict MUST be 'fail' with score <= 0.3 and include actionable mitigations "
    "(allowlist checks, confirm flags, dry-run, tests).\n"
    "Return ONLY JSON with fields: "
    "score (0-1), verdict ('pass'|'fail'), reasons (list), actionable (list), "
    "issues (list of {type, where, detail}), suggested_tests (list)."
)


@dataclass
class AuditResult:
    score: float
    verdict: str
    payload: Dict[str, Any]


class AuditorAgent:
    def __init__(self, model: str, provider: str = "dashscope", min_score: float = 0.7):
        self.model = model
        self.min_score = min_score
        if provider.lower() == "dashscope":
            from termnet.dashscope_client import DashScopeClient

            self._client = DashScopeClient()
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")

    def _parse_json(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except Exception:
            s, e = content.find("{"), content.rfind("}")
            if s != -1 and e != -1:
                try:
                    return json.loads(content[s : e + 1])
                except Exception:
                    pass
            return {
                "score": 0.0,
                "verdict": "fail",
                "reasons": ["Non-JSON auditor response"],
                "actionable": [],
                "issues": [],
                "suggested_tests": [],
            }

    def audit(
        self,
        user_goal: str,
        claude_output: str,
        context: Optional[str] = None,
        images: Optional[list] = None,
    ) -> AuditResult:
        blocks = [
            {
                "type": "text",
                "text": (
                    f"# Goal\n{user_goal}\n\n"
                    f"# Output\n{claude_output}\n\n"
                    f"# Context\n{context or ''}"
                ),
            }
        ]
        if images:
            for url in images:
                blocks.append({"type": "input_image", "image_url": url})

        messages = [
            {"role": "system", "content": AUDIT_SYSTEM},
            {"role": "user", "content": blocks},
        ]
        resp = self._client.chat(self.model, messages, temperature=0.1)
        content = resp["choices"][0]["message"]["content"]
        data = self._parse_json(content)
        score = float(data.get("score", 0.0))
        verdict = (
            "pass"
            if (data.get("verdict") == "pass" and score >= self.min_score)
            else "fail"
        )
        return AuditResult(score=score, verdict=verdict, payload=data)
