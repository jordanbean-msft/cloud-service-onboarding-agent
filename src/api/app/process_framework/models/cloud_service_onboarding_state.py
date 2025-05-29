from typing import Any, Awaitable, Callable

from semantic_kernel.contents import ChatHistory
from semantic_kernel.kernel_pydantic import KernelBaseModel

class CloudServiceOnboardingState(KernelBaseModel):
    chat_history: ChatHistory | None = None
    post_intermediate_message: Callable[[Any], Awaitable[None]] | None = None

__all__ = [
    "CloudServiceOnboardingState",
]
