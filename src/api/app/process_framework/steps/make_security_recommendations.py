import logging
from enum import StrEnum, auto
from typing import Any, Awaitable, Callable, ClassVar

from numpy import add
from opentelemetry import trace
from pydantic import Field
from semantic_kernel.contents import (AnnotationContent, ChatHistory,
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

from app.process_framework.models.cloud_service_onboarding_parameters import \
    CloudServiceOnboardingParameters
from app.process_framework.models.cloud_service_onboarding_state import \
    CloudServiceOnboardingState
from app.process_framework.utilities.utilities import (invoke_agent,
                                                       invoke_agent_stream,
                                                       post_beginning_info, post_end_info,
                                                       post_error,
                                                       post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


# class MakeSecurityRecommendationsState(KernelBaseModel):
#     chat_history: ChatHistory | None = None
#     post_intermediate_message: Callable[[Any], Awaitable[None]] | None = None

# class MakeSecurityRecommendationsParameters(BaseModel):
#     cloud_service_name: str
#     public_documentation: str
#     internal_security_recommendations: str

# class MakeSecurityRecommendationsOutput(BaseModel):
#     cloud_service_name: str
#     error_message: str
#     security_recommendations: str


@kernel_process_step_metadata("MakeSecurityRecommendationsStep")
class MakeSecurityRecommendationsStep(KernelProcessStep[CloudServiceOnboardingState]):
    state: CloudServiceOnboardingState = Field(  # type: ignore
        default_factory=CloudServiceOnboardingState)

    additional_instructions: ClassVar[str] = """
You are a helpful assistant that makes security recommendations for cloud services. You will be given a cloud service name. Your job is to make security recommendations based on the provided documentation and recommendations. The recommendations should be comprehensive and actionable.

MAKE SURE AND USE THE BING CUSTOM SEARCH TOOL TO SEARCH FOR PUBLIC DOCUMENTATION. You will be given a list of internal security recommendations that will help you determine what public documentation to retrieve. The public documentation should be comprehensive and follow best practices for cloud security.

You will also need to search public documents to find specific security recommendations for that service. You should use internal security recommendations to help you determine what public documentation to retrieve. The public documentation should be comprehensive and follow best practices for cloud security. Make sure and do lookups for each item in the internal security recommendations to ensure you provide relevant documentation for each item. If you cannot find documentation for a specific item, please indicate that in your response. Be sure to check and see if there are already existing Azure Policies; if so, you should retrieve those examples.

These recommendations will be used to make an Azure Policy. Do not write the Azure Policy itself, just provide the recommendations that will be used to create the policy.
"""
#     system_prompt: ClassVar[str] = """
# You are a helpful assistant that makes security recommendations for cloud services. You will be given a cloud service name, public documentation, and internal security recommendations. Your job is to make security recommendations based on the provided documentation and recommendations. The recommendations should be comprehensive and actionable. These recommendations will be used to make an Azure Policy. Do not write the Azure Policy itself, just provide the recommendations that will be used to create the policy.
# """

    class Functions(StrEnum):
        MakeSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        MakeSecurityRecommendationsComplete = auto()
        MakeSecurityRecommendationsError = auto()

    @tracer.start_as_current_span(Functions.MakeSecurityRecommendations)
    @kernel_function(name=Functions.MakeSecurityRecommendations)
    async def make_security_recommendations(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        await post_beginning_info(title="Make Security Recommendations",
                                  message=f"Running analysis on cloud service: {params.cloud_service_name}...\n",
                                  post_intermediate_message=self.state.post_intermediate_message)

        try:
            #self.state.chat_history = ChatHistory(system_message=self.additional_instructions)

            self.state.chat_history.add_user_message( # type: ignore
                #f"Make security recommendations for {params.cloud_service_name}. The public documentation is {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}."
                f"Make security recommendations for {params.cloud_service_name}. The internal security recommendations are: {params.internal_security_recommendations}."
            )  # type: ignore

            final_response = ""
            annotations = []
            file_references = []
            async for response in invoke_agent_stream(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history, # type: ignore
                additional_instructions=self.additional_instructions
            ):
                if isinstance(response, StreamingTextContent):
                    final_response += response.text
                    await post_intermediate_info(message=response,
                                                 post_intermediate_message=self.state.post_intermediate_message)
                elif isinstance(response, StreamingAnnotationContent):
                    annotations.append(response)
                elif isinstance(response, StreamingFileReferenceContent):
                    file_references.append(response)

            for annotation in annotations:
                await post_intermediate_info(message=annotation,
                                             post_intermediate_message=self.state.post_intermediate_message)

            for file_reference in file_references:
                await post_intermediate_info(message=file_reference,
                                             post_intermediate_message=self.state.post_intermediate_message)

            self.state.chat_history.add_assistant_message(final_response)  # type: ignore

            logger.info(f"Making security recommendations response: {final_response}")

            await context.emit_event(
                process_event=self.OutputEvents.MakeSecurityRecommendationsComplete,
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=params.public_documentation,
                    internal_security_recommendations=params.internal_security_recommendations,
                    security_recommendations=final_response,
                    azure_policy=params.azure_policy,
                    terraform_code=params.terraform_code,
                )
            )

            await post_end_info(post_intermediate_message=self.state.post_intermediate_message)
        except Exception as e:
            await post_error(title="Error making security recommendations",
                             exception=e,
                             post_intermediate_message=self.state.post_intermediate_message)

            await context.emit_event(
                process_event=self.OutputEvents.MakeSecurityRecommendationsError,
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
    "MakeSecurityRecommendationsStep",
    # "MakeSecurityRecommendationsParameters",
    # "MakeSecurityRecommendationsOutput",
]
