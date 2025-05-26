import asyncio
from typing import ClassVar
import logging
from opentelemetry import trace
from enum import StrEnum, auto

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
#from semantic_kernel.processes.local_runtime import KernelProcessEvent, start
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.utilities import on_intermediate_message
from app.services.agents import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class BuildAzurePolicyParameters(BaseModel):
    cloud_service_name: str
    error_message: str
    public_documentation: str
    internal_security_recommendations: str

class BuildAzurePolicyState(KernelBaseModel):
    final_answer: str = ""

class BuildAzurePolicyOutput(BaseModel):
    azure_policy: str
    error_message: str

@kernel_process_step_metadata("BuildAzurePolicyStep")
class BuildAzurePolicyStep(KernelProcessStep[BuildAzurePolicyState]):
    state: BuildAzurePolicyState = Field(default_factory=BuildAzurePolicyState) # type: ignore

    class Functions(StrEnum):
        BuildAzurePolicy = auto()

    class OutputEvents(StrEnum):
        BuildAzurePolicyComplete = auto()
        BuildAzurePolicyError = auto()

    async def activate(self, state: KernelProcessStepState[BuildAzurePolicyState]):
        self.state = state.state # type: ignore

    @tracer.start_as_current_span(Functions.BuildAzurePolicy)
    @kernel_function(name=Functions.BuildAzurePolicy)
    async def build_azure_policy(self, context: KernelProcessStepContext, params: BuildAzurePolicyParameters):
        logger.debug(f"Building Azure policy for cloud service: {params.cloud_service_name}")

        agent_manager = get_create_agent_manager()
        
        agent = None
        for a in agent_manager:
            if a.name == "cloud-security-agent":
                agent = a
                break

        if not agent:
            return f"cloud-security-agent not found."

        self.state.chat_history.add_user_message(f"Build Azure Policy for {params.cloud_service_name}. The public security recommendations are {params.public_documentation}. The internal security recommendations are {params.internal_security_recommendations}. This Azure Policy needs to be easy to integrate into a Terraform module.") # type: ignore

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
                process_event=self.OutputEvents.BuildAzurePolicyError,
                data=BuildAzurePolicyOutput(
                    azure_policy="",
                    error_message=str(e)
                )
            )

        logger.debug(f"Final response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response) # type: ignore

        self.state.final_answer = f"Final recommendation for cloud service: {params.cloud_service_name}"

        await context.emit_event(
                process_event=self.OutputEvents.BuildAzurePolicyComplete,
                data=BuildAzurePolicyOutput(
                    azure_policy=final_response,
                    error_message=""
                )
            )
    
__all__ = [
    "BuildAzurePolicyStep",
    "BuildAzurePolicyParameters",
    "BuildAzurePolicyOutput",
]