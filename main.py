import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
from langchain_core.messages import AIMessage

from agent import supervisor_agent
from settings import settings

app = FastAPI(title="Business Research Agent")

REPORTS_DIR = Path(settings.REPORTS_DIR).resolve()
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Business Research Agent is running.",
        "websocket": "/ws/research",
        "report_download": "/reports/{filename}",
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/reports/{filename}")
async def download_report(filename: str):
    safe_filename = Path(filename).name
    report_path = (REPORTS_DIR / safe_filename).resolve()

    if report_path.parent != REPORTS_DIR:
        raise HTTPException(
            status_code=400,
            detail="Invalid report path.",
        )

    if not report_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Report not found.",
        )

    if report_path.suffix.lower() != ".docx":
        raise HTTPException(
            status_code=400,
            detail="Only DOCX reports can be downloaded.",
        )

    return FileResponse(
        path=report_path,
        filename=report_path.name,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )

def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    text_parts: list[str] = []

    for item in content:
        if isinstance(item, str):
            text_parts.append(item)
            continue

        if not isinstance(item, dict):
            continue

        text = item.get("text")

        if isinstance(text, str):
            text_parts.append(text)

    return "".join(text_parts).strip()

def get_last_assistant_response(messages: list[Any]) -> str:
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue

        response = content_to_text(message.content)

        if response:
            return response

    return ""

@app.websocket("/ws/research")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    print(f"[WEBSOCKET] Connected: {thread_id}")

    await websocket.send_json(
        {
            "type": "connected",
            "thread_id": thread_id,
            "message": "Connected to the research agent.",
        }
    )

    try:
        while True:
            user_message = await websocket.receive_text()
            user_message = user_message.strip()

            if not user_message:
                continue

            print(f"\n[USER] {user_message}")

            try:
                result = await supervisor_agent.ainvoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_message,
                            }
                        ]
                    },
                    config=config,
                )

                messages = result.get("messages", [])

                assistant_response = get_last_assistant_response(
                    messages
                )

                if not assistant_response:
                    assistant_response = (
                        "The agent completed without returning "
                        "a user-facing response."
                    )

                await websocket.send_json(
                    {
                        "type": "response",
                        "message": assistant_response,
                    }
                )

            except Exception as exc:
                print(f"[AGENT ERROR] {exc!r}")

                await websocket.send_json(
                    {
                        "type": "error",
                        "message": str(exc),
                    }
                )

    except WebSocketDisconnect:
        print(
            f"[WEBSOCKET] Client disconnected: {thread_id}"
        )

    except Exception as exc:
        print(f"[WEBSOCKET ERROR] {exc!r}")

        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": str(exc),
                }
            )
        except Exception:
            pass
