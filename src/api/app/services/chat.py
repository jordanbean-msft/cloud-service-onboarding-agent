import json
import logging

from httpx import get
from opentelemetry import trace
from semantic_kernel import Kernel
from semantic_kernel.contents import AuthorRole
from semantic_kernel.processes.kernel_process import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start

from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput
from app.models.content_type_enum import ContentTypeEnum
from app.models.streaming_text_output import StreamingTextOutput, serialize_streaming_text_output
from app.process_framework.models.retrieve_internal_security_recommendations_step_parameters import \
    RetrieveInternalSecurityRecommendationsStepParameters
from app.process_framework.processes.cloud_service_onboarding_process import \
    build_process_cloud_service_onboarding
from app.routers.context import chat_context_var
from app.services.dependencies import get_create_ai_project_client
from app.services.threads import get_agent_thread

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


async def build_chat_results(chat_input: ChatInput):
    with tracer.start_as_current_span(name="build_chat_results"):
        post_intermediate_message, _, queue = chat_context_var.get()

        try:

            thread = await get_agent_thread(thread_id=chat_input.thread_id, azure_ai_client=get_create_ai_project_client())

            process = build_process_cloud_service_onboarding(thread=thread,
                                                             post_intermediate_message=post_intermediate_message)

            async with await start(
                process=process,
                kernel=Kernel(),
                initial_event=KernelProcessEvent(id="Start", data=RetrieveInternalSecurityRecommendationsStepParameters(
                    cloud_service_name=chat_input.content,
                )),
            ) as process_context:
                process_state = await process_context.get_state()

        except Exception as e:
            error_message = f"""
***
**Error processing chat**
{e}
"""
            logger.error(error_message)

            await post_intermediate_message(json.dumps(
                obj=StreamingTextOutput(
                    content_type=ContentTypeEnum.MARKDOWN,
                    text=error_message,
                    thread_id=chat_input.thread_id,
                ),
                default=serialize_streaming_text_output,
            ) + "\n")

            # if cloud_security_agent is not None:
            #     await azure_ai_client.agents.delete_agent(agent_id=cloud_security_agent.id)

        await queue.put(None)




__all__ = [
    "build_chat_results",
]
