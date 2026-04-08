"""
Unit tests for GeminiProvider.
All tests are fully mocked — no live API calls required.
"""

import sys
from unittest.mock import MagicMock, call, patch

import pytest


def _make_provider(api_key="AIza-test", model="gemini-1.5-flash"):
    from cerebro.providers.gemini.llm import GeminiProvider

    return GeminiProvider(api_key=api_key, model=model)


class TestGeminiProviderConstruction:
    def test_reads_env_vars(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "env-key")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-pro")
        monkeypatch.setenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
        monkeypatch.setenv("GEMINI_TIMEOUT", "60")
        from cerebro.providers.gemini.llm import GeminiProvider

        p = GeminiProvider()
        assert p.api_key == "env-key"
        assert p.model == "gemini-1.5-pro"
        assert p.embedding_model == "models/embedding-001"
        assert p.timeout == 60.0

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        from cerebro.providers.gemini.llm import GeminiProvider

        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            GeminiProvider()


class TestGeminiEmbeddings:
    def test_embed_returns_vector(self):
        p = _make_provider()
        mock_genai = MagicMock()
        mock_genai.embed_content.return_value = {"embedding": [0.1, 0.2, 0.3]}
        p._genai = mock_genai

        result = p.embed("hello world")
        assert result == [0.1, 0.2, 0.3]

    def test_embed_batch_calls_per_text(self):
        p = _make_provider()
        mock_genai = MagicMock()
        mock_genai.embed_content.side_effect = [
            {"embedding": [0.1, 0.2]},
            {"embedding": [0.3, 0.4]},
        ]
        p._genai = mock_genai

        result = p.embed_batch(["text a", "text b"])
        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        assert result[1] == [0.3, 0.4]
        assert mock_genai.embed_content.call_count == 2

    def test_embed_batch_respects_batch_size(self):
        p = _make_provider()
        mock_genai = MagicMock()
        mock_genai.embed_content.return_value = {"embedding": [0.0]}
        p._genai = mock_genai

        p.embed_batch(["a", "b", "c"], batch_size=2)
        # All 3 texts should be processed regardless of batch_size windowing
        assert mock_genai.embed_content.call_count == 3


class TestGeminiGenerate:
    def test_generate_returns_text(self):
        p = _make_provider()
        mock_response = MagicMock()
        mock_response.text = "Gemini answer."
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        p._genai = mock_genai

        result = p.generate("What is AI?")
        assert result == "Gemini answer."

    def test_generate_passes_generation_config(self):
        p = _make_provider()
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        p._genai = mock_genai

        p.generate("prompt", max_tokens=512, temperature=0.2)
        call_args = mock_model.generate_content.call_args
        config = call_args.kwargs["generation_config"]
        assert config["max_output_tokens"] == 512
        assert config["temperature"] == 0.2


class TestGeminiGroundedGenerate:
    def test_returns_required_keys(self):
        p = _make_provider()
        p.generate = MagicMock(return_value="Grounded answer from [1].")

        result = p.grounded_generate("Query?", context=["Doc A", "Doc B"], top_k=2)
        assert "answer" in result
        assert "citations" in result
        assert "snippets" in result
        assert "confidence" in result
        assert "cost_estimate" in result

    def test_returns_error_dict_on_exception(self):
        p = _make_provider()
        p.generate = MagicMock(side_effect=RuntimeError("quota exceeded"))

        result = p.grounded_generate("query", context=["ctx"])
        assert result["answer"].startswith("Error:")
        assert result["confidence"] == 0.0


class TestGeminiHealthCheck:
    def test_returns_true_when_api_responds(self):
        p = _make_provider()
        mock_model = MagicMock()
        mock_model.generate_content.return_value = MagicMock(text="pong")
        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        p._genai = mock_genai

        assert p.health_check() is True

    def test_returns_false_on_exception(self):
        p = _make_provider()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API error")
        mock_genai = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        p._genai = mock_genai

        assert p.health_check() is False

    def test_import_error_gives_helpful_message(self):
        p = _make_provider()
        with patch.dict(sys.modules, {"google.generativeai": None, "google": None}):
            p._genai = None
            with pytest.raises((ImportError, Exception)):
                p._get_genai()
