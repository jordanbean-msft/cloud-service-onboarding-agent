import logging
import time
from opentelemetry import trace
from venv import logger
from enum import StrEnum, auto

from pydantic import Field
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

from app.process_framework.steps.make_security_recommendations import MakeSecurityRecommendationsParameters

logger  = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class RetrievePublicDocumentationStepState(KernelBaseModel):
    analysis_results: str = ""

class RetrievePublicDocumentationParameters(KernelBaseModel):
    cloud_service_name: str

class RetrievePublicDocumentationOutput(KernelBaseModel):
    public_documentation: str

@kernel_process_step_metadata("RetrievePublicDocumentationStep")
class RetrievePublicDocumentationStep(KernelProcessStep):
    state: RetrievePublicDocumentationStepState = Field(default_factory=RetrievePublicDocumentationStepState) # type: ignore

    class Functions(StrEnum):
        RetrievePublicDocumentation = auto()

    class OutputEvents(StrEnum):
        PublicDocumentsRetrieved = auto()
        PublicDocumentsError = auto()

    async def activate(self, state: KernelProcessStepState[RetrievePublicDocumentationStepState]):
        self.state = state.state # type: ignore

    @tracer.start_as_current_span(Functions.RetrievePublicDocumentation)
    @kernel_function(name=Functions.RetrievePublicDocumentation)
    async def retrieve_public_documentation(self, context: KernelProcessStepContext, params: RetrievePublicDocumentationParameters):
        logger.debug(f"Retrieving public documentation for cloud service: {params.cloud_service_name}")

        await context.emit_event(
            process_event=self.OutputEvents.PublicDocumentsRetrieved,
            data=RetrievePublicDocumentationOutput(
                public_documentation=f"Public documentation for {params.cloud_service_name} retrieved successfully."
            )
        )

__all__ = [
    "RetrievePublicDocumentationStep",
    "RetrievePublicDocumentationParameters",
    "RetrievePublicDocumentationOutput",
]