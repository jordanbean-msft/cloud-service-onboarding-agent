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

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class BuildAzurePolicyParameters(BaseModel):
    cloud_service_name: str
    error_message: str
    documentation: str

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

        self.state.final_answer = f"Final recommendation for cloud service: {params.cloud_service_name}"

        await context.emit_event(
                process_event=self.OutputEvents.BuildAzurePolicyComplete,
                data="Azure Policy"
            )
    
__all__ = [
    "BuildAzurePolicyStep",
    "BuildAzurePolicyParameters",
    "BuildAzurePolicyOutput",
]