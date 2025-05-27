import json
import logging
from enum import StrEnum, auto
from typing import ClassVar
from venv import logger

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


class MakeSecurityRecommendationsState(KernelBaseModel):
    chat_history: ChatHistory | None = None

# class MakeSecurityRecommendationsParameters(BaseModel):
#     cloud_service_name: str
#     public_documentation: str
#     internal_security_recommendations: str

# class MakeSecurityRecommendationsOutput(BaseModel):
#     cloud_service_name: str
#     error_message: str
#     security_recommendations: str


@kernel_process_step_metadata("MakeSecurityRecommendationsStep")
class MakeSecurityRecommendationsStep(KernelProcessStep):
    state: MakeSecurityRecommendationsState = Field(
        default_factory=MakeSecurityRecommendationsState)  # type: ignore

    system_prompt: ClassVar[str] = """
You are a helpful assistant that makes security recommendations for cloud services. You will be given a cloud service name, public documentation, and internal security recommendations. Your job is to make security recommendations based on the provided documentation and recommendations. The recommendations should be comprehensive and actionable.
"""

    class Functions(StrEnum):
        MakeSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        MakeSecurityRecommendationsComplete = auto()
        MakeSecurityRecommendationsError = auto()

    async def activate(self, state: KernelProcessStepState[MakeSecurityRecommendationsState]):
        self.state = state.state  # type: ignore
        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)

    @tracer.start_as_current_span(Functions.MakeSecurityRecommendations)
    @kernel_function(name=Functions.MakeSecurityRecommendations)
    async def make_security_recommendations(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        logger.debug(f"Running analysis on cloud service: {params.cloud_service_name}")

        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)

        self.state.chat_history.add_user_message(
            f"Make security recommendations for {params.cloud_service_name}. The public documentation is {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}."
        )  # type: ignore

        try:
            final_response = await call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history,
                on_intermediate_message=on_intermediate_message
            )
        except Exception as e:
            final_response = f"Error making security recommendations: {e}"
            logger.error(f"Error making security recommendations: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.MakeSecurityRecommendationsError,
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

        logger.debug(f"Make Security Recommendations complete. Response: {final_response}")

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
            process_event=self.OutputEvents.MakeSecurityRecommendationsComplete,
            data=CloudServiceOnboardingParameters(
                cloud_service_name=params.cloud_service_name,
                public_documentation=params.public_documentation,
                internal_security_recommendations=params.internal_security_recommendations,
                security_recommendations=final_response,
                azure_policy=params.azure_policy,
                terraform_code=params.terraform_code,
                chat_history=params.chat_history,
                emit_event=params.emit_event
            )
        )


__all__ = [
    "MakeSecurityRecommendationsStep",
    # "MakeSecurityRecommendationsParameters",
    # "MakeSecurityRecommendationsOutput",
]
