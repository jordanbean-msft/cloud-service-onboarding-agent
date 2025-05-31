import logging
from enum import StrEnum, auto
from typing import Any, Awaitable, Callable, ClassVar

from numpy import add
from opentelemetry import trace
from pydantic import Field
from semantic_kernel.contents import (AnnotationContent,
                                      ChatMessageContent, FileReferenceContent,
                                      TextContent)
from semantic_kernel.contents.streaming_annotation_content import \
    StreamingAnnotationContent
from semantic_kernel.contents.streaming_file_reference_content import \
    StreamingFileReferenceContent
from semantic_kernel.contents.streaming_text_content import \
    StreamingTextContent
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep, KernelProcessStepContext, kernel_process_step_metadata)

from app.process_framework.models.build_azure_policy_step_parameters import BuildAzurePolicyStepParameters
from app.process_framework.models.make_security_recommendations_step_parameters import \
    MakeSecurityRecommendationsStepParameters
from app.process_framework.models.cloud_service_onboarding_state import \
    CloudServiceOnboardingState
from app.process_framework.utilities.utilities import (invoke_agent_stream,
                                                       post_beginning_info, post_end_info,
                                                       post_error,
                                                       post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

@kernel_process_step_metadata("MakeSecurityRecommendationsStep")
class MakeSecurityRecommendationsStep(KernelProcessStep[CloudServiceOnboardingState]):
    state: CloudServiceOnboardingState = Field(  # type: ignore
        default_factory=CloudServiceOnboardingState)

    additional_instructions: ClassVar[str] = """
You are a helpful assistant that makes security recommendations for cloud services. You will be given a cloud service name. Your job is to make security recommendations based on the provided documentation and recommendations. The recommendations should be comprehensive and actionable.

MAKE SURE AND USE THE FILE SEARCH TOOL TO SEARCH FOR INTERNAL SECURITY RECOMMENDATIONS. The internal security recommendations should be comprehensive and follow best practices for cloud security. ALWAYS include references to the internal documentation.

MAKE SURE AND USE THE BING CUSTOM SEARCH TOOL TO SEARCH FOR PUBLIC DOCUMENTATION. You will be given a list of internal security recommendations that will help you determine what public documentation to retrieve. The public documentation should be comprehensive and follow best practices for cloud security. ALWAYS include references to the public documentation.

You should use internal security recommendations to help you determine what public documentation to retrieve. The public documentation should be comprehensive and follow best practices for cloud security. You will also need to search public documents to find specific security recommendations for that service. Make sure and do lookups for each item in the internal security recommendations to ensure you provide relevant documentation for each item. If you cannot find documentation for a specific item, please indicate that in your response. Be sure to check and see if there are already existing Azure Policies; if so, you should retrieve those examples.

These recommendations will be used to make an Azure Policy. Do not write the Azure Policy itself, just provide the recommendations that will be used to create the policy.
"""

    class Functions(StrEnum):
        MakeSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        MakeSecurityRecommendationsComplete = auto()
        MakeSecurityRecommendationsError = auto()

    @tracer.start_as_current_span(Functions.MakeSecurityRecommendations)
    @kernel_function(name=Functions.MakeSecurityRecommendations)
    async def make_security_recommendations(self, context: KernelProcessStepContext, params: MakeSecurityRecommendationsStepParameters):
        await post_beginning_info(title="Make Security Recommendations",
                                  message=f"Running analysis on cloud service: {params.cloud_service_name}...\n",
                                  post_intermediate_message=self.state.post_intermediate_message)

        try:
            final_response = ""
            async for response in invoke_agent_stream(
                agent_name="cloud-security-agent",
                thread=self.state.thread, # type: ignore
                message=f"Make security recommendations for {params.cloud_service_name}.",
                additional_instructions=self.additional_instructions
            ):
                if isinstance(response, StreamingTextContent):
                    final_response += response.text

                await post_intermediate_info(message=response,
                                             post_intermediate_message=self.state.post_intermediate_message)

            logger.debug(f"Making security recommendations response: {final_response}")

            await context.emit_event(
                process_event=self.OutputEvents.MakeSecurityRecommendationsComplete,
                data=BuildAzurePolicyStepParameters(
                    cloud_service_name=params.cloud_service_name
                )
            )

            await post_end_info(post_intermediate_message=self.state.post_intermediate_message)
        except Exception as e:
            await post_error(title="Error making security recommendations",
                             exception=e,
                             post_intermediate_message=self.state.post_intermediate_message)

            await context.emit_event(
                process_event=self.OutputEvents.MakeSecurityRecommendationsError,
                data=MakeSecurityRecommendationsStepParameters(
                    cloud_service_name=params.cloud_service_name,
                    error_message=str(e)
                )
            )


__all__ = [
    "MakeSecurityRecommendationsStep",
]
