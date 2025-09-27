"""
Claude Code CLI client for TermNet integration
Uses your existing Claude Code subscription via CLI
"""

import asyncio
import os
from typing import AsyncGenerator, Tuple

from termnet.config import CONFIG


class ClaudeCodeClient:
    def __init__(self):
        self.claude_path = CONFIG.get("CLAUDE_CLI_PATH", "claude")
        self.oauth_token = CONFIG.get("CLAUDE_CODE_OAUTH_TOKEN")

        # Set environment variable for authentication
        if self.oauth_token:
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = self.oauth_token

    async def chat_stream(
        self, messages, tools=None, temperature=0.7
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Stream chat responses from Claude Code CLI
        Yields tuples of (type, content) where type is 'CONTENT' or 'TOOL'
        """

        # Extract the latest user message
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            yield ("CONTENT", "No user message found")
            return

        latest_message = user_messages[-1]["content"]

        # Get system prompt for context
        system_messages = [msg for msg in messages if msg.get("role") == "system"]
        system_context = ""
        if system_messages:
            system_context = system_messages[0]["content"]

        # Build full prompt with system context
        full_prompt = f"{system_context}\n\nUser: {latest_message}"

        # Build Claude CLI command for YOLO mode (no permissions)
        cmd = [
            self.claude_path,
            "--print",
            "--dangerously-skip-permissions",  # Skip permission dialogs
            "--output-format",
            "text",
        ]

        # Add model selection if specified
        claude_model = CONFIG.get("CLAUDE_MODEL")
        if claude_model:
            cmd.extend(["--model", claude_model])

        cmd.append(full_prompt)

        try:
            # Set up environment with OAuth token
            env = os.environ.copy()
            env["CLAUDE_CODE_OAUTH_TOKEN"] = self.oauth_token

            # Execute Claude CLI command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),  # Use current directory for context
                env=env,  # Explicit environment
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                response = stdout.decode("utf-8").strip()
                if response:
                    yield ("CONTENT", response)
                else:
                    yield ("CONTENT", "Empty response from Claude Code")
            else:
                error_msg = stderr.decode("utf-8").strip()
                yield ("CONTENT", f"Claude Code error: {error_msg}")

        except Exception as e:
            yield ("CONTENT", f"Failed to execute Claude Code CLI: {e}")

    def supports_tools(self) -> bool:
        """Claude Code CLI has built-in tool support"""
        return True
