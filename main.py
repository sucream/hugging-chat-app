from hugging_chat_app.app import get_app

import uvicorn


app = get_app()


def main():
    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )


if __name__ == "__main__":
    main()
