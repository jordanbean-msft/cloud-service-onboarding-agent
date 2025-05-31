import logging

from fastapi import APIRouter, Response
from opentelemetry import trace
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory

from app.config.config import get_settings
from app.services.dependencies import get_create_async_azure_ai_client

tracer = trace.get_tracer(__name__)

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


@tracer.start_as_current_span(name="startup")
@router.get("/startup")
async def startup_probe(response: Response):
    azure_openai_status_dict = await check_azure_openai()

    return_value = {
        "azure_openai": azure_openai_status_dict,
    }

    response.status_code = 200

    # Set the response status code to 503 if any of the checks failed
    for _, value in return_value.items():
        if value["status"] != 200:
            response.status_code = 503
            break

    return_value["status"] = response.status_code # type: ignore

    logger.info(return_value)

    return return_value


@tracer.start_as_current_span(name="check_azure_openai")
async def check_azure_openai():
    status_dict = {}
    try:
        chat_completion_service = AzureChatCompletion(
            async_client=await get_create_async_azure_ai_client(),
            deployment_name=get_settings().azure_openai_model_deployment_name,
        )

        chat_history = ChatHistory()
        chat_history.add_user_message("Hello, how are you?")

        response = await chat_completion_service.get_chat_message_content(
            chat_history=chat_history,
            settings=OpenAIChatPromptExecutionSettings()
        )

        status_dict = {"status": 200}
    except Exception as e:
        logger.error(f"Error occurred while checking connection to Azure OpenAI: {e}")
        status_dict = {"status": 503, "error": str(e)}
        return status_dict

    return status_dict
