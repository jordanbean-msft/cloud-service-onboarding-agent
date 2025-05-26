import json
import logging
from opentelemetry import trace

from semantic_kernel import Kernel
from semantic_kernel.contents import StreamingFileReferenceContent, StreamingTextContent
from semantic_kernel.agents import AzureAIAgentThread

from semantic_kernel.processes.kernel_process import KernelProcessEvent, KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from azure.ai.agents.models import ThreadMessageOptions
from app.agents import cloud_security_agent
from app.agents.cloud_security_agent.main import create_cloud_security_agent
from app.models.chat_create_thread_output import ChatCreateThreadOutput
from app.models.chat_get_thread import ChatGetThreadInput
from app.models.chat_input import ChatInput
from app.models.chat_output import ChatOutput, serialize_chat_output
from app.models.content_type_enum import ContentTypeEnum
from app.plugins.cloud_security_plugin import CloudSecurityPlugin
from app.process_framework.models.cloud_service_onboarding_parameters import CloudServiceOnboardingParameters
from app.process_framework.processes.cloud_service_onboarding_process import build_process_cloud_service_onboarding
from app.process_framework.steps.write_terraform import WriteTerraformState, WriteTerraformStep
from app.services.dependencies import AIProjectClient

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

async def create_thread(azure_ai_client: AIProjectClient):
        thread = await azure_ai_client.agents.threads.create()

        return ChatCreateThreadOutput(thread_id=thread.id)

async def build_chat_results(chat_input: ChatInput, azure_ai_client: AIProjectClient):
    with tracer.start_as_current_span(name="build_chat_results"):
        cloud_security_agent = None
        try:        
            kernel = Kernel()

            # cloud_security_agent = await create_cloud_security_agent(
            #     client=azure_ai_client,
            #     kernel=kernel
            # )

            # kernel.add_plugin(
            #     plugin=CloudSecurityPlugin(
            #     ),
            #     plugin_name="cloud_security_plugin"
            # )           
            # thread = await get_agent_thread(chat_input, azure_ai_client, cloud_security_agent)

            process = build_process_cloud_service_onboarding()

            async with await start(
                process=process,
                kernel=kernel,
                initial_event=KernelProcessEvent(id="Start", data=CloudServiceOnboardingParameters(
                    cloud_service_name=chat_input.content,
                )),
            ) as process_context:
                process_state = await process_context.get_state()

                for step in process_state.steps:
                    logger.debug(f"Step: {step.state.name}")

                    yield json.dumps(
                        obj=ChatOutput(
                            content_type=ContentTypeEnum.MARKDOWN,
                            content=f"Step: {step.state.name} - {step.state.state.chat_history[-1].content}", # type: ignore
                            thread_id=chat_input.thread_id,
                        ),
                        default=serialize_chat_output,
                    )

                # write_terraform_state: KernelProcessStepState[WriteTerraformState] = next(
                #     (s.state for s in process_state.steps if s.state.name == WriteTerraformStep.__name__), None
                # ) # type: ignore

                # if write_terraform_state:
                #     logger.debug(f"Write Terraform state: {write_terraform_state}")

                #     final_result = ChatOutput(
                #         content_type=ContentTypeEnum.MARKDOWN,
                #         content=write_terraform_state.state.final_answer.strip(), # type: ignore
                #         thread_id="asdf",
                #     )

                #     final_result_str = json.dumps(
                #         obj=final_result,
                #         default=serialize_chat_output,
                #     )

                #     yield final_result_str

                    # for item in response.items:
                    #   if isinstance(item, StreamingTextContent):
                    #       yield json.dumps(
                    #           obj=ChatOutput(
                    #               content_type=ContentTypeEnum.MARKDOWN,
                    #               content=response.content.content,
                    #               thread_id=str(response.thread.id),
                    #           ),
                    #           default=serialize_chat_output,                    
                    #       )
                    #   elif isinstance(item, StreamingFileReferenceContent):
                    #       yield json.dumps(
                    #           obj=ChatOutput(
                    #               content_type=ContentTypeEnum.FILE,
                    #               content=item.file_id if item.file_id else "",
                    #               thread_id=str(response.thread.id),
                    #           ),
                    #           default=serialize_chat_output,                    
                    #       )
                    #   else:
                    #       logger.warning(f"Unknown content type: {type(item)}")

                    #await send_message("asdf", final_result_str)
                 
            # async for response in cloud_security_agent.invoke_stream(
            #         thread=thread,
            #         messages=chat_input.content
            # ):
            #     for item in response.items:
            #         if isinstance(item, StreamingTextContent):
            #             yield json.dumps(
            #                 obj=ChatOutput(
            #                     content_type=ContentTypeEnum.MARKDOWN,
            #                     content=response.content.content,
            #                     thread_id=str(response.thread.id),
            #                 ),
            #                 default=serialize_chat_output,                    
            #             )
            #         elif isinstance(item, StreamingFileReferenceContent):
            #             yield json.dumps(
            #                 obj=ChatOutput(
            #                     content_type=ContentTypeEnum.FILE,
            #                     content=item.file_id if item.file_id else "",
            #                     thread_id=str(response.thread.id),
            #                 ),
            #                 default=serialize_chat_output,                    
            #             )
            #         else:
            #             logger.warning(f"Unknown content type: {type(item)}")
            
            # await azure_ai_client.agents.delete_agent(agent_id=cloud_security_agent.id)
        except Exception as e:
            logger.error(f"Error processing chat: {e}")

            if cloud_security_agent is not None:
                await azure_ai_client.agents.delete_agent(agent_id=cloud_security_agent.id)

async def get_agent_thread(chat_input, azure_ai_client, cloud_security_agent):
    thread_messages = await get_thread(ChatGetThreadInput(thread_id=chat_input.thread_id), azure_ai_client)

    messages = []

    for message in thread_messages:
        msg = ThreadMessageOptions(
                    content=message['content'],
                    role=message['role']
                )
        messages.append(msg)

    thread = AzureAIAgentThread(
                client=cloud_security_agent.client,
                thread_id=chat_input.thread_id,
                messages=messages
            )
    
    return thread

async def get_thread(thread_input: ChatGetThreadInput, azure_ai_client: AIProjectClient):
        messages = []
        async for msg in azure_ai_client.agents.messages.list(thread_id=thread_input.thread_id):
            messages.append(msg)

        return_value = []

        for message in messages:
            return_value.append({"role": message.role, "content": message.content})

        return return_value

__all__ = [
    "build_chat_results",
    "get_agent_thread",
    "get_thread",
    "create_thread",
]
