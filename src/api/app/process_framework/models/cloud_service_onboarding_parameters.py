from collections.abc import Callable
from typing import Any

from semantic_kernel.contents import ChatHistory
from semantic_kernel.kernel_pydantic import KernelBaseModel


class CloudServiceOnboardingParameters(KernelBaseModel):
    cloud_service_name: str = ""
    public_documentation: str = ""
    internal_security_recommendations: str = ""
    security_recommendations: str = ""
    azure_policy: str = ""
    terraform_code: str = ""
    # chat_history: ChatHistory = ChatHistory()
    error_message: str = ""
    # emit_event: Callable[..., Any] = lambda x: None  # Default to a no-op function


__all__ = [
    "CloudServiceOnboardingParameters",
]
