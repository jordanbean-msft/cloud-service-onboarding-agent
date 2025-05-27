from functools import lru_cache
from typing import Annotated, List

from fastapi import Depends
from semantic_kernel import Kernel
from semantic_kernel.agents import Agent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from app.agents.cloud_security_agent.main import create_cloud_security_agent
from app.config.config import get_settings
from app.services.dependencies import (get_create_ai_project_client,
                                       get_create_async_azure_ai_client)


async def setup_agents():
    # kernel = await get_create_kernel()
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(
        async_client=await get_create_async_azure_ai_client(),
        deployment_name=get_settings().azure_openai_model_deployment_name,
    ))

    cloud_security_agent = await create_cloud_security_agent(
        client=get_create_ai_project_client(),
        kernel=kernel
    )

    agent_manager = get_create_agent_manager()

    agent_manager.append(cloud_security_agent)


async def delete_agents():
    agent_manager = get_create_agent_manager()

    for agent in agent_manager:
        agent_manager.remove(agent)
        client = get_create_ai_project_client()
        client.agents.delete_agent(agent.id)


def create_agent_manager() -> List[Agent]:
    agents: List[Agent] = []
    return agents


@lru_cache
def get_create_agent_manager() -> List[Agent]:
    return create_agent_manager()


AgentManagerDependency = Annotated[List[Agent], Depends(get_create_agent_manager)]

__all__ = ['setup_agents', 'delete_agents', 'get_create_agent_manager', 'AgentManagerDependency']
