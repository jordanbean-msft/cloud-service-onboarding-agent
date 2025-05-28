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
                                                       on_intermediate_message, post_error, post_beginning_info, post_intermediate_info)

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


class MakeSecurityRecommendationsState(KernelBaseModel):
    chat_history: ChatHistory | None = None
    post_intermediate_message: Callable[[Any], Awaitable[None]] | None = None

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
You are a helpful assistant that makes security recommendations for cloud services. You will be given a cloud service name, public documentation, and internal security recommendations. Your job is to make security recommendations based on the provided documentation and recommendations. The recommendations should be comprehensive and actionable. These recommendations will be used to make an Azure Policy. Do not write the Azure Policy itself, just provide the recommendations that will be used to create the policy.
"""

    class Functions(StrEnum):
        MakeSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        MakeSecurityRecommendationsComplete = auto()
        MakeSecurityRecommendationsError = auto()

    @tracer.start_as_current_span(Functions.MakeSecurityRecommendations)
    @kernel_function(name=Functions.MakeSecurityRecommendations)
    async def make_security_recommendations(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        await post_beginning_info(title="Make Security Recommendations",
                        message=f"Running analysis on cloud service: {params.cloud_service_name}...",
                        post_intermediate_message=self.state.post_intermediate_message)

        try:
            if self.state.chat_history is None:
                self.state.chat_history = ChatHistory(system_message=self.system_prompt)

            self.state.chat_history.add_user_message(
                f"Make security recommendations for {params.cloud_service_name}. The public documentation is {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}."
            )  # type: ignore

            final_response = ""
            async for response in call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history,
                on_intermediate_message_param=on_intermediate_message
            ):
                final_response += response
                await post_intermediate_info(message=response,
                                             post_intermediate_message=self.state.post_intermediate_message)

            self.state.chat_history.add_assistant_message(final_response)  # type: ignore

            logger.info(f"Final security recommendations response: {final_response}")

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
