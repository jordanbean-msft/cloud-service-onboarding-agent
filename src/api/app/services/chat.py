import json
import logging

from opentelemetry import trace
from semantic_kernel import Kernel
from semantic_kernel.contents import AuthorRole, ChatHistory
from semantic_kernel.processes.kernel_process import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start

from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.process_framework.models.cloud_service_onboarding_parameters import CloudServiceOnboardingParameters
from app.process_framework.processes.cloud_service_onboarding_process import build_process_cloud_service_onboarding
from app.routers.context import chat_context_var
from app.services.dependencies import create_kernel, get_create_ai_project_client, get_create_kernel
from app.services.threads import get_agent_thread

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def build_chat_results(chat_input: ChatInput):
    with tracer.start_as_current_span(name="build_chat_results"):
        post_intermediate_message, _, queue = chat_context_var.get()

        try:
            chat_history = await build_chat_history(chat_input.thread_id)

            process = build_process_cloud_service_onboarding(chat_history=chat_history,
                                                            post_intermediate_message=post_intermediate_message)

            async with await start(
                process=process,
                kernel=Kernel(),
                initial_event=KernelProcessEvent(id="Start", data=CloudServiceOnboardingParameters(
                    cloud_service_name=chat_input.content,
                )),
            ) as process_context:
                process_state = await process_context.get_state()



            # await post_intermediate_message(json.dumps(
            #         obj=ChatOutput(
            #             content_type=ContentTypeEnum.MARKDOWN,
            #             content=f"Orchestration result: {value}",
            #             thread_id=chat_input.thread_id,
            #         ),
            #         default=serialize_chat_output,
            #     ) + "\n")


        except Exception as e:
            error_message = f"""
***
**Error processing chat**
{e}
"""
            logger.error(error_message)

            await post_intermediate_message(json.dumps(
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

async def build_chat_history(thread_id):
    thread = await get_agent_thread(thread_id=thread_id, azure_ai_client=get_create_ai_project_client())

    chat_history = ChatHistory()

    async for message in thread.get_messages():
        match message.role:
            case AuthorRole.SYSTEM:
                chat_history.add_system_message(message.content)
            case AuthorRole.USER:
                chat_history.add_user_message(message.content)
            case AuthorRole.ASSISTANT:
                    chat_history.add_assistant_message(message.content)
            case AuthorRole.TOOL:
                chat_history.add_tool_message(message.content)
            case AuthorRole.DEVELOPER:
                chat_history.add_developer_message(message.content)
    return chat_history

__all__ = [
    "build_chat_results",
]
