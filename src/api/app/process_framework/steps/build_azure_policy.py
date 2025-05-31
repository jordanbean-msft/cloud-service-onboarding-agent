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

from app.process_framework.models.build_azure_policy_step_parameters import \
    BuildAzurePolicyStepParameters
from app.process_framework.models.cloud_service_onboarding_state import CloudServiceOnboardingState
from app.process_framework.models.write_terraform_step_parameters import WriteTerraformStepParameters
from app.process_framework.utilities.utilities import (invoke_agent_stream,
                                                       post_beginning_info, post_end_info,
                                                       post_error,
                                                       post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

@kernel_process_step_metadata("BuildAzurePolicyStep")
class BuildAzurePolicyStep(KernelProcessStep[CloudServiceOnboardingState]):
    state: CloudServiceOnboardingState = Field(default_factory=CloudServiceOnboardingState)  # type: ignore
    additional_instructions: ClassVar[str] = """
You are a helpful assistant that builds Azure Policy security policies. You will be given a cloud service name, public documentation, and internal security recommendations. Your job is to build an Azure Policy that is easy to integrate into a Terraform module. The policy should be based on the provided documentation and recommendations. Make sure you read the internal security recommendations carefully and incorporate them into the policy. The policy should be comprehensive and follow best practices for Azure Policy. Do not write the Terraform yourself, just the Azure Policy that will be used to create the Terraform code. The Azure Policy should be in JSON format and follow the Azure Policy schema.
"""

    class Functions(StrEnum):
        BuildAzurePolicy = auto()

    class OutputEvents(StrEnum):
        BuildAzurePolicyComplete = auto()
        BuildAzurePolicyError = auto()

    @tracer.start_as_current_span(Functions.BuildAzurePolicy)
    @kernel_function(name=Functions.BuildAzurePolicy)
    async def build_azure_policy(self, context: KernelProcessStepContext, params: BuildAzurePolicyStepParameters):
        await post_beginning_info(title="Build Azure Policy",
                                  message=f"Building Azure policy for cloud service: {params.cloud_service_name}...\n",
                                  post_intermediate_message=self.state.post_intermediate_message)

        try:
            # ChatHistory is no longer used
            final_response = ""
            async for response in invoke_agent_stream(
                agent_name="cloud-security-agent",
                thread=self.state.thread, # type: ignore
                message=f"Build Azure Policy for {params.cloud_service_name}.",
                additional_instructions=self.additional_instructions
            ):
                if isinstance(response, StreamingTextContent):
                    final_response += response.text

                await post_intermediate_info(message=response,
                                            post_intermediate_message=self.state.post_intermediate_message)

            logger.debug(f"Final Azure Policy response: {final_response}")

            await context.emit_event(
                process_event=self.OutputEvents.BuildAzurePolicyComplete,
                data=WriteTerraformStepParameters(
                    cloud_service_name=params.cloud_service_name
                )
            )

            await post_end_info(post_intermediate_message=self.state.post_intermediate_message)

        except Exception as e:
            await post_error(title="Error writing Azure Policy",
                             exception=e,
                             post_intermediate_message=self.state.post_intermediate_message)

            await context.emit_event(
                process_event=self.OutputEvents.BuildAzurePolicyError,
                data=BuildAzurePolicyStepParameters(
                    cloud_service_name=params.cloud_service_name,
                    error_message=str(e)
                )
            )




__all__ = [
    "BuildAzurePolicyStep",
]
