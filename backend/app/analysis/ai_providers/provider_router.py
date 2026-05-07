# Thin entry points reduce coupling.
"""AI provider routing based on configured credentials and model settings."""

from app.analysis.ai_providers.bedrock_service import invoke_bedrock
from app.analysis.ai_providers.openai_compatible_service import invoke_openai_compatible


def _validate_base_url(url: str, label: str) -> str:
    """Validate that the provider base URL uses an allowed scheme (https or http)."""
    if not url.startswith(("https://", "http://")):
        raise ValueError(
            f"Invalid {label} base URL scheme. Only 'https://' and 'http://' are allowed."
        )
    return url


def resolve_ai_provider_config(settings) -> dict:
    """Resolve active provider by priority: Groq, Bedrock, then OpenAI-compatible."""
    if settings.groq_api_key:
        return {
            "provider": "groq",
            "api_key": settings.groq_api_key,
            "model": settings.groq_model,
            "base_url": _validate_base_url(settings.groq_base_url, "GROQ_BASE_URL"),
        }

    if settings.bedrock_model_id:
        return {
            "provider": "bedrock",
            "api_key": "",
            "model": settings.bedrock_model_id,
            "region": settings.bedrock_region,
            "profile_name": settings.bedrock_profile_name,
            "access_key_id": settings.bedrock_access_key_id,
            "secret_access_key": settings.bedrock_secret_access_key,
            "session_token": settings.bedrock_session_token,
        }

    return {
        "provider": "openai-compatible",
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "base_url": _validate_base_url(settings.openai_base_url, "OPENAI_BASE_URL"),
    }


def has_provider_credentials(provider_config: dict) -> bool:
    """Return whether selected provider has enough credentials/config to be invoked."""
    if provider_config.get("provider") == "bedrock":
        return bool(provider_config.get("model"))
    return bool(provider_config.get("api_key"))


def invoke_ai(
    provider_config: dict,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: int,
) -> str:
    """Dispatch invocation to the corresponding provider service implementation."""
    if provider_config.get("provider") == "bedrock":
        return invoke_bedrock(provider_config, system_prompt, user_prompt, temperature, timeout)
    return invoke_openai_compatible(provider_config, system_prompt, user_prompt, temperature, timeout)
