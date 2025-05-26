import logging
from typing import ClassVar
from opentelemetry import trace
from enum import StrEnum, auto

from semantic_kernel import Kernel
from semantic_kernel.contents import FunctionCallContent, FunctionResultContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory, AuthorRole
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, kernel_process_step_metadata, KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.kernel_pydantic import KernelBaseModel
from pydantic import BaseModel, Field

from app.process_framework.models.cloud_service_onboarding_parameters import CloudServiceOnboardingParameters
from app.process_framework.utilities.utilities import on_intermediate_message
from app.services.agents import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

# class RetrieveInternalSecurityRecommendationsParameters(BaseModel):
#     cloud_service_name: str

class RetrieveInternalSecurityRecommendationsState(KernelBaseModel):
    chat_history: ChatHistory | None = None

# class RetrieveInternalSecurityRecommendationsOutput(BaseModel):
#     documentation: str
#     error_message: str

@kernel_process_step_metadata("RetrieveInternalSecurityRecommendationsStep")
class RetrieveInternalSecurityRecommendations(KernelProcessStep[RetrieveInternalSecurityRecommendationsState]):
    state: RetrieveInternalSecurityRecommendationsState = Field(default_factory=RetrieveInternalSecurityRecommendationsState)

    class Functions(StrEnum):
        RetrieveInternalSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        InternalSecurityRecommendationsRetrieved = auto()
        InternalSecurityRecommendationsError = auto()

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves internal security recommendations. Look in your documentation and find relevant documents related to the security message that you have received. Your job is not to interpret the results, just to find relevant documents.
"""

    async def activate(self, state: KernelProcessStepState[RetrieveInternalSecurityRecommendationsState]):
        self.state = state.state # type: ignore
        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)
        self.state.chat_history

    @tracer.start_as_current_span(Functions.RetrieveInternalSecurityRecommendations)
    @kernel_function(name=Functions.RetrieveInternalSecurityRecommendations)
    #async def retrieve_internal_security_recommendations(self, context: KernelProcessStepContext, params: RetrieveInternalSecurityRecommendationsParameters):
    async def retrieve_internal_security_recommendations(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        logger.debug(f"Retrieving internal security recommendations for: {params.cloud_service_name}")
        agent_manager = get_create_agent_manager()
        
        agent = None
        for a in agent_manager:
            if a.name == "cloud-security-agent":
                agent = a
                break

        if not agent:
            return f"cloud-security-agent not found."

        self.state.chat_history.add_user_message(f"Retrieve internal security recommendations for {params.cloud_service_name}.") # type: ignore

        final_response = ""
        try:
            async for response in agent.invoke(
                messages=self.state.chat_history.messages, # type: ignore
                on_intermediate_message=on_intermediate_message
            ): 
                final_response += response.content.content
        except Exception as e:
            final_response = f"Error retrieving internal security recommendations: {e}"
            logger.error(f"Error retrieving internal security recommendations: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.InternalSecurityRecommendationsError,
                # data=RetrieveInternalSecurityRecommendationsOutput(
                #     documentation="",
                #     error_message=str(e)
                # )
                data=CloudServiceOnboardingParameters(
                    cloud_service_name=params.cloud_service_name,
                    public_documentation=params.public_documentation,
                    internal_security_recommendations=params.internal_security_recommendations,
                    security_recommendations=params.security_recommendations,
                    azure_policy=params.azure_policy,
                    terraform_code=params.terraform_code,
                    chat_history=params.chat_history,
                    error_message=str(e),
                )
            )

        logger.debug(f"Final response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response) # type: ignore

        await context.emit_event(
            process_event=self.OutputEvents.InternalSecurityRecommendationsRetrieved,
            # data=RetrieveInternalSecurityRecommendationsOutput(
            #     documentation=final_response,
            #     error_message=""
            # )
            data=CloudServiceOnboardingParameters(
                cloud_service_name=params.cloud_service_name,
                public_documentation=params.public_documentation,
                internal_security_recommendations=final_response,
                security_recommendations=params.security_recommendations,
                azure_policy=params.azure_policy,
                terraform_code=params.terraform_code,
                chat_history=params.chat_history,
            )
        )

__all__ = [
    "RetrieveInternalSecurityRecommendations",
    "RetrieveInternalSecurityRecommendationsParameters",
    "RetrieveInternalSecurityRecommendationsOutput",
]