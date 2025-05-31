import logging
from functools import partial
from typing import Any, Awaitable, Callable

from opentelemetry import trace
from psutil import Process
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process.kernel_process import \
    KernelProcess
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgentThread

from app.process_framework.steps.build_azure_policy import BuildAzurePolicyStep
from app.process_framework.steps.make_security_recommendations import \
    MakeSecurityRecommendationsStep
from app.process_framework.steps.retrieve_internal_security_recommendations import \
    RetrieveInternalSecurityRecommendationsStep
from app.process_framework.steps.write_terraform import WriteTerraformStep

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)



async def retrieve_internal_security_recommendation_step_factory(thread: AzureAIAgentThread,
                                                                 post_intermediate_message: Callable[[Any], Awaitable[None]]
                                                                 ) -> RetrieveInternalSecurityRecommendationsStep:
    step = RetrieveInternalSecurityRecommendationsStep()
    step.state.thread = thread
    step.state.post_intermediate_message = post_intermediate_message
    return step



async def make_security_recommendation_step_factory(thread: AzureAIAgentThread,
                                                    post_intermediate_message: Callable[[Any], Awaitable[None]]
                                                    ) -> MakeSecurityRecommendationsStep:
    step = MakeSecurityRecommendationsStep()
    step.state.thread = thread
    step.state.post_intermediate_message = post_intermediate_message
    return step



async def write_terraform_step_factory(thread: AzureAIAgentThread,
                                       post_intermediate_message: Callable[[Any], Awaitable[None]]
                                       ) -> WriteTerraformStep:
    step = WriteTerraformStep()
    step.state.thread = thread
    step.state.post_intermediate_message = post_intermediate_message
    return step



async def build_azure_policy_step_factory(thread: AzureAIAgentThread,
                                          post_intermediate_message: Callable[[Any], Awaitable[None]]
                                          ) -> BuildAzurePolicyStep:
    step = BuildAzurePolicyStep()
    step.state.thread = thread
    step.state.post_intermediate_message = post_intermediate_message
    return step


def build_process_cloud_service_onboarding(thread: AzureAIAgentThread,
                                           post_intermediate_message: Callable[[Any], Awaitable[None]]) -> KernelProcess:
    # Create the process builder
    process_builder = ProcessBuilder(
        name="cloud-service-onboarding-process",
    )  # type: ignore

    # Add the steps
    retrieve_internal_security_recommendations, \
    make_security_recommendation_step, \
    build_azure_policy_step, \
    write_terraform_step = add_steps(
        process_builder,
        thread,
        post_intermediate_message)

    # Orchestrate the events
    setup_events(process_builder,
                 retrieve_internal_security_recommendations,
                 make_security_recommendation_step,
                 build_azure_policy_step,
                 write_terraform_step)

    process = process_builder.build()

    return process


def setup_events(process_builder,
                 retrieve_internal_security_recommendations,
                 make_security_recommendation_step,
                 build_azure_policy_step,
                 write_terraform_step):
    process_builder.on_input_event("Start").send_event_to(
        target=retrieve_internal_security_recommendations,
        parameter_name="params",
    )

    retrieve_internal_security_recommendations.on_event(
        RetrieveInternalSecurityRecommendationsStep.OutputEvents.RetrieveInternalSecurityRecommendationsComplete
    ).send_event_to(
        target=make_security_recommendation_step,
        function_name=MakeSecurityRecommendationsStep.Functions.MakeSecurityRecommendations,
        parameter_name="params"
    )

    retrieve_internal_security_recommendations.on_event(
        RetrieveInternalSecurityRecommendationsStep.OutputEvents.RetrieveInternalSecurityRecommendationsError
    ).stop_process()

    make_security_recommendation_step.on_event(
        MakeSecurityRecommendationsStep.OutputEvents.MakeSecurityRecommendationsComplete
    ).send_event_to(
        target=build_azure_policy_step,
        function_name=BuildAzurePolicyStep.Functions.BuildAzurePolicy,
        parameter_name="params"
    )

    make_security_recommendation_step.on_event(
        MakeSecurityRecommendationsStep.OutputEvents.MakeSecurityRecommendationsError
    ).stop_process()

    build_azure_policy_step.on_event(
        BuildAzurePolicyStep.OutputEvents.BuildAzurePolicyComplete
    ).send_event_to(
        target=write_terraform_step,
        function_name=WriteTerraformStep.Functions.WriteTerraform,
        parameter_name="params"
    )

    build_azure_policy_step.on_event(
        BuildAzurePolicyStep.OutputEvents.BuildAzurePolicyError
    ).stop_process()

    write_terraform_step.on_event(
        WriteTerraformStep.OutputEvents.WriteTerraformComplete
    ).stop_process()

    write_terraform_step.on_event(
        WriteTerraformStep.OutputEvents.WriteTerraformError
    ).stop_process()



def add_steps(process_builder: ProcessBuilder,
              thread: AzureAIAgentThread,
              intermediate_message: Callable[[Any], Awaitable[None]]):
    retrieve_internal_security_recommendations = process_builder.add_step(
        step_type=RetrieveInternalSecurityRecommendationsStep,
        factory_function=partial(retrieve_internal_security_recommendation_step_factory,
                                 thread=thread,
                                 post_intermediate_message=intermediate_message)
    )

    make_security_recommendation_step = process_builder.add_step(
        step_type=MakeSecurityRecommendationsStep,
        factory_function=partial(make_security_recommendation_step_factory,
                                 thread=thread,
                                 post_intermediate_message=intermediate_message)
    )
    build_azure_policy_step = process_builder.add_step(
        step_type=BuildAzurePolicyStep,
        factory_function=partial(build_azure_policy_step_factory,
                                 thread=thread,
                                 post_intermediate_message=intermediate_message)
    )
    write_terraform_step = process_builder.add_step(
        step_type=WriteTerraformStep,
        factory_function=partial(write_terraform_step_factory,
                                 thread=thread,
                                 post_intermediate_message=intermediate_message)
    )

    return retrieve_internal_security_recommendations, make_security_recommendation_step, build_azure_policy_step, write_terraform_step


__all__ = [
    "build_process_cloud_service_onboarding",
]
