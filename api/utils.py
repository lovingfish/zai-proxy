from datetime import datetime
from fastapi import HTTPException
import json
from typing import Any, Dict, Optional
import uuid
import httpx

from api.config import get_settings
from api.models import ChatRequest
from api.logger import setup_logger

logger = setup_logger(__name__)

settings = get_settings()
BASE_URL = settings.PROXY_URL


def create_chat_completion_data(
    content: str,
    model: str,
    timestamp: int,
    phase: str,
    usage: Optional[dict] = None,
    finish_reason: Optional[str] = None,
) -> Dict[str, Any]:
    if phase == "answer":
        finish_reason = None
        delta = {"content": content, "role": "assistant"}
    elif phase == "thinking":
        finish_reason = None
        delta = {"reasoning_content": content, "role": "assistant"}
    elif phase == "other":
        finish_reason = finish_reason
        delta = {"content": content, "role": "assistant"}

    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion.chunk",
        "created": timestamp,
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
        "usage": None if usage is None else usage,
    }


def message_to_dict(message):
    if isinstance(message.content, str):
        return {"role": message.role, "content": message.content}
    elif isinstance(message.content, list) and len(message.content) == 2:
        return {
            "role": message.role,
            "content": message.content[0]["text"],
            "data": {
                "imageBase64": message.content[1]["image_url"]["url"],
                "fileText": "",
                "title": "snapshoot",
            },
        }
    else:
        return {"role": message.role, "content": message.content}


async def process_streaming_response(request: ChatRequest, access_token: str):

    zai_data = {
        "stream": True,
        "model": request.model,
        "messages": [message_to_dict(msg) for msg in request.messages],
        "features": {
            "image_generation": True,
            "web_search": False,
            "auto_web_search": True,
            "preview_mode": True,
            "flags": [],
            "enable_thinking": True,
        },
        "chat_id": str(uuid.uuid4()),
        "id": str(uuid.uuid4()),
    }

    settings.HEADERS["Authorization"] = f"Bearer {access_token}"
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                f"{BASE_URL}/api/chat/completions",
                headers=settings.HEADERS,
                json=zai_data,
                timeout=100,
            ) as response:
                response.raise_for_status()
                timestamp = int(datetime.now().timestamp())
                async for line in response.aiter_lines():
                    if line:
                        if line.startswith("data:"):
                            json_str = line[6:]  # 去掉 "data: " 前缀
                            json_object = json.loads(json_str)
                            if json_object.get("data").get("phase") == "thinking":
                                if json_object.get("data").get(
                                    "delta_content"
                                ) and "</summary>\n" in json_object.get("data").get(
                                    "delta_content"
                                ):
                                    content = (
                                        json_object.get("data")
                                        .get("delta_content", "")
                                        .split("</summary>\n")[-1]
                                    )
                                else:
                                    content = json_object.get("data").get(
                                        "delta_content", ""
                                    )
                                yield f"data: {json.dumps(create_chat_completion_data(content, request.model, timestamp, 'thinking'))}\n\n"
                            elif json_object.get("data").get("phase") == "answer":
                                if json_object.get("data").get(
                                    "edit_content"
                                ) and "</summary>\n" in json_object.get("data").get(
                                    "edit_content"
                                ):
                                    content = (
                                        json_object.get("data")
                                        .get("edit_content", "")
                                        .split("</details>")[-1]
                                    )
                                elif json_object.get("data").get("delta_content"):
                                    content = json_object.get("data").get(
                                        "delta_content"
                                    )
                                yield f"data: {json.dumps(create_chat_completion_data(content, request.model, timestamp, 'answer'))}\n\n"
                            elif json_object.get("data").get("phase") == "other":
                                usage = json_object.get("data").get("usage", {})
                                content = json_object.get("data").get(
                                    "delta_content", ""
                                )
                                yield f"data: {json.dumps(create_chat_completion_data(content, request.model, timestamp, 'other', usage, 'stop'))}\n\n"
                            elif json_object.get("data").get("phase") == "done":
                                yield "data: [DONE]\n\n"
                                break

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
        except httpx.RequestError as e:
            logger.error(f"Error occurred during request: {e}")


async def process_non_streaming_response(request: ChatRequest, access_token: str):
    zai_data = {
        "stream": False,
        "model": request.model,
        "messages": [message_to_dict(msg) for msg in request.messages],
        "features": {
            "image_generation": True,
            "web_search": False,
            "auto_web_search": True,
            "preview_mode": True,
            "flags": [],
            "enable_thinking": True,
        },
        "chat_id": str(uuid.uuid4()),
        "id": str(uuid.uuid4()),
    }

    settings.HEADERS["Authorization"] = f"Bearer {access_token}"
    full_response = ""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            method="POST",
            url=f"{BASE_URL}/api/chat",
            headers=settings.HEADERS,
            json=zai_data,
        ) as response:
            async for chunk in response.aiter_text():
                full_response += chunk
    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": full_response},
                "finish_reason": "stop",
            }
        ],
        "usage": None,
    }
