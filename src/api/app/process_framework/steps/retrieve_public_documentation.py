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
    KernelProcessStep, KernelProcessStepContext,
    kernel_process_step_metadata)

from app.process_framework.models.cloud_service_onboarding_parameters import \
    CloudServiceOnboardingParameters
from app.process_framework.utilities.utilities import (call_agent,
                                                       on_intermediate_message, post_error, post_beginning_info, post_end_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class RetrievePublicDocumentationState(KernelBaseModel):
    chat_history: ChatHistory | None = None
    emit_event: Callable[[Any], Awaitable[None]] | None = None


@kernel_process_step_metadata("RetrievePublicDocumentationStep")
class RetrievePublicDocumentationStep(KernelProcessStep[RetrievePublicDocumentationState]):
    state: RetrievePublicDocumentationState = Field(  # type: ignore
        default_factory=RetrievePublicDocumentationState)

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves public security documentation for cloud services. You will be given a cloud service name. Your job is to find relevant security recommendations for the service you are provided. You will be given a list of internal security recommendations that will help you determine what public documentation to retrieve. The public documentation should be comprehensive and follow best practices for cloud security. The public documentation will be used to make an Azure Policy. Do not write the Azure Policy itself, just provide the public documentation that will be used to create the policy.
"""

    class Functions(StrEnum):
        RetrievePublicDocumentation = auto()

    class OutputEvents(StrEnum):
        RetrievePublicDocumentationComplete = auto()
        RetrievePublicDocumentationError = auto()

    @tracer.start_as_current_span(Functions.RetrievePublicDocumentation)
    @kernel_function(name=Functions.RetrievePublicDocumentation)
    async def retrieve_public_documentation(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        await post_beginning_info(title="Retrieve Public Documentation",
                        message=f"Retrieving public documentation for cloud service: {params.cloud_service_name}...",
                        emit_event=self.state.emit_event)

        try:
            if self.state.chat_history is None:
                self.state.chat_history = ChatHistory(system_message=self.system_prompt)

            self.state.chat_history.add_user_message(
                f"Retrieve public security documentation for {params.cloud_service_name}. The internal security recommendations are: {params.internal_security_recommendations}."
            )  # type: ignore

            final_response = await call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history,
                on_intermediate_message_param=on_intermediate_message
            )

            await post_end_info(message=f"""
Retrieve Public Documentation complete\n
{final_response}
""",
                                emit_event=self.state.emit_event)

            self.state.chat_history.add_assistant_message(final_response)  # type: ignore

            await context.emit_event(
                process_event=self.OutputEvents.RetrievePublicDocumentationComplete,
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=final_response,
                    internal_security_recommendations=params.internal_security_recommendations,
                    security_recommendations=params.security_recommendations,
                    azure_policy=params.azure_policy,
                    terraform_code=params.terraform_code,
                )
            )
        except Exception as e:
            await post_error(title="Error retrieving public documentation",
                             exception=e,
                             emit_event=self.state.emit_event)

            await context.emit_event(
                process_event=self.OutputEvents.RetrievePublicDocumentationError,
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
    "RetrievePublicDocumentationStep",
]
