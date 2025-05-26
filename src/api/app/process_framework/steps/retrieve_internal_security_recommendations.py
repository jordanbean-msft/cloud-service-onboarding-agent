import asyncio
import json
import logging
from typing import ClassVar
from opentelemetry import trace
from enum import StrEnum, auto

from pydantic import Field

from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatHistory

from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.process_framework.models.cloud_service_onboarding_parameters import CloudServiceOnboardingParameters
from app.process_framework.utilities.utilities import on_intermediate_message, call_agent

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class RetrieveInternalSecurityRecommendationsState(KernelBaseModel):
    chat_history: ChatHistory | None = None
    #queue: asyncio.Queue | None = None

@kernel_process_step_metadata("RetrieveInternalSecurityRecommendationsStep")
class RetrieveInternalSecurityRecommendationsStep(KernelProcessStep[RetrieveInternalSecurityRecommendationsState]):
    state: RetrieveInternalSecurityRecommendationsState = Field(default_factory=RetrieveInternalSecurityRecommendationsState) # type: ignore

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves internal security recommendations for cloud services. You will be given a cloud service name and public documentation. Your job is to retrieve any relevant internal security recommendations for the service.
"""

    class Functions(StrEnum):
        RetrieveInternalSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        RetrieveInternalSecurityRecommendationsComplete = auto()
        RetrieveInternalSecurityRecommendationsError = auto()

    async def activate(self, state: KernelProcessStepState[RetrieveInternalSecurityRecommendationsState]):
        self.state = state.state # type: ignore
        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)
        self.state.chat_history

    @tracer.start_as_current_span(Functions.RetrieveInternalSecurityRecommendations)
    @kernel_function(name=Functions.RetrieveInternalSecurityRecommendations)
    async def retrieve_internal_security_recommendations(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        logger.debug(f"Retrieving internal security recommendations for cloud service: {params.cloud_service_name}")

        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)

        self.state.chat_history.add_user_message(
            f"Retrieve internal security recommendations for {params.cloud_service_name}. The public documentation is {params.public_documentation}."
        ) # type: ignore

        try:
            final_response = await call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history,
                on_intermediate_message=on_intermediate_message
            )
        except Exception as e:
            final_response = f"Error retrieving internal security recommendations: {e}"
            logger.error(f"Error retrieving internal security recommendations: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.RetrieveInternalSecurityRecommendationsError,
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

        logger.debug(f"Retrieve Internal Security Recommendations complete. Response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response) # type: ignore
        
        await params.emit_event(json.dumps(
                        obj=ChatOutput(
                            content_type=ContentTypeEnum.MARKDOWN,
                            content=final_response,
                            thread_id="asdf",
                        ),
                        default=serialize_chat_output,
                    ) + "\n")

        await context.emit_event(
            process_event=self.OutputEvents.RetrieveInternalSecurityRecommendationsComplete,
            data=CloudServiceOnboardingParameters(
                cloud_service_name=params.cloud_service_name,
                public_documentation=params.public_documentation,
                internal_security_recommendations=final_response,
                security_recommendations=params.security_recommendations,
                azure_policy=params.azure_policy,
                terraform_code=params.terraform_code,
                chat_history=params.chat_history,
                emit_event=params.emit_event
            )
        )

__all__ = [
    "RetrieveInternalSecurityRecommendationsStep",
]