from semantic_kernel.kernel_pydantic import KernelBaseModel


class ChatGetFileNameOutput(KernelBaseModel):
    file_id: str
    file_name: str


__all__ = ["ChatGetFileNameOutput"]
