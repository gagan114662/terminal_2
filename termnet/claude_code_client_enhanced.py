"""
Enhanced Claude Code CLI client for TermNet integration
Includes retry logic, context management, and task decomposition
"""

import asyncio
import os
import time
from typing import AsyncGenerator, Dict, List, Tuple

from termnet.config import CONFIG


class EnhancedClaudeCodeClient:
    def __init__(self):
        self.claude_path = CONFIG.get("CLAUDE_CLI_PATH", "claude")
        self.oauth_token = CONFIG.get("CLAUDE_CODE_OAUTH_TOKEN")
        self.max_retries = 3
        self.retry_delay = 2
        self.max_prompt_length = 8000  # Conservative limit for CLI

        # Set environment variable for authentication
        if self.oauth_token:
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = self.oauth_token

        # Conversation context tracking
        self.recent_context = []
        self.max_context_messages = 5

    async def chat_stream(
        self, messages, tools=None, temperature=0.7
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Enhanced stream chat with retry logic and context management
        """

        # Extract the latest user message
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            yield ("CONTENT", "No user message found")
            return

        latest_message = user_messages[-1]["content"]

        # Check if this is a complex task that needs decomposition
        if self._is_complex_task(latest_message):
            # Decompose into smaller subtasks
            subtasks = self._decompose_task(latest_message)
            if subtasks:
                yield (
                    "CONTENT",
                    f"Breaking down complex task into {len(subtasks)} steps:\n",
                )
                for i, subtask in enumerate(subtasks, 1):
                    yield ("CONTENT", f"\nStep {i}: {subtask}\n")
                    # Process each subtask
                    async for tag, content in self._execute_with_retry(
                        subtask, messages
                    ):
                        yield (tag, content)
                    await asyncio.sleep(0.5)  # Small delay between subtasks
                return

        # For normal tasks, execute with retry
        async for tag, content in self._execute_with_retry(latest_message, messages):
            yield (tag, content)

    async def _execute_with_retry(
        self, prompt: str, messages: List[Dict]
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Execute Claude CLI with retry logic
        """
        # Build context from recent messages
        context = self._build_context(messages)

        # Ensure prompt fits within limits
        prompt = self._truncate_if_needed(prompt)

        retry_count = 0
        last_error = None

        while retry_count < self.max_retries:
            try:
                # Build full prompt with context
                full_prompt = self._create_optimized_prompt(context, prompt)

                # Build Claude CLI command
                cmd = [
                    self.claude_path,
                    "--print",
                    "--dangerously-skip-permissions",
                    "--output-format",
                    "text",
                ]

                # Add model if specified
                claude_model = CONFIG.get("CLAUDE_MODEL")
                if claude_model:
                    cmd.extend(["--model", claude_model])

                cmd.append(full_prompt)

                # Set up environment
                env = os.environ.copy()
                env["CLAUDE_CODE_OAUTH_TOKEN"] = self.oauth_token

                # Add timeout for long-running commands
                timeout = 60  # 60 seconds timeout

                # Execute with timeout
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.getcwd(),
                    env=env,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=timeout
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    yield (
                        "CONTENT",
                        f"Request timed out after {timeout} seconds. Retrying with simpler prompt...",
                    )
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    # Simplify prompt for retry
                    prompt = self._simplify_prompt(prompt)
                    continue

                if process.returncode == 0:
                    response = stdout.decode("utf-8").strip()
                    if response:
                        # Cache successful response context
                        self._update_context(prompt, response)
                        yield ("CONTENT", response)
                        return
                    else:
                        # Empty response - retry with fallback
                        if retry_count == 0:
                            yield (
                                "CONTENT",
                                "Empty response, retrying with simplified prompt...",
                            )
                        retry_count += 1
                        prompt = self._simplify_prompt(prompt)
                        await asyncio.sleep(self.retry_delay)
                        continue
                else:
                    error_msg = stderr.decode("utf-8").strip()
                    last_error = error_msg

                    # Check for specific errors
                    if (
                        "model" in error_msg.lower()
                        and "not found" in error_msg.lower()
                    ):
                        # Model error - retry without model specification
                        CONFIG["CLAUDE_MODEL"] = ""
                        retry_count += 1
                        continue
                    elif (
                        "authentication" in error_msg.lower()
                        or "oauth" in error_msg.lower()
                    ):
                        # Authentication error - can't retry
                        yield ("CONTENT", f"Authentication error: {error_msg}")
                        return
                    else:
                        # Other error - retry
                        retry_count += 1
                        await asyncio.sleep(self.retry_delay)
                        continue

            except Exception as e:
                last_error = str(e)
                retry_count += 1
                await asyncio.sleep(self.retry_delay)
                continue

        # All retries exhausted
        if last_error:
            yield (
                "CONTENT",
                f"Failed after {self.max_retries} attempts. Last error: {last_error}",
            )
        else:
            yield ("CONTENT", "Failed to get response from Claude Code CLI")

    def _is_complex_task(self, prompt: str) -> bool:
        """
        Determine if a task is complex and needs decomposition
        """
        complex_indicators = [
            "analyze the entire",
            "analyze all",
            "comprehensive",
            "full codebase",
            "complete application",
            "entire project",
            "all files",
            "generate tests for all",
            "refactor everything",
        ]

        prompt_lower = prompt.lower()
        return any(indicator in prompt_lower for indicator in complex_indicators)

    def _decompose_task(self, prompt: str) -> List[str]:
        """
        Break down complex tasks into smaller subtasks
        """
        prompt_lower = prompt.lower()

        # Codebase analysis decomposition
        if "analyze" in prompt_lower and (
            "codebase" in prompt_lower or "project" in prompt_lower
        ):
            return [
                "List the main Python files in the termnet directory",
                "Analyze the agent.py file for structure and patterns",
                "Review the configuration system in config.py",
                "Identify performance bottlenecks in the tool loading system",
                "Suggest 3 specific improvements based on the analysis",
            ]

        # Test generation decomposition
        elif "generate tests" in prompt_lower or "unit tests" in prompt_lower:
            return [
                "Analyze the target file structure and main functions",
                "Create test setup and fixtures",
                "Write unit tests for core functionality",
                "Add edge case tests",
                "Create a test runner script",
            ]

        # Application creation decomposition
        elif "complete application" in prompt_lower or "crud" in prompt_lower:
            return [
                "Design the database schema",
                "Create the data models",
                "Implement CRUD operations",
                "Build the user interface",
                "Add error handling and validation",
                "Create usage documentation",
            ]

        # Default - don't decompose
        return []

    def _build_context(self, messages: List[Dict]) -> str:
        """
        Build optimized context from message history
        """
        # Get system prompt
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        system_context = ""
        if system_messages:
            system_context = system_messages[0]["content"]
            # Truncate system prompt if too long
            if len(system_context) > 2000:
                system_context = system_context[:2000] + "..."

        # Get recent relevant messages
        recent_messages = []
        for msg in messages[-self.max_context_messages :]:
            if msg.get("role") in ["user", "assistant"]:
                content = msg.get("content", "")
                if content and len(content) < 1000:  # Skip very long messages
                    recent_messages.append(f"{msg['role']}: {content[:500]}")

        # Include cached context if relevant
        context_parts = []
        if system_context:
            context_parts.append(f"Context: {system_context}")
        if recent_messages:
            context_parts.append(
                "Recent conversation:\n" + "\n".join(recent_messages[-3:])
            )

        return "\n\n".join(context_parts)

    def _create_optimized_prompt(self, context: str, prompt: str) -> str:
        """
        Create an optimized prompt that fits within CLI limits
        """
        # Add helpful instructions for better success
        instructions = """
IMPORTANT: You have access to terminal tools. When asked to perform tasks:
1. Execute commands directly when needed
2. Create and run files as requested
3. Provide concrete implementations, not just suggestions
4. Keep responses focused and actionable

"""

        # Combine parts
        full_prompt = f"{instructions}\n{context}\n\nUser: {prompt}"

        # Ensure it fits within limits
        if len(full_prompt) > self.max_prompt_length:
            # Trim context first
            available_space = (
                self.max_prompt_length - len(instructions) - len(prompt) - 20
            )
            if available_space > 0:
                context = context[:available_space] + "..."
                full_prompt = f"{instructions}\n{context}\n\nUser: {prompt}"
            else:
                # Just use prompt with instructions
                full_prompt = f"{instructions}\nUser: {prompt}"

        return full_prompt

    def _truncate_if_needed(self, text: str, max_length: int = 4000) -> str:
        """
        Truncate text if it exceeds maximum length
        """
        if len(text) > max_length:
            return text[: max_length - 20] + "... [truncated]"
        return text

    def _simplify_prompt(self, prompt: str) -> str:
        """
        Simplify a prompt for retry attempts
        """
        # Remove extra details and focus on core request
        simplified = prompt.split(".")[0] if "." in prompt else prompt
        simplified = simplified.split(",")[0] if "," in simplified else simplified

        # Add clarification
        if not simplified.endswith("?"):
            simplified += " (simplified request)"

        return simplified[:500]  # Keep it short

    def _update_context(self, prompt: str, response: str):
        """
        Update context cache with successful interactions
        """
        self.recent_context.append(
            {
                "prompt": prompt[:200],
                "response": response[:200],
                "timestamp": time.time(),
            }
        )

        # Keep only recent context
        if len(self.recent_context) > 10:
            self.recent_context = self.recent_context[-10:]

    def supports_tools(self) -> bool:
        """Claude Code CLI has built-in tool support"""
        return True
