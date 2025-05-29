import logging
from typing import Annotated

from opentelemetry import trace
from semantic_kernel import Kernel
from semantic_kernel.contents import AuthorRole, ChatHistory
from semantic_kernel.processes.kernel_process import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from app.process_framework.models.cloud_service_onboarding_parameters import CloudServiceOnboardingParameters
from app.process_framework.processes.cloud_service_onboarding_process import build_process_cloud_service_onboarding
from app.services.threads import get_agent_thread
from app.services.dependencies import get_create_ai_project_client

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def post(message):
    # This function is a placeholder for the post_intermediate_message function.
    # In a real application, this would send the message to a queue or another service.
    logger.info(f"Posting message: {message}")

class CloudSecurityPlugin:
        #self.post_intermediate_message = post_intermediate_message
        #self.kernel = kernel

    @kernel_function(name="CloudServiceOnboarding",
                     description="This function will generate all the necessary data to onboard a cloud service.")
    async def cloud_service_onboarding_process(self,
                                               thread_id: Annotated[str, "Thread ID"],
                                               content: Annotated[str, "Cloud Service Name"]):
        chat_history = await self.build_chat_history(thread_id)

        process = build_process_cloud_service_onboarding(chat_history=chat_history,
                                                         #post_intermediate_message=self.post_intermediate_message)\
                                                         post_intermediate_message=post)

        async with await start(
            process=process,
            kernel=Kernel(), #self.kernel,
            initial_event=KernelProcessEvent(id="Start", data=CloudServiceOnboardingParameters(
                cloud_service_name=content,
            )),
        ) as process_context:
            process_state = await process_context.get_state()

    async def build_chat_history(self, thread_id):
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

__all__ = ["CloudSecurityPlugin",]
