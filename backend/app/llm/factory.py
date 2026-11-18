from typing import Literal

from app.config import Settings, settings as default_settings
from app.llm.base import LLMProvider, ProviderNotConfigured
from app.llm.providers import AnthropicProvider, OpenAICompatProvider


def get_provider(role: Literal["hosted", "open"], settings: Settings | None = None) -> LLMProvider:
    s = settings or default_settings
    common = {"max_retries": s.llm_max_retries, "timeout_s": s.llm_timeout_s,
              "rate_limit_retries": s.llm_rate_limit_retries}
    if role == "hosted":
        common |= {"min_interval_s": s.hosted_llm_min_interval_s, "extra_body": s.hosted_llm_extra_body}
        if s.hosted_llm_provider == "anthropic" and s.hosted_llm_model and s.hosted_llm_api_key:
            return AnthropicProvider(api_key=s.hosted_llm_api_key, model=s.hosted_llm_model, **common)
        if s.hosted_llm_provider == "openai_compat" and s.hosted_llm_model and s.hosted_llm_base_url:
            return OpenAICompatProvider(base_url=s.hosted_llm_base_url, model=s.hosted_llm_model,
                                        api_key=s.hosted_llm_api_key, **common)
        raise ProviderNotConfigured(
            "hosted LLM not configured: set HOSTED_LLM_PROVIDER (anthropic|openai_compat), HOSTED_LLM_MODEL and "
            "HOSTED_LLM_API_KEY (anthropic) or HOSTED_LLM_BASE_URL (openai_compat) in .env"
        )
    if role == "open":
        if s.open_model_endpoint and s.open_model_name:
            return OpenAICompatProvider(base_url=s.open_model_endpoint, model=s.open_model_name,
                                        api_key=s.open_model_api_key, min_interval_s=s.open_model_min_interval_s,
                                        extra_body=s.open_model_extra_body, **common)
        raise ProviderNotConfigured("open model not configured: set OPEN_MODEL_ENDPOINT and OPEN_MODEL_NAME in .env")
    raise ValueError(f"unknown role {role!r}")
