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
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent

from app.process_framework.models.write_terraform_step_parameters import \
    WriteTerraformStepParameters
from app.process_framework.models.cloud_service_onboarding_state import CloudServiceOnboardingState
from app.process_framework.utilities.utilities import (invoke_agent_stream,
                                                       post_beginning_info, post_end_info,
                                                       post_error,
                                                       post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


@kernel_process_step_metadata("WriteTerraformStep")
class WriteTerraformStep(KernelProcessStep[CloudServiceOnboardingState]):
    state: CloudServiceOnboardingState = Field(default_factory=CloudServiceOnboardingState)  # type: ignore

    additional_instructions: ClassVar[str] = """
You are a helpful assistant that writes Terraform code for cloud services. You will be given a cloud service name, public documentation, internal security recommendations, and an Azure Policy. Your job is to write Terraform code that implements the Azure Policy and follows the recommendations. Do not write write code to deploy the cloud service itself, just the Terraform code that implements the Azure Policy. The Terraform code should be easy to integrate into a Terraform module and follow best practices for Terraform.
"""

    class Functions(StrEnum):
        WriteTerraform = auto()

    class OutputEvents(StrEnum):
        WriteTerraformComplete = auto()
        WriteTerraformError = auto()

    @tracer.start_as_current_span(Functions.WriteTerraform)
    @kernel_function(name=Functions.WriteTerraform)
    async def write_terraform(self, context: KernelProcessStepContext, params: WriteTerraformStepParameters):
        await post_beginning_info(title="Write Terraform",
                                  message=f"Writing Terraform...\n",
                                  post_intermediate_message=self.state.post_intermediate_message)

        try:
            final_response = ""
            async for response in invoke_agent_stream(
                agent_name="cloud-security-agent",
                thread=self.state.thread, # type: ignore
                message=f"Write Terraform code for deploying Azure Policy. User message: {params.cloud_service_name}.",
                additional_instructions=self.additional_instructions
            ):
                if isinstance(response, StreamingTextContent):
                    final_response += response.text

                await post_intermediate_info(message=response,
                                            post_intermediate_message=self.state.post_intermediate_message)

            logger.debug(f"Final Terraform response: {final_response}")

            await context.emit_event(
                process_event=self.OutputEvents.WriteTerraformComplete,
                data=WriteTerraformStepParameters(
                    cloud_service_name=params.cloud_service_name
                )
            )

            await post_end_info(post_intermediate_message=self.state.post_intermediate_message)
        except Exception as e:
            await post_error(title="Error writing Terraform",
                             exception=e,
                             post_intermediate_message=self.state.post_intermediate_message)

            await context.emit_event(
                process_event=self.OutputEvents.WriteTerraformError,
                data=WriteTerraformStepParameters(
                    cloud_service_name=params.cloud_service_name,
                    error_message=str(e)
                )
            )


__all__ = [
    "WriteTerraformStep",
]
