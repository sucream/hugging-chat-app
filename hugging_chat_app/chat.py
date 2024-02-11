from typing import TypedDict, Annotated
import re
import os
import asyncio
import uuid
import json

import aiohttp
from dotenv import load_dotenv


load_dotenv()


ConversationId = Annotated[str, "대화 ID"]


class LoginInfo(TypedDict):
    username: str
    password: str


class HuggingChat:
    def __init__(self, login_info: LoginInfo):
        self.login_info = login_info
        self.session = aiohttp.ClientSession()
        self.headers = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Host": "huggingface.co",
            "Origin": "https://huggingface.co",
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "application/json",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Ch-Ua": 'Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        }

    async def login(self):
        async with self.session.post(
            'https://huggingface.co/login',
            data=self.login_info,
        ) as response:
            # print(response.status)
            # # print(await response.text())
            # print(response.headers)
            # print(response.cookies.items())
            pass

        location = await self.getAuthURL()

        if await self.grantAuth(location):
            print("login success")
        else:
            raise Exception("login failed")

    async def new_conversation(
        self,
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        preprompt="You are a Korean chatbot. You must answer the user's questions in Korean not English."
    ) -> ConversationId:
        conversation_info = {
            "model": model,
            "preprompt": preprompt,
        }

        async with self.session.post(
            'https://huggingface.co/chat/conversation',
            headers=self.headers | {"Referer": "https://huggingface.co/chat"},
            json=conversation_info
        ) as response:
            if response.status != 200:
                raise Exception(f"new conversation fatal! - {response.status}")
            res_data = await response.json()
            return res_data["conversationId"]

    async def getAuthURL(self) -> str:
        url = "https://huggingface.co/chat/login"
        headers = {
            "Referer": "https://huggingface.co/chat/login",
            "User-Agent": self.headers["User-Agent"],
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with self.session.post(url, headers=headers) as response:
            if response.status == 200:
                res_data = await response.json()
                return res_data["location"]
            elif response.status == 303:
                location = response.headers["location"]
                if location:
                    return location
                else:
                    raise Exception("No location found!")
            else:
                raise Exception(f"get auth url fatal! - {response.status}")

    async def grantAuth(self, url: str) -> int:
        async with self.session.get(url, allow_redirects=False) as response:
            if response.headers.__contains__("location"):
                location = response.headers["location"]
                async with self.session.get(
                    location,
                    allow_redirects=False
                ) as response:
                    if response.cookies.__contains__("hf-chat"):
                        return 1

            if response.status != 200:
                raise Exception("grant auth fatal!")
            csrf = re.findall('/oauth/authorize.*?name="csrf" value="(.*?)"', response.text)
            if len(csrf) == 0:
                raise Exception("No csrf found!")
            data = {
                "csrf": csrf[0]
            }
            async with self.session.post(
                url,
                data=data,
                allow_redirects=False
            ) as response:
                if response.status != 303:
                    raise Exception(f"get hf-chat cookies fatal! - {response.status}")
                else:
                    location = response.headers.get("Location")
                async with self.session.get(location, allow_redirects=False) as response:
                    if response.status != 302:
                        raise Exception(f"get hf-chat cookie fatal! - {response.status}")
                    else:
                        return 1

    async def chat(self, conversation_id: str, query: str):
        url = f"https://huggingface.co/chat/conversation/{conversation_id}"

        headers = {
            "Origin": "https://huggingface.co",
            "Referer": f"https://huggingface.co/chat/conversation/{conversation_id}",
            "Content-Type": "application/json",
            "Sec-ch-ua": '"Chromium";v="94", "Microsoft Edge";v="94", ";Not A Brand";v="99"',
            "Sec-ch-ua-mobile": "?0",
            "Sec-ch-ua-platform": '"Windows"',
            "Accept": "*/*",
            "Accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6",
        }
        
        req_json = {
            "inputs": query,
            "parameters": {
                "temperature": 0.1,
                "top_p": 0.95,
                "repetition_penalty": 1.2,
                "top_k": 50,
                "truncate": 1000,
                "watermark": False,
                "max_new_tokens": 1024,
                "stop": ["</s>"],
                "return_full_text": False,
                "stream": True,
            },
            "options": {
                "use_cache": False,
                "is_retry": False,
                "id": str(uuid.uuid4()),
            },
            "stream": True,
            "web_search": False,
        }

        async with self.session.post(
            url,
            headers=headers,
            json=req_json
        ) as response:
            async for chunk in response.content:
                chunk_data = json.loads(chunk.decode('utf-8'))
                if chunk_data["type"] == "status":
                    pass
                elif chunk_data["type"] == "stream":
                    # print(chunk_data["token"], end="")
                    yield chunk_data["token"]
                elif chunk_data["type"] == "finalAnswer":
                    break
                else:
                    raise Exception("Unknown chunk type")


async def main():
    login_info = LoginInfo(
        username=os.getenv("LOGIN_ID"),
        password=os.getenv("LOGIN_PW")
    )
    
    hugging_chat = HuggingChat(login_info)
    await hugging_chat.login()
    conversation_id = await hugging_chat.new_conversation()

    while True:
        query = input("질문: ")
        if query == "exit":
            break
        # await hugging_chat.chat(conversation_id, query)
        async for chunk in hugging_chat.chat(conversation_id, query):
            print(chunk, end="")
        print()

    try:
        pass
    finally:
        await hugging_chat.session.close()


if __name__ == "__main__":
    asyncio.run(main())
