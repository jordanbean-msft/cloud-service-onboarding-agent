import json
import logging
from enum import StrEnum, auto
from typing import ClassVar

from opentelemetry import trace
from pydantic import Field
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep, KernelProcessStepContext, KernelProcessStepState,
    kernel_process_step_metadata)

from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.process_framework.models.cloud_service_onboarding_parameters import \
    CloudServiceOnboardingParameters
from app.process_framework.utilities.utilities import (call_agent,
                                                       on_intermediate_message)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class RetrievePublicDocumentationState(KernelBaseModel):
    chat_history: ChatHistory | None = None


@kernel_process_step_metadata("RetrievePublicDocumentationStep")
class RetrievePublicDocumentationStep(KernelProcessStep[RetrievePublicDocumentationState]):
    state: RetrievePublicDocumentationState = Field(
        default_factory=RetrievePublicDocumentationState)  # type: ignore

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves public documentation for cloud services. You will be given a cloud service name. Your job is to find and summarize the most relevant public documentation for that service.
"""

    class Functions(StrEnum):
        RetrievePublicDocumentation = auto()

    class OutputEvents(StrEnum):
        RetrievePublicDocumentationComplete = auto()
        RetrievePublicDocumentationError = auto()

    async def activate(self, state: KernelProcessStepState[RetrievePublicDocumentationState]):
        self.state = state.state  # type: ignore
        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)

    @tracer.start_as_current_span(Functions.RetrievePublicDocumentation)
    @kernel_function(name=Functions.RetrievePublicDocumentation)
    async def retrieve_public_documentation(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        logger.debug(
            f"Retrieving public documentation for cloud service: {params.cloud_service_name}")

        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)

        self.state.chat_history.add_user_message(
            f"Retrieve and summarize public documentation for {params.cloud_service_name}."
        )  # type: ignore

        try:
            final_response = await call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history,
                on_intermediate_message=on_intermediate_message
            )
        except Exception as e:
            final_response = f"Error retrieving public documentation: {e}"
            logger.error(f"Error retrieving public documentation: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.RetrievePublicDocumentationError,
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=params.public_documentation,
                    internal_security_recommendations=params.internal_security_recommendations,
                    security_recommendations=params.security_recommendations,
                    azure_policy=params.azure_policy,
                    terraform_code=params.terraform_code,
                    chat_history=params.chat_history,
                    error_message=str(e),
                    emit_event=params.emit_event
                )
            )
            return

        logger.debug(f"Retrieve Public Documentation complete. Response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response)  # type: ignore

        await params.emit_event(json.dumps(
            obj=ChatOutput(
                content_type=ContentTypeEnum.MARKDOWN,
                content=final_response,
                thread_id="asdf",
            ),
            default=serialize_chat_output,
        ) + "\n")

        await context.emit_event(
            process_event=self.OutputEvents.RetrievePublicDocumentationComplete,
            data=CloudServiceOnboardingParameters(
                cloud_service_name=params.cloud_service_name,
                public_documentation=final_response,
                internal_security_recommendations=params.internal_security_recommendations,
                security_recommendations=params.security_recommendations,
                azure_policy=params.azure_policy,
                terraform_code=params.terraform_code,
                chat_history=params.chat_history,
                emit_event=params.emit_event
            )
        )


__all__ = [
    "RetrievePublicDocumentationStep",
]
