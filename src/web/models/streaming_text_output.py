from typing import Any, Optional
from semantic_kernel.kernel_pydantic import KernelBaseModel

from models.chat_output import ChatOutput
from models.content_type_enum import ContentTypeEnum

class StreamingTextOutput(ChatOutput):
    text: str
    content_type: ContentTypeEnum = ContentTypeEnum.MARKDOWN


def deserialize_streaming_text_output(data: dict[str, Any]) -> StreamingTextOutput:
    """
    Deserialize a dictionary into a StreamingTextOutput instance.
    """
    if not isinstance(data, dict):
        raise TypeError("Input must be a dictionary.")
    text = data.get("text")
    thread_id = data.get("thread_id")
    if text is None:
        raise ValueError("'text' is required for deserialization.")
    if thread_id is None:
        raise ValueError("'thread_id' is required for deserialization.")
    # Remove keys that are explicitly passed
    extra_data = dict(data)
    extra_data.pop("text", None)
    extra_data.pop("thread_id", None)
    return StreamingTextOutput(text=text, thread_id=thread_id, **extra_data)

__all__ = ["StreamingTextOutput", "deserialize_streaming_text_output"]
