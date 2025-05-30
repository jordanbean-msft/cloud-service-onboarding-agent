from typing import Any, Optional
from semantic_kernel.kernel_pydantic import KernelBaseModel

from models.chat_output import ChatOutput
from models.content_type_enum import ContentTypeEnum

class StreamingSentinelOutput(ChatOutput):
    content_type: ContentTypeEnum = ContentTypeEnum.SENTINEL

def deserialize_streaming_sentinel_output(data: dict[str, Any]) -> StreamingSentinelOutput:
    """
    Deserialize a dictionary into a StreamingSentinelOutput instance.
    """
    if not isinstance(data, dict):
        raise TypeError("Input must be a dictionary.")
    thread_id = data.get("thread_id")
    if thread_id is None:
        raise ValueError("'thread_id' is required for deserialization.")
    return StreamingSentinelOutput(thread_id=thread_id, **data)

__all__ = ["StreamingSentinelOutput", "deserialize_streaming_sentinel_output"]
