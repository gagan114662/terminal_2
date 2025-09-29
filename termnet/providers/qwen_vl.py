"""
Qwen-VL provider using OpenAI-compatible endpoint.
Supports multimodal messages (text + images) via OpenAI client.
"""

from typing import Any, Dict, List, Optional


class QwenVLClient:
    """Qwen-VL client wrapper for OpenAI-compatible API."""

    def __init__(self, api_key: str, base_url: str, model: str):
        """
        Initialize Qwen-VL client.

        Args:
            api_key: API key from environment
            base_url: Base URL for OpenAI-compatible endpoint
            model: Model name to use
        """
        try:
            import openai

            self.openai = openai
        except ImportError:
            raise ImportError("openai package required for Qwen-VL provider")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = self.openai.OpenAI(api_key=api_key, base_url=base_url)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.2,
    ) -> Any:
        """
        Execute chat completion with Qwen-VL.

        Args:
            messages: List of message dicts with multimodal content
                     e.g., [{"role": "user", "content": [{"type": "text", "text": "..."},
                            {"type": "image_url", "image_url": {"url": "..."}}]}]
            tools: Optional list of tool definitions
            tool_choice: Tool selection mode ("auto", "none", or specific tool)
            temperature: Sampling temperature

        Returns:
            OpenAI ChatCompletion response object
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools is not None:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        return self.client.chat.completions.create(**kwargs)
