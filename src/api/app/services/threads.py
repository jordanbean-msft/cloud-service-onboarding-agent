from azure.ai.agents.models import ThreadMessageOptions
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgentThread

from app.models.chat_create_thread_output import ChatCreateThreadOutput
from app.services.dependencies import AIProjectClient

async def create_thread(azure_ai_client: AIProjectClient):
    thread = await azure_ai_client.agents.threads.create()

    return ChatCreateThreadOutput(thread_id=thread.id)

async def get_agent_thread(thread_id, azure_ai_client: AIProjectClient):
        thread_messages = await get_thread(thread_id, azure_ai_client)

        messages = []

        for message in thread_messages:
            msg = ThreadMessageOptions(
                content=message['content'],
                role=message['role']
            )
            messages.append(msg)

        thread = AzureAIAgentThread(
            client=azure_ai_client,
            thread_id=thread_id,
            messages=messages
        )

        return thread

async def get_thread(thread_id: str, azure_ai_client: AIProjectClient):
    messages = []
    async for msg in azure_ai_client.agents.messages.list(thread_id=thread_id):
        messages.append(msg)

    return_value = []

    for message in messages:
        return_value.append({"role": message.role, "content": message.content})

    return return_value

__all__ = [
     'get_agent_thread',
     'get_thread',
     'create_thread'
]
