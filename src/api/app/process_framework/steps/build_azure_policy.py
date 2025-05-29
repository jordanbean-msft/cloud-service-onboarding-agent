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
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent

from app.process_framework.models.cloud_service_onboarding_parameters import \
    CloudServiceOnboardingParameters
from app.process_framework.models.cloud_service_onboarding_state import CloudServiceOnboardingState
from app.process_framework.utilities.utilities import (invoke_agent_stream,
                                                       post_beginning_info,
                                                       post_error,
                                                       post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

# class BuildAzurePolicyParameters(BaseModel):
#     cloud_service_name: str
#     error_message: str
#     public_documentation: str
#     internal_security_recommendations: str


# class BuildAzurePolicyState(KernelBaseModel):
#     chat_history: ChatHistory | None = None
#     post_intermediate_message: Callable[[Any], Awaitable[None]] | None = None

# class BuildAzurePolicyOutput(BaseModel):
#     azure_policy: str
#     error_message: str


@kernel_process_step_metadata("BuildAzurePolicyStep")
class BuildAzurePolicyStep(KernelProcessStep[CloudServiceOnboardingState]):
    state: CloudServiceOnboardingState = Field(default_factory=CloudServiceOnboardingState)  # type: ignore
    system_prompt: ClassVar[str] = """
You are a helpful assistant that builds Azure Policy security policies. You will be given a cloud service name, public documentation, and internal security recommendations. Your job is to build an Azure Policy that is easy to integrate into a Terraform module. The policy should be based on the provided documentation and recommendations. Make sure you read the internal security recommendations carefully and incorporate them into the policy. The policy should be comprehensive and follow best practices for Azure Policy.
"""

    class Functions(StrEnum):
        BuildAzurePolicy = auto()

    class OutputEvents(StrEnum):
        BuildAzurePolicyComplete = auto()
        BuildAzurePolicyError = auto()

    @tracer.start_as_current_span(Functions.BuildAzurePolicy)
    @kernel_function(name=Functions.BuildAzurePolicy)
    async def build_azure_policy(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        await post_beginning_info(title="Build Azure Policy",
                                  message=f"Building Azure policy for cloud service: {params.cloud_service_name}...\n",
                                  post_intermediate_message=self.state.post_intermediate_message)

        try:
            if self.state.chat_history is None:
                self.state.chat_history = ChatHistory(system_message=self.system_prompt)

            self.state.chat_history.add_user_message(
                f"Build Azure Policy for {params.cloud_service_name}. The public security recommendations are {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}."
            )  # type: ignore

            final_response = ""
            async for response in invoke_agent_stream(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history,
            ):
                if isinstance(response, StreamingTextContent):
                    final_response += response.text

                await post_intermediate_info(message=response,
                                             post_intermediate_message=self.state.post_intermediate_message)

            self.state.chat_history.add_assistant_message(final_response)  # type: ignore

            logger.info(f"Final Azure Policy response: {final_response}")

            await context.emit_event(
                process_event=self.OutputEvents.BuildAzurePolicyComplete,
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=params.public_documentation,
                    internal_security_recommendations=params.internal_security_recommendations,
                    security_recommendations=params.security_recommendations,
                    azure_policy=final_response,
                    terraform_code=params.terraform_code,
                )
            )
        except Exception as e:
            await post_error(title="Error writing Azure Policy",
                             exception=e,
                             post_intermediate_message=self.state.post_intermediate_message)

            await context.emit_event(
                process_event=self.OutputEvents.BuildAzurePolicyError,
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
    "BuildAzurePolicyStep",
    # "BuildAzurePolicyParameters",
    # "BuildAzurePolicyOutput",
]
