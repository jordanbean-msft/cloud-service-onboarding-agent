from functools import lru_cache
from typing import Annotated

from async_lru import alru_cache
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from fastapi import Depends
from openai import AsyncAzureOpenAI
from semantic_kernel import Kernel
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from app.config import get_settings


def create_azure_ai_client() -> AIProjectClient:
    creds = DefaultAzureCredential()

    client = AzureAIAgent.create_client(
        credential=creds,
        endpoint=get_settings().azure_ai_agent_endpoint
    )

    return client


async def create_async_azure_ai_client() -> AsyncAzureOpenAI:
    project_client = AIProjectClient(
        endpoint=get_settings().azure_ai_agent_endpoint,
        credential=DefaultAzureCredential()
    )

    async_azure_ai_client = await project_client.inference.get_azure_openai_client(
        api_version=get_settings().azure_ai_agent_api_version,
    )

    return async_azure_ai_client


async def create_kernel() -> Kernel:
    kernel = Kernel()

    kernel.add_service(AzureChatCompletion(
        async_client=await get_create_async_azure_ai_client(),
        deployment_name=get_settings().azure_openai_model_deployment_name,
    ))

    return kernel


@lru_cache
def get_create_ai_project_client() -> AIProjectClient:
    return create_azure_ai_client()


@alru_cache
async def get_create_async_azure_ai_client() -> AsyncAzureOpenAI:
    return await create_async_azure_ai_client()


@alru_cache
async def get_create_kernel() -> Kernel:
    return await create_kernel()

AIProjectClientDependency = Annotated[AIProjectClient, Depends(get_create_ai_project_client)]
AsyncAzureAIClientDependency = Annotated[AsyncAzureOpenAI,
                                         Depends(get_create_async_azure_ai_client)]
KernelDependency = Annotated[Kernel, Depends(get_create_kernel)]

__all__ = [
    "AIProjectClientDependency",
    "AsyncAzureAIClientDependency",
    "KernelDependency",
    "get_create_ai_project_client",
    "get_create_async_azure_ai_client",
    "get_create_kernel",
]
