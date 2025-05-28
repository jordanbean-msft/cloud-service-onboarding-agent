import json
import logging

from opentelemetry import trace
from semantic_kernel.contents import (ChatHistory, ChatMessageContent,
                                      FunctionCallContent,
                                      FunctionResultContent)

from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.services.agents import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def post_emit_event(emit_event, content: str, thread_id: str = "asdf"):
    if emit_event is not None:
        await emit_event(json.dumps(
            obj=ChatOutput(
                content_type=ContentTypeEnum.MARKDOWN,
                content=content,
                thread_id=thread_id,
            ),
            default=serialize_chat_output,
        ) + "\n")

async def post_beginning_info(title, message, emit_event):
    final_response = f"""
***
## {title}
{message}
"""
    logger.info(final_response)

    await post_emit_event(emit_event, final_response)

async def post_end_info(message, emit_event):
    final_response = f"""
{message}
"""
    logger.info(final_response)

    await post_emit_event(emit_event, final_response)

async def post_error(title, exception, emit_event):
    final_response = f"""
***
**{title}**
{exception}
"""
    logger.error(final_response)

    await post_emit_event(emit_event, final_response)

async def on_intermediate_message(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            logger.debug(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            logger.debug(f"Function Result:> {item.result} for function: {item.name}")
        else:
            logger.debug(f"{message.role}: {message.content}")


async def call_agent(agent_name: str,
                     chat_history: ChatHistory,
                     on_intermediate_message_param) -> str:
    agent_manager = get_create_agent_manager()

    agent = None
    for a in agent_manager:
        if a.name == agent_name:
            agent = a
            break

    if not agent:
        return f"{agent_name} not found."

    final_response = ""
    try:
        async for response in agent.invoke(
            messages=chat_history.messages,  # type: ignore
            on_intermediate_message=on_intermediate_message_param
        ):
            final_response += response.content.content
    except Exception as e:
        logger.error(f"Error calling agent {agent_name}: {e}")
        raise

    logger.debug(f"Agent {agent_name} response: {final_response}")

    return final_response

__all__ = [
    "on_intermediate_message",
    "call_agent",
    "post_beginning_info",
    "post_end_info",
    "post_error",
]
