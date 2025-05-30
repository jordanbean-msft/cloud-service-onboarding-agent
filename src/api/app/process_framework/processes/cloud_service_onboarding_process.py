import logging
from functools import partial
from typing import Any, Awaitable, Callable

from opentelemetry import trace
from semantic_kernel.contents import ChatHistory
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process.kernel_process import \
    KernelProcess

from app.process_framework.steps.build_azure_policy import BuildAzurePolicyStep
from app.process_framework.steps.make_security_recommendations import \
    MakeSecurityRecommendationsStep
from app.process_framework.steps.retrieve_internal_security_recommendations import \
    RetrieveInternalSecurityRecommendationsStep
from app.process_framework.steps.retrieve_public_documentation import \
    RetrievePublicDocumentationStep
from app.process_framework.steps.write_terraform import WriteTerraformStep

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)


async def retrieve_internal_security_recommendation_step_factory(chat_history: ChatHistory,
                                                                 post_intermediate_message: Callable[[
                                                                     Any], Awaitable[None]]
                                                                 ) -> RetrieveInternalSecurityRecommendationsStep:
    step = RetrieveInternalSecurityRecommendationsStep()
    step.state.chat_history = chat_history
    step.state.post_intermediate_message = post_intermediate_message
    return step


async def make_security_recommendation_step_factory(chat_history: ChatHistory,
                                                    post_intermediate_message: Callable[[
                                                        Any], Awaitable[None]]
                                                    ) -> MakeSecurityRecommendationsStep:
    step = MakeSecurityRecommendationsStep()
    step.state.chat_history = chat_history
    step.state.post_intermediate_message = post_intermediate_message
    return step


async def retrieve_public_documentation_step_factory(chat_history: ChatHistory,
                                                     post_intermediate_message: Callable[[
                                                         Any], Awaitable[None]]
                                                     ) -> RetrievePublicDocumentationStep:
    step = RetrievePublicDocumentationStep()
    step.state.chat_history = chat_history
    step.state.post_intermediate_message = post_intermediate_message
    return step


async def write_terraform_step_factory(chat_history: ChatHistory,
                                       post_intermediate_message: Callable[[Any], Awaitable[None]]
                                       ) -> WriteTerraformStep:
    step = WriteTerraformStep()
    step.state.chat_history = chat_history
    step.state.post_intermediate_message = post_intermediate_message
    return step


async def build_azure_policy_step_factory(chat_history: ChatHistory,
                                          post_intermediate_message: Callable[[
                                              Any], Awaitable[None]]
                                          ) -> BuildAzurePolicyStep:
    step = BuildAzurePolicyStep()
    step.state.chat_history = chat_history
    step.state.post_intermediate_message = post_intermediate_message
    return step


def build_process_cloud_service_onboarding(chat_history: ChatHistory, post_intermediate_message: Callable[[Any], Awaitable[None]]) -> KernelProcess:
    # Create the process builder
    process_builder = ProcessBuilder(
        name="cloud-service-onboarding-process",
    )  # type: ignore

    # Add the steps
    retrieve_internal_security_recommendations, retrieve_public_documentation_step, make_security_recommendation_step, build_azure_policy_step, write_terraform_step = add_steps(
        process_builder, chat_history, post_intermediate_message)

    # Orchestrate the events
    setup_events(process_builder,
                 retrieve_internal_security_recommendations,
                 retrieve_public_documentation_step,
                 make_security_recommendation_step,
                 build_azure_policy_step,
                 write_terraform_step)

    process = process_builder.build()

    return process


def setup_events(process_builder,
                 retrieve_internal_security_recommendations,
                 retrieve_public_documentation_step,
                 make_security_recommendation_step,
                 build_azure_policy_step,
                 write_terraform_step):
    process_builder.on_input_event("Start").send_event_to(
        target=retrieve_internal_security_recommendations,
        # target=make_security_recommendation_step,
        parameter_name="params",
    )

    retrieve_internal_security_recommendations.on_event(
        RetrieveInternalSecurityRecommendationsStep.OutputEvents.RetrieveInternalSecurityRecommendationsComplete
    ).send_event_to(
        #target=retrieve_public_documentation_step,
        target=make_security_recommendation_step,
        #function_name=RetrievePublicDocumentationStep.Functions.RetrievePublicDocumentation,
        function_name=MakeSecurityRecommendationsStep.Functions.MakeSecurityRecommendations,
        parameter_name="params"
    )

    retrieve_internal_security_recommendations.on_event(
        RetrieveInternalSecurityRecommendationsStep.OutputEvents.RetrieveInternalSecurityRecommendationsError
    ).stop_process()

    # retrieve_public_documentation_step.on_event(
    #     RetrievePublicDocumentationStep.OutputEvents.RetrievePublicDocumentationComplete
    # ).send_event_to(
    #     target=make_security_recommendation_step,
    #     function_name=MakeSecurityRecommendationsStep.Functions.MakeSecurityRecommendations,
    #     parameter_name="params"
    # )

    # retrieve_public_documentation_step.on_event(
    #     RetrievePublicDocumentationStep.OutputEvents.RetrievePublicDocumentationError
    # ).stop_process()

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


def add_steps(process_builder, chat_history: ChatHistory, intermediate_message: Callable[[Any], Awaitable[None]]):
    retrieve_internal_security_recommendations = process_builder.add_step(
        step_type=RetrieveInternalSecurityRecommendationsStep,
        factory_function=partial(retrieve_internal_security_recommendation_step_factory,
                                 chat_history=chat_history,
                                 post_intermediate_message=intermediate_message)
    )

    retrieve_public_documentation_step = process_builder.add_step(
        step_type=RetrievePublicDocumentationStep,
        factory_function=partial(retrieve_public_documentation_step_factory,
                                 chat_history=chat_history,
                                 post_intermediate_message=intermediate_message)
    )
    make_security_recommendation_step = process_builder.add_step(
        step_type=MakeSecurityRecommendationsStep,
        factory_function=partial(make_security_recommendation_step_factory,
                                 chat_history=chat_history,
                                 post_intermediate_message=intermediate_message)
    )
    build_azure_policy_step = process_builder.add_step(
        step_type=BuildAzurePolicyStep,
        factory_function=partial(build_azure_policy_step_factory,
                                 chat_history=chat_history,
                                 post_intermediate_message=intermediate_message)
    )
    write_terraform_step = process_builder.add_step(
        step_type=WriteTerraformStep,
        factory_function=partial(write_terraform_step_factory,
                                 chat_history=chat_history,
                                 post_intermediate_message=intermediate_message)
    )

    return retrieve_internal_security_recommendations, retrieve_public_documentation_step, make_security_recommendation_step, build_azure_policy_step, write_terraform_step


__all__ = [
    "build_process_cloud_service_onboarding",
]
