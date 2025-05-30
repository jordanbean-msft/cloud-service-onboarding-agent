from typing import Any, Optional
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.models.chat_output import ChatOutput
from app.models.content_type_enum import ContentTypeEnum

class StreamingSentinelOutput(ChatOutput):
    content_type: ContentTypeEnum = ContentTypeEnum.SENTINEL


def serialize_streaming_sentinel_output(streaming_sentinel_output: StreamingSentinelOutput) -> dict[str, Any]:
    if isinstance(streaming_sentinel_output, StreamingSentinelOutput):
        return {
            "content_type": streaming_sentinel_output.content_type.value,
            "thread_id": streaming_sentinel_output.thread_id,
        }
    raise TypeError

__all__ = ["StreamingSentinelOutput", "serialize_streaming_sentinel_output"]
