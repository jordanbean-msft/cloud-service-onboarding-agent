import logging
import time
from typing import ClassVar
from opentelemetry import trace
from venv import logger
from enum import StrEnum, auto

from pydantic import Field
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatHistory

from app.process_framework.models.cloud_service_onboarding_parameters import CloudServiceOnboardingParameters
from app.process_framework.utilities.utilities import on_intermediate_message
from app.services.agents import get_create_agent_manager

logger  = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

# class RetrievePublicDocumentationParameters(KernelBaseModel):
#     cloud_service_name: str
#     internal_security_recommendations: str

class RetrievePublicDocumentationStepState(KernelBaseModel):
    chat_history: ChatHistory | None = None
    

# class RetrievePublicDocumentationOutput(KernelBaseModel):
#     public_documentation: str = ""
#     error_message: str = ""

@kernel_process_step_metadata("RetrievePublicDocumentationStep")
class RetrievePublicDocumentationStep(KernelProcessStep):
    state: RetrievePublicDocumentationStepState = Field(default_factory=RetrievePublicDocumentationStepState) # type: ignore

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves public documentation for cloud services. You will be given a cloud service name and internal security recommendations. Your job is to retrieve relevant public documentation based on the provided information.
You will need to search for relevant security recommendations based upon the internal security recommendations provided.
"""

    class Functions(StrEnum):
        RetrievePublicDocumentation = auto()

    class OutputEvents(StrEnum):
        PublicDocumentsRetrieved = auto()
        PublicDocumentsError = auto()

    async def activate(self, state: KernelProcessStepState[RetrievePublicDocumentationStepState]):
        self.state = state.state # type: ignore
        if self.state.chat_history is None:
            self.state.chat_history = ChatHistory(system_message=self.system_prompt)
        self.state.chat_history

    @tracer.start_as_current_span(Functions.RetrievePublicDocumentation)
    @kernel_function(name=Functions.RetrievePublicDocumentation)
    #async def retrieve_public_documentation(self, context: KernelProcessStepContext, params: RetrievePublicDocumentationParameters):
    async def retrieve_public_documentation(self, context: KernelProcessStepContext, params: CloudServiceOnboardingParameters):
        logger.debug(f"Retrieving public documentation for cloud service: {params.cloud_service_name}")

        agent_manager = get_create_agent_manager()
        
        agent = None
        for a in agent_manager:
            if a.name == "cloud-security-agent":
                agent = a
                break

        if not agent:
            return f"cloud-security-agent not found."

        self.state.chat_history.add_user_message(f"Retrieve public Azure security documentation for {params.cloud_service_name}. You will need to search for relevant security recommendations based upon {params.internal_security_recommendations}") # type: ignore

        final_response = ""
        try:
            async for response in agent.invoke(
                messages=self.state.chat_history.messages, # type: ignore
                on_intermediate_message=on_intermediate_message
            ): 
                final_response += response.content.content
        except Exception as e:
            final_response = f"Error retrieving public security documentation: {e}"
            logger.error(f"Error retrieving public security documentation: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.PublicDocumentsError,
                # data=RetrievePublicDocumentationOutput(
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
            process_event=self.OutputEvents.PublicDocumentsRetrieved,
            # data=RetrievePublicDocumentationOutput(
            #     public_documentation=final_response,
            #     error_message=""
            # )
            data=CloudServiceOnboardingParameters(
                cloud_service_name=params.cloud_service_name,
                public_documentation=final_response,
                internal_security_recommendations=params.internal_security_recommendations,
                security_recommendations=params.security_recommendations,
                azure_policy=params.azure_policy,
                terraform_code=params.terraform_code,
                chat_history=params.chat_history,
            )
        )

__all__ = [
    "RetrievePublicDocumentationStep",
    # "RetrievePublicDocumentationParameters",
    # "RetrievePublicDocumentationOutput",
]