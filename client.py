import asyncio
import aiohttp


async def main():
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8000/login") as response:
            pass
        async with session.post("http://localhost:8000/new_conversation") as response:
            conversation_id = (await response.json())["conversation_id"]

        async with session.post(
            f"http://localhost:8000/chat?conversation_id={conversation_id}&query=파이썬으로 간단한 계산기 코드를 보여줘"
        ) as response:
            async for chunk in response.content:
                print(chunk.decode("utf-8"), end="")
            print()


if __name__ == "__main__":
    asyncio.run(main())
