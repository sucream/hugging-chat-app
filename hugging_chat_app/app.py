import os

from hugging_chat_app.chat import HuggingChat, LoginInfo

from fastapi import FastAPI, status
from fastapi.responses import StreamingResponse, JSONResponse


hugging_chat_obj = None


def get_app():
    app = FastAPI()

    @app.get("/")
    async def root():
        return {"message": "Hello Hugging Chat!"}

    @app.post(
        "/login",
        summary="HuggingFace 로그인"
    )
    async def login(username: str | None = None, password: str | None = None):
        if username is None or password is None:
            login_info = LoginInfo(
                username=os.getenv("LOGIN_ID"),
                password=os.getenv("LOGIN_PW")
            )
        else:
            login_info = LoginInfo(
                username=username,
                password=password
            )
        global hugging_chat_obj
        hugging_chat_obj = HuggingChat(login_info)
        try:
            await hugging_chat_obj.login()
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "로그인 실패"}
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "로그인 성공"}
        )

    @app.post(
        "/new_conversation",
        summary="새로운 대화 세션 생성"
    )
    async def new_conversation():
        global hugging_chat_obj
        if hugging_chat_obj is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "로그인이 필요합니다."}
            )

        conversation_id = await hugging_chat_obj.new_conversation()
        return {"conversation_id": conversation_id}

    @app.get(
        "/conversations",
        summary="대화 세션 목록 확인"
    )
    async def get_conversations():
        global hugging_chat_obj
        if hugging_chat_obj is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "로그인이 필요합니다."}
            )

        return {"conversations": await hugging_chat_obj.get_conversations()}

    @app.post(
        "/chat",
        summary="대화하기",
        description="`conversation_id`에 해당하는 대화에 `query`를 보내고 대화 결과를 스트리밍합니다.",
    )
    async def chat(conversation_id: str, query: str):
        global hugging_chat_obj
        if hugging_chat_obj is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "로그인이 필요합니다."}
            )

        return StreamingResponse(hugging_chat_obj.chat(conversation_id, query))

    return app
