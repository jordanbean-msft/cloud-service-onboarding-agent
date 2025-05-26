import logging
from datetime import datetime
import os
from pydoc import cli

from httpx import get
from semantic_kernel import Kernel
from semantic_kernel.agents import AzureAIAgent
from azure.ai.agents.models import (
    CodeInterpreterTool,
    FileSearchTool,
    ToolSet,
    FilePurpose,
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
    BingGroundingTool,
    BingCustomSearchTool
)

from app.config import get_settings
from app.models.chat_output_message import ChatOutputMessage
from app.services.dependencies import AIProjectClient

logger = logging.getLogger("uvicorn.error")

async def setup_file_search_tool(client: AIProjectClient, kernel: Kernel) -> FileSearchTool:
    file_search_tool = None

    try:
        files = []
        # upload documentation files to Agent storage
        for file in os.listdir(f"{os.path.dirname(os.path.abspath(__file__))}/files"):
            file_path = os.path.join(f"{os.path.dirname(os.path.abspath(__file__))}/files", file)
            with open(file_path, "rb") as f:
                file = await client.agents.files.upload(
                    file_path=file_path,
                    purpose=FilePurpose.AGENTS
                )
                logger.info(f"Uploaded {file} to Agent storage.")
                files.append(file.id)

        # create vector store
        vector_store = await client.agents.vector_stores.create(
            file_ids=files,
            name="cloud-security-documentation"
        )
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise

    # create file search tool
    file_search_tool = FileSearchTool(
        vector_store_ids=[vector_store.id],
    )            

    return file_search_tool

async def create_cloud_security_agent(client: AIProjectClient, kernel: Kernel) -> AzureAIAgent:

    azure_ai_agent = None

    async for agent in client.agents.list_agents():
        if agent.name == "cloud-security-agent":
            logger.info(f"Found existing cloud-security-agent: {agent.id}")
            agent = await client.agents.get_agent(agent.id)
            azure_ai_agent = AzureAIAgent(
                client=client,
                definition=agent,
                kernel=kernel
            )
            break

    if not azure_ai_agent:
        code_interpreter = CodeInterpreterTool()

        file_search_tool = await setup_file_search_tool(client, kernel)

        toolset = ToolSet()
        async for connection in client.connections.list():
            if connection.name == get_settings().bing_connection_name:
                logger.info(f"Found existing Bing connection: {connection.id}")
                #bing_grounding_tool = BingGroundingTool(connection_id=connection.id)
                bing_custom_tool = BingCustomSearchTool(
                    connection_id=connection.id,
                    instance_name=get_settings().bing_instance_name
                )
                toolset.add(bing_custom_tool)
                break

        toolset.add(code_interpreter)
        toolset.add(file_search_tool)

        agent_definition = await client.agents.create_agent(
            model=get_settings().azure_openai_model_deployment_name,
            name="cloud-security-agent",
            instructions=f"""
            You are a helpful assistant that can help onboard new cloud services. You will make security recommendations on how to secure cloud resources. You also help write Terraform code to deploy cloud resources securely. You can also search for relevant documentation and provide it to the user. You also write Azure Policy to enforce security best practices.
            """,
            toolset=toolset,
        )

        azure_ai_agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            kernel=kernel
        )

    return azure_ai_agent

__all__ = ["create_cloud_security_agent"]
