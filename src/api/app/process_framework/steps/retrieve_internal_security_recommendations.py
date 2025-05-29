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
from app.process_framework.utilities.utilities import (call_agent,
                                                       post_beginning_info,
                                                       post_error,
                                                       post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


# class RetrieveInternalSecurityRecommendationsState(KernelBaseModel):
#     chat_history: ChatHistory | None = None
#     post_intermediate_message: Callable[[Any], Awaitable[None]] | None = None


@kernel_process_step_metadata("RetrieveInternalSecurityRecommendationsStep")
class RetrieveInternalSecurityRecommendationsStep(KernelProcessStep[CloudServiceOnboardingState]):
    state: CloudServiceOnboardingState = Field(  # type: ignore
        default_factory=CloudServiceOnboardingState)

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves internal security recommendations for cloud services. You will be given a cloud service name. Your job is to retrieve any relevant internal security recommendations for the service. Make sure and follow links to find additional information. The internal security recommendations should be comprehensive and follow best practices for cloud security. These recommendations will be used to make an Azure Policy. Do not write the Azure Policy itself, just provide the internal security recommendations that will be used to create the policy. The recommendations should be actionable and include specifics, not links to other documentation.
"""

    class Functions(StrEnum):
        RetrieveInternalSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        RetrieveInternalSecurityRecommendationsComplete = auto()
        RetrieveInternalSecurityRecommendationsError = auto()

    @tracer.start_as_current_span(Functions.RetrieveInternalSecurityRecommendations)
    @kernel_function(name=Functions.RetrieveInternalSecurityRecommendations)
    async def retrieve_internal_security_recommendations(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        await post_beginning_info(title="Retrieve Internal Security Recommendations",
                                  message=f"Retrieving internal security recommendations for cloud service: {params.cloud_service_name}...\n",
                                  post_intermediate_message=self.state.post_intermediate_message)
        try:
            if self.state.chat_history is None:
                self.state.chat_history = ChatHistory(system_message=self.system_prompt)

            self.state.chat_history.add_user_message(
                f"Retrieve internal security recommendations for {params.cloud_service_name}."
            )  # type: ignore

            final_response = ""
            async for response in call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history
            ):
                #if isinstance(response, StreamingTextContent):
                final_response += response

                await post_intermediate_info(message=response,
                                             post_intermediate_message=self.state.post_intermediate_message)

            self.state.chat_history.add_assistant_message(final_response)  # type: ignore

            logger.info(f"Final internal security recommendations response: {final_response}")

            await context.emit_event(
                process_event=self.OutputEvents.RetrieveInternalSecurityRecommendationsComplete,
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=params.public_documentation,
                    internal_security_recommendations=final_response,
                    security_recommendations=params.security_recommendations,
                    azure_policy=params.azure_policy,
                    terraform_code=params.terraform_code,
                )
            )
        except Exception as e:
            await post_error(title="Error retrieving internal security recommendations",
                             exception=e,
                             post_intermediate_message=self.state.post_intermediate_message)

            await context.emit_event(
                process_event=self.OutputEvents.RetrieveInternalSecurityRecommendationsError,
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
    "RetrieveInternalSecurityRecommendationsStep",
]
