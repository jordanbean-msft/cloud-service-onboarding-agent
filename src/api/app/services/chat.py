import json
import logging
from math import log
from typing import Tuple

from openai import AsyncAzureOpenAI
from opentelemetry import trace
from semantic_kernel import Kernel
from semantic_kernel.agents import OrchestrationHandoffs, HandoffOrchestration, AzureAIAgent, ChatCompletionAgent
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion

from app.agents import cloud_security_process_agent
from app.agents.cloud_security_process_agent.main import create_cloud_security_process_agent
from app.config.config import get_settings
from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.plugins.cloud_security_plugin import CloudSecurityPlugin
from app.routers.context import chat_context_var
from app.services.agents import get_create_agent_manager
from app.services.dependencies import create_kernel

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def build_chat_results(chat_input: ChatInput):
    with tracer.start_as_current_span(name="build_chat_results"):
        post_intermediate_message, _, queue = chat_context_var.get()

        try:
            kernel = await create_kernel()

            # kernel.add_plugin(CloudSecurityPlugin(
            #     #post_intermediate_message=post,
            # ))

            cloud_security_process_agent = await create_cloud_security_process_agent(
                kernel=kernel
            )

            orchestration_agent = get_orchestration_agent()

            handoff_orchestration, runtime = setup_orchestration(cloud_security_process_agent=cloud_security_process_agent,
                                                                 orchestration_agent=orchestration_agent)

            runtime.start()

            orchestration_result = await handoff_orchestration.invoke(
                task=chat_input.content,
                runtime=runtime,
            )

            value = await orchestration_result.get()

            await post_intermediate_message(json.dumps(
                    obj=ChatOutput(
                        content_type=ContentTypeEnum.MARKDOWN,
                        content=f"Orchestration result: {value}",
                        thread_id=chat_input.thread_id,
                    ),
                    default=serialize_chat_output,
                ) + "\n")

            await runtime.stop()

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

def setup_orchestration(cloud_security_process_agent,
                        orchestration_agent):
    handoffs = (
                OrchestrationHandoffs()
                .add_many(
                    source_agent=orchestration_agent.name,
                    target_agents={
                        cloud_security_process_agent.name: "Transfer to this agent if the user is asking about cloud service onboarding."
                    }
                )
            )

    handoff_orchestration = HandoffOrchestration(
                members=[
                    orchestration_agent,
                    cloud_security_process_agent
                ],
                handoffs=handoffs,
                agent_response_callback=agent_response_callback,
            )

    runtime = InProcessRuntime()
    return handoff_orchestration, runtime

def get_orchestration_agent() -> ChatCompletionAgent:
    agent_manager = get_create_agent_manager()
    agent_names = [
        "orchestration-agent"
    ]
    agents = {}

    for a in agent_manager:
        if a.name in agent_names:
            agents[a.name] = a

    missing = [name for name in agent_names if name not in agents]
    if missing:
        raise ValueError(f"Agent(s) not found: {', '.join(missing)}")

    return agents["orchestration-agent"]

def agent_response_callback(message):
    agent_response = f"Agent response: {getattr(message, 'content', str(message))}"

    logger.debug(agent_response)


__all__ = [
    "build_chat_results",
]
