import asyncio
from typing import ClassVar
import logging
from opentelemetry import trace
from enum import Enum

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes import ProcessBuilder
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

from app.process_framework.steps import retrieve_public_documentation, write_terraform
from app.process_framework.steps.build_azure_policy import BuildAzurePolicyStep
from app.process_framework.steps.retrieve_internal_security_recommendations import RetrieveInternalSecurityRecommendations
from app.process_framework.steps.make_security_recommendations import MakeSecurityRecommendationsStep
from app.process_framework.steps.retrieve_public_documentation import RetrievePublicDocumentationStep
from app.process_framework.steps.write_terraform import WriteTerraformStep

def build_process_cloud_service_onboarding() -> KernelProcess:
      # Create the process builder
    process_builder = ProcessBuilder(
      name="cloud-service-onboarding-process",
    ) # type: ignore

    # Add the steps
    retrieve_internal_security_recommendations = process_builder.add_step(RetrieveInternalSecurityRecommendations)
    retrieve_public_documentation_step = process_builder.add_step(RetrievePublicDocumentationStep)
    make_security_recommendation_step = process_builder.add_step(MakeSecurityRecommendationsStep)
    build_azure_policy_step = process_builder.add_step(BuildAzurePolicyStep)
    write_terraform_step = process_builder.add_step(WriteTerraformStep)

    # Orchestrate the events
    process_builder.on_input_event("Start").send_event_to(
        target=retrieve_internal_security_recommendations,
        parameter_name="params",
    )

    retrieve_internal_security_recommendations.on_event(
        RetrieveInternalSecurityRecommendations.OutputEvents.InternalSecurityRecommendationsRetrieved
    ).send_event_to(
        target=retrieve_public_documentation_step, 
        function_name=RetrievePublicDocumentationStep.Functions.RetrievePublicDocumentation, 
        parameter_name="params"
    )

    retrieve_public_documentation_step.on_event(
        RetrievePublicDocumentationStep.OutputEvents.PublicDocumentsRetrieved
    ).send_event_to(
        target=make_security_recommendation_step, 
        function_name=MakeSecurityRecommendationsStep.Functions.MakeSecurityRecommendations, 
        parameter_name="params"
    )

    make_security_recommendation_step.on_event(
        MakeSecurityRecommendationsStep.OutputEvents.MakeSecurityRecommendationsComplete
    ).send_event_to(
        target=build_azure_policy_step, 
        function_name=BuildAzurePolicyStep.Functions.BuildAzurePolicy, 
        parameter_name="params"
    )

    build_azure_policy_step.on_event(
        BuildAzurePolicyStep.OutputEvents.BuildAzurePolicyComplete
    ).send_event_to(
        target=write_terraform_step, 
        function_name=WriteTerraformStep.Functions.WriteTerraform, 
        parameter_name="params"
    )

    process = process_builder.build()

    return process

__all__ = [
    "build_process_cloud_service_onboarding",
]