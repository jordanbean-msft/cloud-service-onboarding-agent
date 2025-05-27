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

# class BuildAzurePolicyParameters(BaseModel):
#     cloud_service_name: str
#     error_message: str
#     public_documentation: str
#     internal_security_recommendations: str


class BuildAzurePolicyState(KernelBaseModel):
    chat_history: ChatHistory | None = None

# class BuildAzurePolicyOutput(BaseModel):
#     azure_policy: str
#     error_message: str


@kernel_process_step_metadata("BuildAzurePolicyStep")
class BuildAzurePolicyStep(KernelProcessStep[BuildAzurePolicyState]):
    state: BuildAzurePolicyState = Field(default_factory=BuildAzurePolicyState)  # type: ignore
    system_prompt: ClassVar[str] = """
You are a helpful assistant that builds Azure security policies. You will be given a cloud service name, public documentation, and internal security recommendations. Your job is to build an Azure Policy that is easy to integrate into a Terraform module. The policy should be based on the provided documentation and recommendations.
"""

    class Functions(StrEnum):
        BuildAzurePolicy = auto()

    class OutputEvents(StrEnum):
        BuildAzurePolicyComplete = auto()
        BuildAzurePolicyError = auto()

    async def activate(self, state: KernelProcessStepState[BuildAzurePolicyState]):
        self.state = state.state  # type: ignore
        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)

    @tracer.start_as_current_span(Functions.BuildAzurePolicy)
    @kernel_function(name=Functions.BuildAzurePolicy)
    # async def build_azure_policy(self, context: KernelProcessStepContext, params: BuildAzurePolicyParameters):
    async def build_azure_policy(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        logger.debug(f"Building Azure policy for cloud service: {params.cloud_service_name}")

        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)

        self.state.chat_history.add_user_message(
            f"Build Azure Policy for {params.cloud_service_name}. The public security recommendations are {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}."
        )  # type: ignore

        try:
            final_response = await call_agent(
                agent_name="cloud-security-agent",
                chat_history=self.state.chat_history,
                on_intermediate_message=on_intermediate_message
            )
        except Exception as e:
            final_response = f"Error writing Azure Policy: {e}"
            logger.error(f"Error writing Azure Policy: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.BuildAzurePolicyError,
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

        logger.debug(f"Building Azure Policy complete. Response: {final_response}")

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
            process_event=self.OutputEvents.BuildAzurePolicyComplete,
            data=CloudServiceOnboardingParameters(
                cloud_service_name=params.cloud_service_name,
                public_documentation=params.public_documentation,
                internal_security_recommendations=params.internal_security_recommendations,
                security_recommendations=params.security_recommendations,
                azure_policy=final_response,
                terraform_code=params.terraform_code,
                chat_history=params.chat_history,
                emit_event=params.emit_event
            )
        )


__all__ = [
    "BuildAzurePolicyStep",
    # "BuildAzurePolicyParameters",
    # "BuildAzurePolicyOutput",
]
