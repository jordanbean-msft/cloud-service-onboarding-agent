from typing import Any, Optional
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.models.chat_output import ChatOutput
from app.models.content_type_enum import ContentTypeEnum

class StreamingAnnotationFileOutput(ChatOutput):
    start_index: int
    end_index: int
    file_id: str
    quote: str
    content_type: ContentTypeEnum = ContentTypeEnum.ANNOTATION_FILE


def serialize_streaming_annotation_file_output(streaming_annotation_file_output: StreamingAnnotationFileOutput) -> dict[str, Any]:
    if isinstance(streaming_annotation_file_output, StreamingAnnotationFileOutput):
        return {
            "content_type": streaming_annotation_file_output.content_type.value,
            "thread_id": streaming_annotation_file_output.thread_id,
            "start_index": streaming_annotation_file_output.start_index,
            "end_index": streaming_annotation_file_output.end_index,
            "file_id": streaming_annotation_file_output.file_id,
            "quote": streaming_annotation_file_output.quote,
        }
    raise TypeError


__all__ = ["StreamingAnnotationFileOutput", "serialize_streaming_annotation_file_output"]
