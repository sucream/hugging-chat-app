import os

from hugging_chat_app.chat import HuggingChat, LoginInfo

from fastapi import FastAPI
from fastapi.responses import StreamingResponse


hugging_chat_obj = None


def get_app():
    app = FastAPI()

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.get(
        "/login",
        summary="HuggingFace 로그인"
    )
    async def login():
        login_info = LoginInfo(
            username=os.getenv("LOGIN_ID"),
            password=os.getenv("LOGIN_PW")
        )
        global hugging_chat_obj
        hugging_chat_obj = HuggingChat(login_info)
        await hugging_chat_obj.login()

        return {"message": "Login Success"}

    @app.get(
        "/new_conversation",
        summary="새로운 대화 시작"
    )
    async def new_conversation():
        global hugging_chat_obj
        conversation_id = await hugging_chat_obj.new_conversation()
        return {"conversation_id": conversation_id}

    @app.get(
        "/chat",
        summary="대화하기",
        description="`conversation_id`에 해당하는 대화에 `query`를 보내고 대화 결과를 스트리밍합니다.",
    )
    async def chat(conversation_id: str, query: str):
        global hugging_chat_obj
        return StreamingResponse(hugging_chat_obj.chat(conversation_id, query))

    return app
