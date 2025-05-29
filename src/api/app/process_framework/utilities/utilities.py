import json
import logging
from typing import Any, AsyncIterable

from opentelemetry import trace
from semantic_kernel.contents import (AnnotationContent, ChatHistory,
                                      ChatMessageContent, FileReferenceContent,
                                      FunctionCallContent,
                                      FunctionResultContent, TextContent)
from semantic_kernel.contents.streaming_annotation_content import \
    StreamingAnnotationContent
from semantic_kernel.contents.streaming_file_reference_content import \
    StreamingFileReferenceContent
from semantic_kernel.contents.streaming_text_content import \
    StreamingTextContent

from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.services.agents import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


async def _post_intermediate_message(post_intermediate_message,
                                     content: Any,
                                     thread_id: str = "asdf"):
    if post_intermediate_message is not None:

        obj = None
        if isinstance(content, StreamingTextContent):
            obj = ChatOutput(
                content_type=ContentTypeEnum.MARKDOWN,
                content=content.text,
                thread_id=thread_id,
            )
        elif isinstance(content, StreamingAnnotationContent):
            obj = ChatOutput(
                content_type=ContentTypeEnum.ANNOTATION,
                content=content.quote if content.quote else '',
                thread_id=thread_id,
            )
        elif isinstance(content, StreamingFileReferenceContent):
            obj = ChatOutput(
                content_type=ContentTypeEnum.FILE,
                content=content.file_id if content.file_id else '',
                thread_id=thread_id,
            )
        elif isinstance(content, AnnotationContent):
            obj = ChatOutput(
                content_type=ContentTypeEnum.ANNOTATION,
                content=content.quote if content.quote else '',
                thread_id=thread_id,
            )
        elif isinstance(content, FileReferenceContent):
            obj = ChatOutput(
                content_type=ContentTypeEnum.FILE,
                content=content.file_id if content.file_id else '',
                thread_id=thread_id,
            )
        elif isinstance(content, TextContent):
            obj = ChatOutput(
                content_type=ContentTypeEnum.MARKDOWN,
                content=content.text,
                thread_id=thread_id,
            )
        elif isinstance(content, str):
            obj = ChatOutput(
                content_type=ContentTypeEnum.MARKDOWN,
                content=content,
                thread_id=thread_id,
            )

        await post_intermediate_message(json.dumps(
            obj=obj,
            default=serialize_chat_output,
        ) + "\n")


async def post_beginning_info(title, message, post_intermediate_message):
    final_response = f"""
***
## {title}
{message}
"""
    logger.debug(final_response)

    await _post_intermediate_message(post_intermediate_message, final_response)


async def post_intermediate_info(message, post_intermediate_message):
    await _post_intermediate_message(post_intermediate_message, message)


async def post_error(title, exception, post_intermediate_message):
    final_response = f"""
***
**{title}**
{exception}
"""
    logger.error(final_response)

    await _post_intermediate_message(post_intermediate_message, final_response)


async def print_on_intermediate_message(message: ChatMessageContent):
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            logger.debug(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            logger.debug(f"Function Result:> {item.result} for function: {item.name}")
        else:
            logger.debug(f"{message.role}: {message.content}")


async def invoke_agent_stream(agent_name: str,
                              chat_history: ChatHistory) -> AsyncIterable[Any]:
    agent_manager = get_create_agent_manager()

    agent = None
    for a in agent_manager:
        if a.name == agent_name:
            agent = a
            break

    if not agent:
        raise ValueError(f"{agent_name} not found.")

    thread = None
    annotations = []
    file_references = []
    try:
        async for response in agent.invoke_stream(
            thread=thread,
            messages=chat_history.messages,  # type: ignore
            on_intermediate_message=print_on_intermediate_message,
        ):
            thread = response.thread

            for item in response.items:
                yield item

            # yield response.content.content
    except Exception as e:
        logger.error(f"Error calling agent {agent_name}: {e}")
        raise

    logger.debug(f"Final thread ID: {thread.id if thread else 'None'}")


async def invoke_agent(agent_name: str,
                       chat_history: ChatHistory) -> AsyncIterable[Any]:
    agent_manager = get_create_agent_manager()

    agent = None
    for a in agent_manager:
        if a.name == agent_name:
            agent = a
            break

    if not agent:
        raise ValueError(f"{agent_name} not found.")

    thread = None
    text_content = []
    annotations = []
    file_references = []
    try:
        async for response in agent.invoke(
            thread=thread,
            messages=chat_history.messages,  # type: ignore
            on_intermediate_message=print_on_intermediate_message,
            parallel_tool_calls=False
        ):
            thread = response.thread

            for item in response.items:
                yield item

    except Exception as e:
        logger.error(f"Error calling agent {agent_name}: {e}")
        raise

    logger.debug(f"Final thread ID: {thread.id if thread else 'None'}")

__all__ = [
    "invoke_agent_stream",
    "post_beginning_info",
    "post_intermediate_info",
    "post_error",
    "invoke_agent",
]
