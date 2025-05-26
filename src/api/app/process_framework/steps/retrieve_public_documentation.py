import logging
import time
from opentelemetry import trace
from venv import logger
from enum import StrEnum, auto

from pydantic import Field
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.steps.make_security_recommendations import MakeSecurityRecommendationsParameters
from app.process_framework.utilities import on_intermediate_message
from app.services.agents import get_create_agent_manager

logger  = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class RetrievePublicDocumentationParameters(KernelBaseModel):
    cloud_service_name: str
    internal_security_recommendations: str

class RetrievePublicDocumentationStepState(KernelBaseModel):
    public_documentation: str = ""

class RetrievePublicDocumentationOutput(KernelBaseModel):
    public_documentation: str = ""
    error_message: str = ""

@kernel_process_step_metadata("RetrievePublicDocumentationStep")
class RetrievePublicDocumentationStep(KernelProcessStep):
    state: RetrievePublicDocumentationStepState = Field(default_factory=RetrievePublicDocumentationStepState) # type: ignore

    class Functions(StrEnum):
        RetrievePublicDocumentation = auto()

    class OutputEvents(StrEnum):
        PublicDocumentsRetrieved = auto()
        PublicDocumentsError = auto()

    async def activate(self, state: KernelProcessStepState[RetrievePublicDocumentationStepState]):
        self.state = state.state # type: ignore

    @tracer.start_as_current_span(Functions.RetrievePublicDocumentation)
    @kernel_function(name=Functions.RetrievePublicDocumentation)
    async def retrieve_public_documentation(self, context: KernelProcessStepContext, params: RetrievePublicDocumentationParameters):
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
            final_response = f"Error retrieving security documentation: {e}"
            logger.error(f"Error retrieving security documentation: {e}")
            await context.emit_event(
                process_event=self.OutputEvents.PublicDocumentsError,
                data=RetrievePublicDocumentationOutput(
                    error_message=str(e)
                )
            )

        logger.debug(f"Final response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response) # type: ignore

        await context.emit_event(
            process_event=self.OutputEvents.PublicDocumentsRetrieved,
            data=RetrievePublicDocumentationOutput(
                public_documentation=final_response,
                error_message=""
            )
        )

__all__ = [
    "RetrievePublicDocumentationStep",
    "RetrievePublicDocumentationParameters",
    "RetrievePublicDocumentationOutput",
]