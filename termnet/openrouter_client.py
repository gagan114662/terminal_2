"""
OpenRouter API client for TermNet integration
Replaces Ollama with OpenRouter for cloud-based LLM access
"""

import json
import time
from typing import AsyncGenerator, Dict, List, Tuple

import aiohttp


class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://termnet.local",
            "X-Title": "TermNet AI Terminal Assistant",
        }

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict],
        tools: List[Dict] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[Tuple[str, any], None]:
        """
        Stream chat responses from OpenRouter API
        Yields tuples of (type, content) where type is 'CONTENT' or 'TOOL'
        """

        # Convert TermNet tool format to OpenAI tool format for GPT-OSS
        openai_tools = []
        if tools:
            for tool in tools:
                if tool.get("type") == "function":
                    openai_tools.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool["function"]["name"],
                                "description": tool["function"]["description"],
                                "parameters": tool["function"]["parameters"],
                            },
                        }
                    )

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "max_tokens": 4000,
        }

        # Add tools for GPT-OSS models that support tool calling
        if openai_tools and self._model_supports_tools(model):
            payload["tools"] = openai_tools
            payload["tool_choice"] = "auto"

        try:
            # Create SSL context that doesn't verify certificates (for testing)
            import ssl

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            timeout = aiohttp.ClientTimeout(total=300)
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            # Accumulate tool calls across streaming chunks
            accumulated_tool_calls = {}

            async with aiohttp.ClientSession(
                timeout=timeout, headers=self.headers, connector=connector
            ) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions", json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"❌ OpenRouter API error {response.status}: {error_text}")
                        yield ("CONTENT", f"API Error: {error_text}")
                        return

                    async for line in response.content:
                        if not line.strip():
                            continue

                        line_str = line.decode("utf-8").strip()
                        if not line_str.startswith("data: "):
                            continue

                        if line_str == "data: [DONE]":
                            # Send accumulated tool calls if any
                            if accumulated_tool_calls:
                                complete_tools = []
                                for (
                                    call_id,
                                    tool_data,
                                ) in accumulated_tool_calls.items():
                                    if tool_data.get("function", {}).get(
                                        "name"
                                    ) and tool_data.get("function", {}).get(
                                        "arguments"
                                    ):
                                        complete_tools.append(
                                            {
                                                "id": call_id,
                                                "function": tool_data["function"],
                                            }
                                        )
                                if complete_tools:
                                    yield ("TOOL", complete_tools)
                            break

                        try:
                            json_str = line_str[6:]  # Remove 'data: ' prefix
                            data = json.loads(json_str)

                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                delta = choice.get("delta", {})

                                # Handle content streaming
                                if "content" in delta and delta["content"]:
                                    yield ("CONTENT", delta["content"])

                                # Handle tool calls - accumulate them
                                if "tool_calls" in delta and delta["tool_calls"]:
                                    for tool_call in delta["tool_calls"]:
                                        # Use index to track tool calls since id only appears in first chunk
                                        index = tool_call.get("index", 0)
                                        call_id = tool_call.get("id")

                                        # If this is the first chunk for this index, store the id
                                        if call_id:
                                            accumulated_tool_calls[index] = {
                                                "id": call_id,
                                                "function": {
                                                    "name": "",
                                                    "arguments": "",
                                                },
                                            }

                                        # Make sure we have this index in our accumulator
                                        if index not in accumulated_tool_calls:
                                            # This shouldn't happen but just in case
                                            accumulated_tool_calls[index] = {
                                                "id": f"call_{index}_{int(time.time())}",
                                                "function": {
                                                    "name": "",
                                                    "arguments": "",
                                                },
                                            }

                                        # Update function name
                                        if tool_call.get("function", {}).get("name"):
                                            accumulated_tool_calls[index]["function"][
                                                "name"
                                            ] = tool_call["function"]["name"]

                                        # Accumulate arguments
                                        if tool_call.get("function", {}).get(
                                            "arguments"
                                        ):
                                            accumulated_tool_calls[index]["function"][
                                                "arguments"
                                            ] += tool_call["function"]["arguments"]

                                # Check if tool calls are complete (finish_reason is tool_calls)
                                if (
                                    choice.get("finish_reason") == "tool_calls"
                                    and accumulated_tool_calls
                                ):
                                    complete_tools = []
                                    for (
                                        index,
                                        tool_data,
                                    ) in accumulated_tool_calls.items():
                                        if tool_data.get("function", {}).get(
                                            "name"
                                        ) and tool_data.get("function", {}).get(
                                            "arguments"
                                        ):
                                            complete_tools.append(
                                                {
                                                    "id": tool_data.get(
                                                        "id", f"call_{index}"
                                                    ),
                                                    "function": tool_data["function"],
                                                }
                                            )
                                    if complete_tools:
                                        yield ("TOOL", complete_tools)
                                    # Clear accumulated tools
                                    accumulated_tool_calls = {}

                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            print(f"❌ Error processing stream chunk: {e}")
                            continue

        except Exception as e:
            print(f"❌ OpenRouter client error: {e}")
            yield ("CONTENT", f"Connection error: {e}")

    def _model_supports_tools(self, model: str) -> bool:
        """Check if the model supports function calling/tools"""
        # GPT-OSS models and other tool-supporting models
        tool_supported_models = [
            "openai/gpt-4",
            "openai/gpt-4o",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3.1-70b-instruct",
            "mistralai/mixtral-8x7b-instruct",
        ]

        # GPT-OSS models do not support OpenAI function calling format

        return any(supported in model for supported in tool_supported_models)

    async def get_available_models(self) -> List[Dict]:
        """Get list of available models from OpenRouter"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(f"{self.base_url}/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        print(f"❌ Failed to fetch models: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Error fetching models: {e}")
            return []
