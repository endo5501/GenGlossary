"""Tests for LLM client factory."""

from unittest.mock import patch

import pytest

from genglossary.llm.factory import create_llm_client


class TestCreateLLMClientBaseUrl:
    """Tests for base_url parameter propagation."""

    def test_ollama_uses_provided_base_url(self) -> None:
        """Ollamaプロバイダでbase_urlを指定した場合、その値が使用される"""
        custom_url = "http://192.168.1.100:11434"

        with patch("genglossary.llm.factory.OllamaClient") as mock_ollama:
            create_llm_client(provider="ollama", base_url=custom_url)

            mock_ollama.assert_called_once()
            call_kwargs = mock_ollama.call_args.kwargs
            assert call_kwargs["base_url"] == custom_url

    def test_ollama_uses_config_default_when_base_url_not_provided(self) -> None:
        """Ollamaプロバイダでbase_urlを指定しない場合、Configのデフォルト値が使用される"""
        with patch("genglossary.llm.factory.OllamaClient") as mock_ollama, \
             patch("genglossary.llm.factory.Config") as mock_config:
            mock_config.return_value.ollama_base_url = "http://config-default:11434"

            create_llm_client(provider="ollama", base_url=None)

            mock_ollama.assert_called_once()
            call_kwargs = mock_ollama.call_args.kwargs
            assert call_kwargs["base_url"] == "http://config-default:11434"

    def test_openai_uses_provided_base_url(self) -> None:
        """OpenAIプロバイダでbase_urlを指定した場合、その値が使用される"""
        custom_url = "http://127.0.0.1:8080/v1"

        with patch("genglossary.llm.factory.OpenAICompatibleClient") as mock_openai, \
             patch("genglossary.llm.factory.Config") as mock_config:
            mock_config.return_value.openai_api_key = "test-key"
            mock_config.return_value.openai_model = "gpt-4"
            mock_config.return_value.azure_openai_api_version = None

            create_llm_client(provider="openai", base_url=custom_url)

            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args.kwargs
            assert call_kwargs["base_url"] == custom_url

    def test_openai_uses_config_default_when_base_url_not_provided(self) -> None:
        """OpenAIプロバイダでbase_urlを指定しない場合、Configのデフォルト値が使用される"""
        with patch("genglossary.llm.factory.OpenAICompatibleClient") as mock_openai, \
             patch("genglossary.llm.factory.Config") as mock_config:
            mock_config.return_value.openai_base_url = "https://api.openai.com/v1"
            mock_config.return_value.openai_api_key = "test-key"
            mock_config.return_value.openai_model = "gpt-4"
            mock_config.return_value.azure_openai_api_version = None

            create_llm_client(provider="openai", base_url=None)

            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args.kwargs
            assert call_kwargs["base_url"] == "https://api.openai.com/v1"
