from semantic_kernel.kernel_pydantic import KernelBaseModel

class WriteTerraformStepParameters(KernelBaseModel):
    cloud_service_name: str = ""
    error_message: str = ""

__all__ = [
    "WriteTerraformStepParameters",
]
