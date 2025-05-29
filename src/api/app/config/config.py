from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    azure_openai_model_deployment_name: str
    azure_ai_agent_endpoint: str
    azure_ai_agent_api_version: str
    application_insights_connection_string: str
    bing_connection_name: str
    bing_instance_name: str

    model_config = SettingsConfigDict(env_file=".env",
                                      env_file_encoding="utf-8")


@lru_cache
def get_settings():
    return Settings()  # type: ignore


__all__ = ["get_settings"]
