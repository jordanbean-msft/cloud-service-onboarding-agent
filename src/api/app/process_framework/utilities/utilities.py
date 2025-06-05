import json
import logging
from tracemalloc import start
from typing import Any, AsyncIterable

from opentelemetry import trace
from semantic_kernel.contents import (ChatHistory,
                                      ChatMessageContent,
                                      FunctionCallContent,
                                      FunctionResultContent, )
from semantic_kernel.contents.annotation_content import CitationType
from semantic_kernel.contents.streaming_annotation_content import \
    StreamingAnnotationContent
from semantic_kernel.contents.streaming_file_reference_content import \
    StreamingFileReferenceContent
from semantic_kernel.contents.streaming_text_content import \
    StreamingTextContent
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgentThread

from app.models.streaming_annotation_file_output import StreamingAnnotationFileOutput, serialize_streaming_annotation_file_output
from app.models.streaming_annotation_url_output import StreamingAnnotationUrlOutput, serialize_streaming_annotation_url_output
from app.models.content_type_enum import ContentTypeEnum
from app.models.streaming_sentinel_output import StreamingSentinelOutput, serialize_streaming_sentinel_output
from app.models.streaming_text_output import StreamingTextOutput, serialize_streaming_text_output
from app.services.agents import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


async def _post_intermediate_message(post_intermediate_message,
                                     content: Any,
                                     thread_id: str = "asdf"):
    if post_intermediate_message is not None:
        obj = None
        default_serializer = None
        if isinstance(content, StreamingTextContent):
            obj = StreamingTextOutput(
                text=content.text,
                thread_id=thread_id,
            )
            default_serializer = serialize_streaming_text_output
        elif isinstance(content, StreamingAnnotationContent):
            match content.citation_type:
                case CitationType.URL_CITATION:
                    obj = StreamingAnnotationUrlOutput(
                        start_index=content.start_index, # type: ignore
                        end_index=content.end_index, # type: ignore
                        url=content.url, # type: ignore
                        title=content.title, # type: ignore
                        quote=content.quote, # type: ignore
                        thread_id=thread_id,
                    )
                    default_serializer = serialize_streaming_annotation_url_output
                case CitationType.FILE_CITATION:
                    obj = StreamingAnnotationFileOutput(
                        start_index=content.start_index, # type: ignore
                        end_index=content.end_index, # type: ignore
                        file_id=content.file_id, # type: ignore
                        quote=content.quote, # type: ignore
                        thread_id=thread_id,
                    )
                    default_serializer = serialize_streaming_annotation_file_output
                case _:
                    raise ValueError(f"Unknown citation type {content.citation_type}")
        elif isinstance(content, StreamingFileReferenceContent):
            obj = StreamingTextOutput(
                text=content.file_id, # type: ignore
                thread_id=thread_id,
            )
            default_serializer = serialize_streaming_text_output
        elif isinstance(content, str):
            try:
                obj = StreamingTextOutput(
                    text=content,
                    thread_id=thread_id,
                )
            except Exception as e:
                logger.error(f"Error creating StreamingTextOutput: {e}")
            default_serializer = serialize_streaming_text_output
        elif isinstance(content, StreamingSentinelOutput):
            obj = StreamingSentinelOutput(
                thread_id=content.thread_id,
            )
            default_serializer = serialize_streaming_sentinel_output
        else:
            logger.error(f"Unknown content type: {type(content)}")
            raise ValueError(f"Unknown content type: {type(content)}")

        await post_intermediate_message(json.dumps(
            obj=obj,
            default=default_serializer,
        ) + "\n")


async def post_beginning_info(title, message, post_intermediate_message):
    final_response = f"""
## {title}
{message}
"""
    logger.debug(final_response)

    await _post_intermediate_message(post_intermediate_message, final_response)

    await _post_intermediate_message(post_intermediate_message, StreamingSentinelOutput(thread_id=""))


async def post_intermediate_info(message, post_intermediate_message):
    await _post_intermediate_message(post_intermediate_message, message)

async def post_end_info(post_intermediate_message):
    await _post_intermediate_message(post_intermediate_message, StreamingSentinelOutput(thread_id=""))

async def post_error(title, exception, post_intermediate_message):
    final_response = f"""
***
**{title}**
{exception}
"""
    logger.error(final_response)

    await _post_intermediate_message(post_intermediate_message, final_response)

    await _post_intermediate_message(post_intermediate_message, StreamingSentinelOutput(thread_id=""))


async def print_on_intermediate_message(message: ChatMessageContent):
    for item in message.items or []:
        if isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        elif isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        else:
            print(f"{item}")


async def invoke_agent_stream(agent_name: str,
                              thread: AzureAIAgentThread,
                              message: str,
                              additional_instructions: str = "") -> AsyncIterable[Any]:
    agent_manager = get_create_agent_manager()

    agent = None
    for a in agent_manager:
        if a.name == agent_name:
            agent = a
            break

    if not agent:
        raise ValueError(f"{agent_name} not found.")

    try:
        async for response in agent.invoke_stream(
            thread=thread,
            messages=message,  # type: ignore
            on_intermediate_message=print_on_intermediate_message,
            additional_instructions=additional_instructions,
        ):
            #thread = response.thread

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
    "post_end_info",
    "post_error",
]
