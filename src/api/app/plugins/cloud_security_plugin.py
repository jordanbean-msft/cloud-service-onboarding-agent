import logging
import urllib
import json
import csv
from typing import Annotated
import requests
from opentelemetry import trace

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class CloudSecurityPlugin:
       def __init__(self, ):
            self.thread_id = ''  

__all__ = ["CloudSecurityPlugin",]