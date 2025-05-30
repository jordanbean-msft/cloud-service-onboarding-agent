import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import Response, StreamingResponse
from opentelemetry import trace

from app.models.chat_get_file_name import ChatGetFileNameInput
from app.models.chat_get_file_name_output import ChatGetFileNameOutput
from app.models.chat_get_image import ChatGetImageInput
from app.models.chat_get_image_contents import ChatGetImageContents
from app.models.chat_get_thread import ChatGetThreadInput
from app.models.chat_input import ChatInput
from app.routers.context import build_chat_context, chat_context_var
from app.services.chat import build_chat_results
from app.services.threads import create_thread, get_thread
from app.services.dependencies import AIProjectClientDependency, AsyncAzureAIClientDependency

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

router = APIRouter()

@tracer.start_as_current_span(name="create_thread")
@router.post("/create_thread")
async def create_thread_router(azure_ai_client: AIProjectClientDependency):
    return await create_thread(azure_ai_client)


@tracer.start_as_current_span(name="get_thread")
@router.get("/get_thread")
async def get_thread_router(thread_input: ChatGetThreadInput,
                            azure_ai_client: AIProjectClientDependency):
    return await get_thread(thread_input.thread_id, azure_ai_client)


@tracer.start_as_current_span(name="get_image_contents")
@router.get("/get_image_contents")
async def get_file_path_annotations(thread_input: ChatGetImageContents,
                                    azure_ai_client: AIProjectClientDependency):
    messages = []
    async for msg in azure_ai_client.agents.messages.list(thread_id=thread_input.thread_id):
        messages.append(msg)

    return_value = []

    for message in messages:
        return_value.append(
            {
                "type": message.type,
                "file_id": message.image_file.file_id,
            }
        )

    return return_value


@tracer.start_as_current_span(name="get_image")
@router.get("/get_image", response_class=Response)
async def get_image(thread_input: ChatGetImageInput,
                    azure_ai_client: AIProjectClientDependency):
    file_content_stream = await azure_ai_client.agents.files.get_content(thread_input.file_id)
    if not file_content_stream:
        raise RuntimeError(f"No content retrievable for file ID '{thread_input.file_id}'.")

    chunks = []
    async for chunk in file_content_stream:
        if isinstance(chunk, (bytes, bytearray)):
            chunks.append(chunk)
        else:
            raise TypeError(f"Expected bytes or bytearray, got {type(chunk).__name__}")

    image_data = b"".join(chunks)

    return Response(content=image_data, media_type="image/png")

@tracer.start_as_current_span(name="get_file_name")
@router.get("/get_file_name")
async def get_file_name(thread_input: ChatGetFileNameInput,
                        azure_ai_client: AIProjectClientDependency):
    file = await azure_ai_client.agents.files.get(thread_input.file_id)
    if not file:
        raise RuntimeError(f"No file found for ID '{thread_input.file_id}'.")

    return ChatGetFileNameOutput(
        file_name=file.filename,
        file_id=file.id
    )


@tracer.start_as_current_span(name="chat")
@router.post("/chat")
async def post_chat(chat_input: ChatInput):
    intermediate_message, close, queue = build_chat_context()
    chat_context_var.set((intermediate_message, close, queue))

    asyncio.create_task(
        build_chat_results(chat_input=chat_input)
    )

    async def event_generator():
        while True:
            event = await queue.get()
            if event is None:  # End of stream
                break
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
