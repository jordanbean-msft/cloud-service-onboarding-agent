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

from app.services.agents import get_create_agent_manager

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class RetrieveSecurityDocumentationParameters(BaseModel):
    cloud_service_name: str
    systems_number: int
    analysis: str
    error_message: str

class RetrieveSecurityDocumentationState(KernelBaseModel):
    chat_history: ChatHistory | None = None

class RetrieveSecurityDocumentationOutput(BaseModel):
    documentation: str
    error_message: str

@kernel_process_step_metadata("RetrieveSecurityDocumentationStep")
class RetrieveSecurityDocumentationStep(KernelProcessStep[RetrieveSecurityDocumentationState]):
    state: RetrieveSecurityDocumentationState = Field(default_factory=RetrieveSecurityDocumentationState)

    class Functions(StrEnum):
        RetrieveSecurityDocumentation = auto()

    class OutputEvents(StrEnum):
        SecurityDocumentationRetrieved = auto()
        SecurityDocumentationError = auto()

    system_prompt: ClassVar[str] = """
You are a helpful assistant that retrieves security documentation. Look in your documentation and find relevant documents related to the security message that you have received. Your job is not to interpret the results, just to find relevant documents.
"""

    async def activate(self, state: KernelProcessStepState[RetrieveSecurityDocumentationState]):
        self.state = state.state # type: ignore
        if self.state.chat_history is None: # type: ignore
            self.state.chat_history = ChatHistory(system_message=self.system_prompt) # type: ignore
        self.state.chat_history # type: ignore

    @tracer.start_as_current_span(Functions.RetrieveSecurityDocumentation)
    @kernel_function(name=Functions.RetrieveSecurityDocumentation)
    async def retrieve_security_documentation(self, context: KernelProcessStepContext, params: RetrieveSecurityDocumentationParameters):
        logger.debug(f"Retrieving security documentation for: {params.cloud_service_name} with systems number: {params.systems_number}")
        agent_manager = get_create_agent_manager()
        
        agent = None
        for a in agent_manager:
            if a.name == "security-agent":
                agent = a
                break

        if not agent:
            return f"security-agent not found."

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
                process_event=self.OutputEvents.SecurityDocumentationError,
                data=RetrieveSecurityDocumentationOutput(
                    documentation="",
                    error_message=str(e)
                )
            )

        logger.debug(f"Final response: {final_response}")

        self.state.chat_history.add_assistant_message(final_response) # type: ignore

        await context.emit_event(
            process_event=self.OutputEvents.SecurityDocumentationRetrieved,
            data=RetrieveSecurityDocumentationOutput(
                documentation=final_response,
                error_message=""
            )
        )
    
async def on_intermediate_message(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            logger.debug(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            logger.debug(f"Function Result:> {item.result} for function: {item.name}")
        else:
            logger.debug(f"{message.role}: {message.content}")

__all__ = [
    "RetrieveSecurityDocumentationStep",
    "RetrieveSecurityDocumentationParameters",
    "RetrieveSecurityDocumentationState",
]