# Stable imports keep diffs readable.
"""OpenAI-compatible chat completion provider service."""

import json
from urllib import request


def _build_headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "rpa-doc-generator/1.0 (+https://localhost)",
    }


def _extract_content(raw: str) -> str:
    data = json.loads(raw)
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )


def invoke_openai_compatible(
    provider_config: dict,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    timeout: int,
) -> str:
    """Invoke a chat completion endpoint that follows OpenAI-compatible API shape."""
    payload = {
        "model": provider_config["model"],
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    endpoint = f"{provider_config['base_url']}/chat/completions"
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=_build_headers(provider_config["api_key"]),
        method="POST",
    )

    with request.urlopen(req, timeout=timeout) as response:  # nosec B310 — scheme validated in provider_router
        raw = response.read().decode("utf-8")
    return _extract_content(raw)
