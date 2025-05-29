import logging

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.functions import KernelPlugin

logger = logging.getLogger("uvicorn.error")

async def create_cloud_security_process_agent(kernel: Kernel) -> ChatCompletionAgent:
    cloud_security_process_agent = ChatCompletionAgent(
        name="cloud-security-process-agent",
        instructions="You are a cloud security process agent that can assist with cloud security-related tasks.",
        kernel=kernel,
    )
    return cloud_security_process_agent

__all__ = ["create_cloud_security_process_agent"]
