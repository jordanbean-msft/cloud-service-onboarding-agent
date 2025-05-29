import logging

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent

logger = logging.getLogger("uvicorn.error")

async def create_orchestration_agent(kernel: Kernel) -> ChatCompletionAgent:
    orchestration_agent = ChatCompletionAgent(
        name="orchestration-agent",
        instructions="You are a customer support agent that can triage customer requests and route them to the appropriate agent.",
        kernel=kernel,
    )

    return orchestration_agent

__all__ = ["create_orchestration_agent"]
