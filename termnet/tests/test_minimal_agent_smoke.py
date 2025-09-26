import pytest

from termnet.agent import Agent  # alias to TermNetAgent
from termnet.tools.terminal import TerminalTool


@pytest.mark.asyncio
async def test_agent_smoke_runs_offline():
    tool = TerminalTool()
    tool.set_offline_mode(True)
    a = Agent(tool)
    resp = await a.chat("echo 'hello' and then show current directory")
    assert isinstance(resp, str)
