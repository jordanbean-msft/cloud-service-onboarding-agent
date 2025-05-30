from typing import Any
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.models.chat_output import ChatOutput
from app.models.content_type_enum import ContentTypeEnum

class StreamingAnnotationUrlOutput(ChatOutput):
    start_index: int
    end_index: int
    url: str
    title: str
    content_type: ContentTypeEnum = ContentTypeEnum.ANNOTATION_URL

def serialize_streaming_annotation_url_output(streaming_annotation_url_output: StreamingAnnotationUrlOutput) -> dict[str, Any]:
    if isinstance(streaming_annotation_url_output, StreamingAnnotationUrlOutput):
        return {
            "content_type": streaming_annotation_url_output.content_type.value,
            "thread_id": streaming_annotation_url_output.thread_id,
            "start_index": streaming_annotation_url_output.start_index,
            "end_index": streaming_annotation_url_output.end_index,
            "url": streaming_annotation_url_output.url,
            "title": streaming_annotation_url_output.title,
        }
    raise TypeError


__all__ = ["StreamingAnnotationUrlOutput", "serialize_streaming_annotation_url_output"]
