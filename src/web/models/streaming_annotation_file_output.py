from typing import Any, Optional
from semantic_kernel.kernel_pydantic import KernelBaseModel

from models.chat_output import ChatOutput
from models.content_type_enum import ContentTypeEnum

class StreamingAnnotationFileOutput(ChatOutput):
    start_index: int
    end_index: int
    file_id: str
    quote: str
    content_type: ContentTypeEnum = ContentTypeEnum.ANNOTATION_FILE


def deserialize_streaming_annotation_file_output(data: dict[str, Any]) -> StreamingAnnotationFileOutput:
    """
    Deserialize a dictionary into a StreamingAnnotationFileOutput instance.
    """
    if not isinstance(data, dict):
        raise TypeError("Input must be a dictionary.")
    start_index = data.get("start_index")
    end_index = data.get("end_index")
    file_id = data.get("file_id")
    quote = data.get("quote")
    thread_id = data.get("thread_id")
    # Remove keys that are explicitly passed
    extra_data = dict(data)
    for k in ("start_index", "end_index", "file_id", "quote", "thread_id"):
        extra_data.pop(k, None)
    return StreamingAnnotationFileOutput(start_index=start_index, end_index=end_index, file_id=file_id, quote=quote, thread_id=thread_id, **extra_data) # type: ignore


__all__ = ["StreamingAnnotationFileOutput", "deserialize_streaming_annotation_file_output"]
