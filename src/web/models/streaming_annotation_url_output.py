from typing import Any
from semantic_kernel.kernel_pydantic import KernelBaseModel

from models.chat_output import ChatOutput
from models.content_type_enum import ContentTypeEnum

class StreamingAnnotationUrlOutput(ChatOutput):
    start_index: int
    end_index: int
    url: str
    title: str
    content_type: ContentTypeEnum = ContentTypeEnum.ANNOTATION_URL

def deserialize_streaming_annotation_url_output(data: dict[str, Any]) -> StreamingAnnotationUrlOutput:
    """
    Deserialize a dictionary into a StreamingAnnotationUrlOutput instance.
    """
    if not isinstance(data, dict):
        raise TypeError("Input must be a dictionary.")
    start_index = data.get("start_index")
    end_index = data.get("end_index")
    url = data.get("url")
    title = data.get("title")
    thread_id = data.get("thread_id")
    # Validate required fields
    if start_index is None:
        raise ValueError("'start_index' is required for deserialization.")
    if end_index is None:
        raise ValueError("'end_index' is required for deserialization.")
    if url is None:
        raise ValueError("'url' is required for deserialization.")
    if title is None:
        raise ValueError("'title' is required for deserialization.")
    if thread_id is None:
        raise ValueError("'thread_id' is required for deserialization.")
    # Remove keys that are explicitly passed
    extra_data = dict(data)
    for k in ("start_index", "end_index", "url", "title", "thread_id"):
        extra_data.pop(k, None)
    return StreamingAnnotationUrlOutput(start_index=start_index, end_index=end_index, url=url, title=title, thread_id=thread_id, **extra_data)


__all__ = ["StreamingAnnotationUrlOutput", "deserialize_streaming_annotation_url_output"]
