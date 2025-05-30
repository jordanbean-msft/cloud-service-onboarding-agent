from typing import Any
from semantic_kernel.kernel_pydantic import KernelBaseModel

from models.content_type_enum import ContentTypeEnum

class ChatOutput(KernelBaseModel):
    content_type: ContentTypeEnum
    thread_id: str

def deserialize_chat_output(data: dict[str, Any]) -> ChatOutput:
    """
    Deserialize a dictionary into a ChatOutput instance.
    """
    if not isinstance(data, dict):
        raise TypeError("Input must be a dictionary.")
    content_type = data.get("content_type")
    thread_id = data.get("thread_id")
    return ChatOutput(content_type=content_type, thread_id=thread_id) # type: ignore

__all__ = ["ChatOutput"]
