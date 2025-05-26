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

class WriteTerraformParameters(BaseModel):
    cloud_service_name: str
    internal_security_recommendations: str
    public_documentation: str

class WriteTerraformState(KernelBaseModel):
    final_answer: str = ""

class WriteTerraformOutput(BaseModel):
    terraform_code: str
    error_message: str

@kernel_process_step_metadata("WriteTerraformStep")
class WriteTerraformStep(KernelProcessStep[WriteTerraformState]):
    state: WriteTerraformState = Field(default_factory=WriteTerraformState) # type: ignore

    class Functions(StrEnum):
        WriteTerraform = auto()

    class OutputEvents(StrEnum):
        WriteTerraformComplete = auto()

    async def activate(self, state: KernelProcessStepState[WriteTerraformState]):
        self.state = state.state # type: ignore

    @tracer.start_as_current_span(Functions.WriteTerraform)
    @kernel_function(name=Functions.WriteTerraform)
    async def write_terraform(self, context: KernelProcessStepContext, params: WriteTerraformParameters):
        logger.debug(f"Writing Terraform for cloud service: {params.cloud_service_name}")

        agent_manager = get_create_agent_manager()
        
        agent = None
        for a in agent_manager:
            if a.name == "cloud-security-agent":
                agent = a
                break

        if not agent:
            return f"cloud-security-agent not found."

        self.state.chat_history.add_user_message(f"Retrieve security documentation for {params.cloud_service_name}.") # type: ignore

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
                process_event=self.OutputEvents.WriteTerraformComplete,
                data=WriteTerraformOutput(
                    terraform_code="",
                    error_message=str(e)
                )
            )

        logger.debug(f"Final response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response) # type: ignore

        self.state.final_answer = f"Final recommendation for cloud service: {params.cloud_service_name}"

        await context.emit_event(
            process_event=self.OutputEvents.WriteTerraformComplete,
            data=WriteTerraformOutput(
                terraform_code=final_response,
                error_message=""
            )
        )
    
__all__ = [
    "WriteTerraformStep",
    "WriteTerraformParameters",
    "WriteTerraformOutput",
]