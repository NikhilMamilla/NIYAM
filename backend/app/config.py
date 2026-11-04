from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    hosted_llm_api_key: str = ""
    open_model_endpoint: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
