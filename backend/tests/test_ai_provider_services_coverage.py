# Reusable seams aid maintenance.
"""Coverage tests for AI provider service helpers."""

from __future__ import annotations

import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.analysis.ai_providers.bedrock_service import invoke_bedrock
from app.analysis.ai_providers.provider_router import _validate_base_url, resolve_ai_provider_config


class _FakeConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class BedrockServiceCoverageTests(unittest.TestCase):
    def test_should_return_empty_string_when_boto3_import_fails(self):
        real_import = __import__

        def _import_hook(name, globals=None, locals=None, fromlist=(), level=0):
            if name in {"boto3", "botocore.config"}:
                raise ImportError("simulated missing dependency")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=_import_hook):
            output = invoke_bedrock(
                provider_config={"model": "model-id"},
                system_prompt="sys",
                user_prompt="usr",
                temperature=0.1,
                timeout=8,
            )

        self.assertEqual(output, "")

    def test_should_invoke_direct_client_when_access_keys_are_present(self):
        captured = {"client_kwargs": None}

        class _FakeClient:
            def converse(self, **kwargs):
                captured["converse_kwargs"] = kwargs
                return {
                    "output": {
                        "message": {
                            "content": [
                                {"text": "line-a"},
                                "not-a-dict",
                                {"text": "line-b"},
                                {"text": ""},
                            ]
                        }
                    }
                }

        def _client(name, **kwargs):
            captured["client_name"] = name
            captured["client_kwargs"] = kwargs
            return _FakeClient()

        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.client = _client
        fake_boto3.session = SimpleNamespace(Session=lambda **_: None)

        fake_botocore = types.ModuleType("botocore")
        fake_botocore_config = types.ModuleType("botocore.config")
        fake_botocore_config.Config = _FakeConfig

        with patch.dict(
            "sys.modules",
            {
                "boto3": fake_boto3,
                "botocore": fake_botocore,
                "botocore.config": fake_botocore_config,
            },
            clear=False,
        ):
            output = invoke_bedrock(
                provider_config={
                    "model": "anthropic.claude",
                    "region": "us-east-2",
                    "access_key_id": "AKIA",
                    "secret_access_key": "SECRET",
                    "session_token": "TOKEN",
                },
                system_prompt="system-msg",
                user_prompt="user-msg",
                temperature=0.3,
                timeout=12,
            )

        self.assertEqual(output, "line-a\nline-b")
        self.assertEqual(captured["client_name"], "bedrock-runtime")
        self.assertEqual(captured["client_kwargs"]["region_name"], "us-east-2")
        self.assertEqual(captured["client_kwargs"]["aws_access_key_id"], "AKIA")
        self.assertEqual(captured["client_kwargs"]["aws_secret_access_key"], "SECRET")
        self.assertEqual(captured["client_kwargs"]["aws_session_token"], "TOKEN")
        self.assertEqual(captured["converse_kwargs"]["modelId"], "anthropic.claude")

    def test_should_use_profile_session_when_profile_is_set_without_keys(self):
        captured = {"session_args": None, "session_client_args": None}

        class _FakeClient:
            def converse(self, **kwargs):
                captured["converse_kwargs"] = kwargs
                return {"output": {"message": {"content": [{"text": "profile-path"}]}}}

        class _FakeSession:
            def __init__(self, profile_name: str, region_name: str):
                captured["session_args"] = {"profile_name": profile_name, "region_name": region_name}

            def client(self, name: str, config):
                captured["session_client_args"] = {"name": name, "config": config}
                return _FakeClient()

        fake_boto3 = types.ModuleType("boto3")
        fake_boto3.client = lambda *_args, **_kwargs: None
        fake_boto3.session = SimpleNamespace(Session=_FakeSession)

        fake_botocore = types.ModuleType("botocore")
        fake_botocore_config = types.ModuleType("botocore.config")
        fake_botocore_config.Config = _FakeConfig

        with patch.dict(
            "sys.modules",
            {
                "boto3": fake_boto3,
                "botocore": fake_botocore,
                "botocore.config": fake_botocore_config,
            },
            clear=False,
        ):
            output = invoke_bedrock(
                provider_config={
                    "model": "anthropic.claude",
                    "region": "us-west-1",
                    "profile_name": "my-profile",
                    "access_key_id": "",
                    "secret_access_key": "",
                    "session_token": "",
                },
                system_prompt="system-msg",
                user_prompt="user-msg",
                temperature=0.4,
                timeout=9,
            )

        self.assertEqual(output, "profile-path")
        self.assertEqual(
            captured["session_args"], {"profile_name": "my-profile", "region_name": "us-west-1"}
        )
        self.assertEqual(captured["session_client_args"]["name"], "bedrock-runtime")


class ProviderRouterCoverageTests(unittest.TestCase):
    def test_should_raise_value_error_when_base_url_scheme_is_invalid(self):
        with self.assertRaises(ValueError):
            _validate_base_url("ftp://invalid", "OPENAI_BASE_URL")

    def test_should_resolve_openai_provider_when_no_other_credentials_exist(self):
        settings = SimpleNamespace(
            groq_api_key="",
            groq_model="llm-a",
            groq_base_url="https://api.groq.com/openai/v1",
            bedrock_model_id="",
            bedrock_region="us-east-1",
            bedrock_profile_name="",
            bedrock_access_key_id="",
            bedrock_secret_access_key="",
            bedrock_session_token="",
            openai_api_key="openai-key",
            openai_model="gpt-4o-mini",
            openai_base_url="https://api.openai.com/v1",
        )

        config = resolve_ai_provider_config(settings)

        self.assertEqual(config["provider"], "openai-compatible")
        self.assertEqual(config["api_key"], "openai-key")
