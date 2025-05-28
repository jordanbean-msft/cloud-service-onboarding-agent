import json
import logging

from azure.ai.agents.models import ThreadMessageOptions
from opentelemetry import trace
from semantic_kernel import Kernel
from semantic_kernel.contents import (ChatHistory, AuthorRole)
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgentThread
from semantic_kernel.processes.kernel_process import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start

from app.models.chat_create_thread_output import ChatCreateThreadOutput
from app.models.chat_get_thread import ChatGetThreadInput
from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.process_framework.models.cloud_service_onboarding_parameters import \
    CloudServiceOnboardingParameters
from app.process_framework.processes.cloud_service_onboarding_process import \
    build_process_cloud_service_onboarding
from app.routers.context import chat_context_var
from app.services.agents import get_create_agent_manager
from app.services.dependencies import AIProjectClient

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


async def create_thread(azure_ai_client: AIProjectClient):
    thread = await azure_ai_client.agents.threads.create()

    return ChatCreateThreadOutput(thread_id=thread.id)


async def build_chat_results(chat_input: ChatInput, azure_ai_client: AIProjectClient):
    with tracer.start_as_current_span(name="build_chat_results"):
        emit_event, _, queue = chat_context_var.get()

        try:
            kernel = Kernel()

            agent_manager = get_create_agent_manager()

            cloud_security_agent = None
            for a in agent_manager:
                if a.name == "cloud-security-agent":
                    cloud_security_agent = a
                    break

            if not cloud_security_agent:
                return f"cloud-security-agent not found."

            thread = await get_agent_thread(chat_input, azure_ai_client, cloud_security_agent)

            chat_history = ChatHistory()

            async for message in thread.get_messages():
                match message.role:
                    case AuthorRole.USER:
                        chat_history.add_user_message(message.content)
                    case AuthorRole.ASSISTANT:
                        chat_history.add_assistant_message(message.content)
                    case AuthorRole.TOOL:
                        chat_history.add_tool_message(message.content)

            process = build_process_cloud_service_onboarding(chat_history=chat_history,
                                                             emit_event=emit_event)

            async with await start(
                process=process,
                kernel=kernel,
                initial_event=KernelProcessEvent(id="Start", data=CloudServiceOnboardingParameters(
                    cloud_service_name=chat_input.content,
                )),
            ) as process_context:
                process_state = await process_context.get_state()

#                 for step in process_state.steps:
#                     step_message = f"""
# ***
# ## Step: {step.state.name}
# {step.state.state.chat_history[-1].content if step.state.state.chat_history else ''}
# """
#                     logger.debug(step_message)

#                     await emit_event(json.dumps(
#                         obj=ChatOutput(
#                             content_type=ContentTypeEnum.MARKDOWN,
#                             content=step_message,
#                             thread_id=chat_input.thread_id,
#                         ),
#                         default=serialize_chat_output,
#                     ) + "\n")  # Ensure each chunk ends with a newline

        except Exception as e:
            error_message = f"""
***
**Error processing chat**
{e}
"""
            logger.error(error_message)

            await emit_event(json.dumps(
                obj=ChatOutput(
                    content_type=ContentTypeEnum.MARKDOWN,
                    content=error_message,
                    thread_id=chat_input.thread_id,
                ),
                default=serialize_chat_output,
            ) + "\n")

            # if cloud_security_agent is not None:
            #     await azure_ai_client.agents.delete_agent(agent_id=cloud_security_agent.id)

        await queue.put(None)


async def get_agent_thread(chat_input, azure_ai_client, cloud_security_agent):
    thread_messages = await get_thread(ChatGetThreadInput(thread_id=chat_input.thread_id), azure_ai_client)

    messages = []

    for message in thread_messages:
        msg = ThreadMessageOptions(
            content=message['content'],
            role=message['role']
        )
        messages.append(msg)

    thread = AzureAIAgentThread(
        client=cloud_security_agent.client,
        thread_id=chat_input.thread_id,
        messages=messages
    )

    return thread


async def get_thread(thread_input: ChatGetThreadInput, azure_ai_client: AIProjectClient):
    messages = []
    async for msg in azure_ai_client.agents.messages.list(thread_id=thread_input.thread_id):
        messages.append(msg)

    return_value = []

    for message in messages:
        return_value.append({"role": message.role, "content": message.content})

    return return_value

__all__ = [
    "build_chat_results",
    "get_agent_thread",
    "get_thread",
    "create_thread",
]
