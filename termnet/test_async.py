import asyncio


async def test():
    print("Starting async test...")
    await asyncio.sleep(1)
    print("Async test completed!")
    return "Test successful"


if __name__ == "__main__":
    result = asyncio.run(test())
    print(f"Result: {result}")
