import logging
from opentelemetry import trace

from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def on_intermediate_message(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            logger.debug(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            logger.debug(f"Function Result:> {item.result} for function: {item.name}")
        else:
            logger.debug(f"{message.role}: {message.content}")

__all__ = [
    "on_intermediate_message",
]