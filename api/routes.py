import json
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from api.config import get_settings
from api.models import ChatRequest
from api.utils import process_non_streaming_response, process_streaming_response
from api.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

ALLOWED_MODELS = get_settings().ALLOWED_MODELS


@router.options("/chat/completions")
async def chat_completions_options():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


@router.get("/models")
async def list_models():
    return {"object": "list", "data": ALLOWED_MODELS, "success": True}


@router.post("/chat/completions")
async def chat_completions(request: Request, chat_request: ChatRequest):
    logger.info("Entering chat_completions route")
    # logger.info(f"Received request: {chat_request}")
    ## 获取header中的Authorization
    access_token = (
        request.headers.get("Authorization").split(" ")[-1]
        if request.headers.get("Authorization")
        else None
    )
    if access_token:
        logger.info(f"Access Token: {access_token}")
    else:
        logger.info("No Access Token provided")
        return Response(
            status_code=401,
            content=json.dumps({"message": "Unauthorized: Access token is missing"}),
            media_type="application/json",
        )
    logger.info(f"Received chat completion request for model: {chat_request.model}")

    if chat_request.model not in [model["id"] for model in ALLOWED_MODELS]:
        raise HTTPException(
            status_code=400,
            detail=f"Model {chat_request.model} is not allowed. Allowed models are: {', '.join(model['id'] for model in ALLOWED_MODELS)}",
        )

    if chat_request.stream:
        logger.info("Streaming response")
        return StreamingResponse(
            process_streaming_response(chat_request, access_token),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked",
            },
        )
    else:
        logger.info("Non-streaming response")
        return await process_non_streaming_response(chat_request, access_token)


@router.route("/")
@router.get("/health")
def health_check():
    return Response(content=json.dumps({"status": "ok"}), media_type="application/json")
