from typing import Any, Awaitable, Callable

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgentThread

class CloudServiceOnboardingState(KernelBaseModel):
    thread: AzureAIAgentThread | None = None
    post_intermediate_message: Callable[[Any], Awaitable[None]] | None = None

__all__ = [
    "CloudServiceOnboardingState",
]
