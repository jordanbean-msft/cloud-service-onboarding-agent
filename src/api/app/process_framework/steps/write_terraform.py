import json
import logging
from enum import StrEnum, auto
from typing import Any, Awaitable, Callable, ClassVar

from opentelemetry import trace
from pydantic import Field
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep, KernelProcessStepContext, kernel_process_step_metadata)

from app.process_framework.models.cloud_service_onboarding_parameters import \
    CloudServiceOnboardingParameters
from app.process_framework.models.cloud_service_onboarding_state import CloudServiceOnboardingState
from app.process_framework.utilities.utilities import (call_agent,
                                                       post_beginning_info,
                                                       post_error,
                                                       post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


# class WriteTerraformState(KernelBaseModel):
#     chat_history: ChatHistory | None = None
#     post_intermediate_message: Callable[[Any], Awaitable[None]] | None = None


@kernel_process_step_metadata("WriteTerraformStep")
class WriteTerraformStep(KernelProcessStep[CloudServiceOnboardingState]):
    state: CloudServiceOnboardingState = Field(default_factory=CloudServiceOnboardingState)  # type: ignore

    system_prompt: ClassVar[str] = """
You are a helpful assistant that writes Terraform code for cloud services. You will be given a cloud service name, public documentation, internal security recommendations, and an Azure Policy. Your job is to write Terraform code that implements the Azure Policy and follows the recommendations. Do not write write code to deploy the cloud service itself, just the Terraform code that implements the Azure Policy. The Terraform code should be easy to integrate into a Terraform module and follow best practices for Terraform.
"""

    class Functions(StrEnum):
        WriteTerraform = auto()

    class OutputEvents(StrEnum):
        WriteTerraformComplete = auto()
        WriteTerraformError = auto()

    @tracer.start_as_current_span(Functions.WriteTerraform)
    @kernel_function(name=Functions.WriteTerraform)
    async def write_terraform(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        await post_beginning_info(title="Write Terraform",
                                  message=f"Writing Terraform for cloud service: {params.cloud_service_name}...\n",
                                  post_intermediate_message=self.state.post_intermediate_message)

        try:
            if self.state.chat_history is None:
                self.state.chat_history = ChatHistory(system_message=self.system_prompt)

            self.state.chat_history.add_user_message(
                f"Write Terraform code for deploying Azure Policy for the {params.cloud_service_name} service. The public documentation is {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}. The Azure Policy is {params.azure_policy}."
            )  # type: ignore

            final_response = ""
            async for response in call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history
            ):
                final_response += response
                await post_intermediate_info(message=response,
                                             post_intermediate_message=self.state.post_intermediate_message)

            self.state.chat_history.add_assistant_message(final_response)  # type: ignore

            logger.info(f"Final Terraform response: {final_response}")

            await context.emit_event(
                process_event=self.OutputEvents.WriteTerraformComplete,
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=params.public_documentation,
                    internal_security_recommendations=params.internal_security_recommendations,
                    security_recommendations=params.security_recommendations,
                    azure_policy=params.azure_policy,
                    terraform_code=final_response,
                )
            )
        except Exception as e:
            await post_error(title="Error writing Terraform",
                             exception=e,
                             post_intermediate_message=self.state.post_intermediate_message)

            await context.emit_event(
                process_event=self.OutputEvents.WriteTerraformError,
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=params.public_documentation,
                    internal_security_recommendations=params.internal_security_recommendations,
                    security_recommendations=params.security_recommendations,
                    azure_policy=params.azure_policy,
                    terraform_code=params.terraform_code,
                    error_message=str(e),
                )
            )


__all__ = [
    "WriteTerraformStep",
]
