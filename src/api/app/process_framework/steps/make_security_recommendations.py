import asyncio
import logging
from opentelemetry import trace
from venv import logger
from enum import StrEnum, auto

from pydantic import BaseModel

from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.utilities import on_intermediate_message
from app.services.agents import get_create_agent_manager

logger  = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class MakeSecurityRecommendationsState(KernelBaseModel):
    security_recommendations: str

class MakeSecurityRecommendationsParameters(BaseModel):
    cloud_service_name: str
    public_documentation: str
    internal_security_recommendations: str

class MakeSecurityRecommendationsOutput(BaseModel):
    cloud_service_name: str
    error_message: str
    security_recommendations: str

@kernel_process_step_metadata("MakeSecurityRecommendationsStep")
class MakeSecurityRecommendationsStep(KernelProcessStep):
    class Functions(StrEnum):
        MakeSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        MakeSecurityRecommendationsComplete = auto()
        MakeSecurityRecommendationsError = auto()

    @tracer.start_as_current_span(Functions.MakeSecurityRecommendations)
    @kernel_function(name=Functions.MakeSecurityRecommendations)
    async def run_analysis(self, context: KernelProcessStepContext, params: MakeSecurityRecommendationsParameters):
        logger.debug(f"Running analysis on cloud service: {params.cloud_service_name}")
        
        agent_manager = get_create_agent_manager()
        
        agent = None
        for a in agent_manager:
            if a.name == "cloud-security-agent":
                agent = a
                break

        if not agent:
            return f"cloud-security-agent not found."

        self.state.chat_history.add_user_message(f"Make security recommendations for {params.cloud_service_name}. The public documentation is {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}.") # type: ignore

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
                process_event=self.OutputEvents.MakeSecurityRecommendationsError,
                data=MakeSecurityRecommendationsOutput(
                    cloud_service_name=params.cloud_service_name,
                    error_message=str(e),
                    security_recommendations=""
                )
            )

        logger.debug(f"Final response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response) # type: ignore

        await context.emit_event(
            process_event=self.OutputEvents.MakeSecurityRecommendationsComplete,
            data=MakeSecurityRecommendationsOutput(
                cloud_service_name=params.cloud_service_name,
                error_message="",
                security_recommendations=final_response
            )
        )

__all__ = [
    "MakeSecurityRecommendationsStep",
    "MakeSecurityRecommendationsParameters",
    "MakeSecurityRecommendationsOutput",
]