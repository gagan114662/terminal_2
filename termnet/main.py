import asyncio

from termnet.agent import TermNetAgent
from termnet.tools.terminal import TerminalSession


async def main():
    print("TermNet v1.2 ready — type 'exit' to quit.\n")
    term = TerminalSession()
    await term.start()
    agent = TermNetAgent(term)
    loop = asyncio.get_running_loop()

    while True:
        user_input = await loop.run_in_executor(None, input, "You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        response = await agent.chat(user_input)
        print(f"TermNet: {response}")

    await term.stop()
    print("Closed.")


if __name__ == "__main__":
    asyncio.run(main())
