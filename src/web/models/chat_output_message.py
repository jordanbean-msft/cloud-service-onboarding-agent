from semantic_kernel.kernel_pydantic import KernelBaseModel

from models.content_type_enum import ContentTypeEnum


class ChatOutputMessage(KernelBaseModel):
    content_type: ContentTypeEnum
    content: str


__all__ = ["ChatOutputMessage"]
