"""AWS Bedrock provider service using Converse API."""

import logging

logger = logging.getLogger(__name__)


def invoke_bedrock(
    provider_config: dict,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: int,
) -> str:
    """Invoke Bedrock Converse API and return joined text content blocks."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        logger.warning("boto3 is not installed. Bedrock provider cannot be used.")
        return ""

    region = provider_config.get("region") or "us-east-1"
    profile_name = provider_config.get("profile_name", "").strip()
    access_key_id = provider_config.get("access_key_id", "").strip()
    secret_access_key = provider_config.get("secret_access_key", "").strip()
    session_token = provider_config.get("session_token", "").strip()

    config = Config(
        read_timeout=timeout,
        connect_timeout=min(timeout, 10),
        retries={"max_attempts": 2, "mode": "standard"},
    )

    client_kwargs = {"region_name": region, "config": config}
    if access_key_id and secret_access_key:
        client_kwargs["aws_access_key_id"] = access_key_id
        client_kwargs["aws_secret_access_key"] = secret_access_key
        if session_token:
            client_kwargs["aws_session_token"] = session_token

    if profile_name and not (access_key_id and secret_access_key):
        session = boto3.session.Session(profile_name=profile_name, region_name=region)
        client = session.client("bedrock-runtime", config=config)
    else:
        client = boto3.client("bedrock-runtime", **client_kwargs)

    response = client.converse(
        modelId=provider_config["model"],
        system=[{"text": system_prompt}],
        messages=[
            {
                "role": "user",
                "content": [{"text": user_prompt}],
            }
        ],
        inferenceConfig={"temperature": temperature},
    )

    content_blocks = response.get("output", {}).get("message", {}).get("content", [])
    texts = [block.get("text", "") for block in content_blocks if isinstance(block, dict)]
    return "\n".join(text for text in texts if text).strip()
