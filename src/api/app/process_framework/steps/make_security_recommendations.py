import asyncio
import logging
from opentelemetry import trace
from venv import logger
from enum import StrEnum, auto

from pydantic import BaseModel

from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process import KernelProcessStep, KernelProcessStepContext, KernelProcessStepState, kernel_process_step_metadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger  = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class MakeSecurityRecommendationsState(KernelBaseModel):
    analysis_results: str

class MakeSecurityRecommendationsParameters(BaseModel):
    cloud_service_name: str

class MakeSecurityRecommendationsOutput(BaseModel):
    cloud_service_name: str
    error_message: str
    analysis: str

@kernel_process_step_metadata("MakeSecurityRecommendationsStep")
class MakeSecurityRecommendationsStep(KernelProcessStep):
    class Functions(StrEnum):
        MakeSecurityRecommendations = auto()

    class OutputEvents(StrEnum):
        MakeSecurityRecommendationsComplete = auto()
        MakeSecurityRecommendationsError = auto()

    @tracer.start_as_current_span(Functions.MakeSecurityRecommendations)
    @kernel_function(name=Functions.MakeSecurityRecommendations)
    async def run_analysis(self, context: KernelProcessStepContext, params: MakeSecurityRecommendationsParameters):
        logger.debug(f"Running analysis on cloud service: {params.cloud_service_name}")
        await asyncio.sleep(5)

        logger.debug(f"Analysis complete for cloud service: {params.cloud_service_name}")
        await context.emit_event(
            process_event=self.OutputEvents.MakeSecurityRecommendationsComplete,
            data=MakeSecurityRecommendationsOutput(
                cloud_service_name=params.cloud_service_name,
                error_message="",
                analysis=f"Analysis results for cloud service: {params.cloud_service_name}."
            )
        )

        # TODO: Handle the case where the analysis fails
        # if params.systems_number == -1:
        #     logger.debug(f"Analysis error for cloud service: {params.cloud_service_name}")
        #     await context.emit_event(
        #         process_event=self.OutputEvents.AnalysisError,
        #         data=MakeSecurityRecommendationsOutput(
        #             cloud_service_name=params.cloud_service_name,
        #             error_message="Analysis failed",
        #             analysis=""
        #         )
        #)

__all__ = [
    "MakeSecurityRecommendationsStep",
    "MakeSecurityRecommendationsParameters",
    "MakeSecurityRecommendationsOutput",
]