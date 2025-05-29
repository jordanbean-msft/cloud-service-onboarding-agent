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
    error_message: str = ""


__all__ = [
    "CloudServiceOnboardingParameters",
]
