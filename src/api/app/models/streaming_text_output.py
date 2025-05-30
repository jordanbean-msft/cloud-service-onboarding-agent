from typing import Any, Optional
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.models.chat_output import ChatOutput
from app.models.content_type_enum import ContentTypeEnum

class StreamingTextOutput(ChatOutput):
    text: str
    content_type: ContentTypeEnum = ContentTypeEnum.MARKDOWN


def serialize_streaming_text_output(streaming_text_output: StreamingTextOutput) -> dict[str, Any]:
    if isinstance(streaming_text_output, StreamingTextOutput):
        return {
            "content_type": streaming_text_output.content_type.value,
            "thread_id": streaming_text_output.thread_id,
            "text": streaming_text_output.text,
        }
    raise TypeError

__all__ = ["StreamingTextOutput", "serialize_streaming_text_output"]
