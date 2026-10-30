import base64
import json
import os
import tempfile
import pytest
from unittest import mock
import requests

from backend.schemas import Label
from backend.gemma import (
    extract_label,
    generate_explanation,
    _call_ollama_chat,
    OllamaModelNotFoundError,
)


MOCK_LABEL_JSON = {
    "product_name": {"text": "Rogor 30 EC", "found": True},
    "active_ingredient": {"text": "Dimethoate 30% w/w", "found": True},
    "crops_listed": {"text": "Cotton, Wheat, Mustard", "found": True},
    "protective_gear": {"text": "Gloves and protective glasses", "found": True},
    "first_aid": {"text": "In case of ingestion induce vomiting", "found": True},
    "waiting_period": {"text": "14 days", "found": True},
}

MOCK_EXPLANATION_JSON = {
    "english": "Rogor 30 EC is effective for Cotton, Wheat, and Mustard. Wait 14 days before harvest.",
    "hindi": "रोगोर 30 ईसी कपास, गेहूं और सरसों के लिए उपयोगी है। कटाई से 14 दिन पहले छिड़काव रोक दें।",
}


@pytest.fixture
def sample_image():
    temp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    temp.write(b"fake_image_bytes_12345")
    temp.close()
    yield temp.name
    if os.path.exists(temp.name):
        os.remove(temp.name)


class TestGemmaOllama:
    def test_extract_label_successful_call_and_base64_image(self, sample_image):
        """Verify the uploaded image is converted to base64 and sent to Ollama."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": json.dumps(MOCK_LABEL_JSON),
            }
        }

        with mock.patch("requests.post", return_value=mock_response) as mock_post:
            result = extract_label(sample_image, mime_type="image/jpeg")

            assert isinstance(result, Label)
            assert result.product_name.text == "Rogor 30 EC"
            assert result.product_name.found is True
            assert result.waiting_period.text == "14 days"

            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args[1]
            payload = call_kwargs["json"]

            assert payload["model"] == "gemma3:4b"
            assert payload["format"] == "json"

            # Verify image base64
            user_msg = payload["messages"][1]
            assert "images" in user_msg
            with open(sample_image, "rb") as f:
                expected_b64 = base64.b64encode(f.read()).decode("utf-8")
            assert user_msg["images"] == [expected_b64]

    def test_second_call_generate_explanation(self):
        """Verify the second AI call generates English and Hindi explanations."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": json.dumps(MOCK_EXPLANATION_JSON),
            }
        }

        with mock.patch("requests.post", return_value=mock_response) as mock_post:
            explanation = generate_explanation(
                label=MOCK_LABEL_JSON,
                crop="Cotton",
                spray_date="2026-10-30",
            )

            assert "Rogor 30 EC" in explanation["english"]
            assert "रोगोर" in explanation["hindi"]

            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert "Cotton" in payload["messages"][1]["content"]
            assert "2026-10-30" in payload["messages"][1]["content"]

    def test_error_handling_when_ollama_not_running(self, sample_image):
        """Verify a clean ConnectionError is raised when Ollama is unreachable."""
        with mock.patch("requests.post", side_effect=requests.exceptions.ConnectionError("Connection refused")):
            with pytest.raises(ConnectionError) as exc_info:
                extract_label(sample_image)
            assert "Ollama server is not running or unreachable" in str(exc_info.value)

    def test_error_handling_when_model_missing_404(self, sample_image):
        """Verify OllamaModelNotFoundError is raised when the requested model is not found (HTTP 404)."""
        mock_404 = mock.Mock()
        mock_404.status_code = 404
        mock_404.text = "model 'gemma3:4b' not found"

        with mock.patch("requests.post", return_value=mock_404):
            with pytest.raises(OllamaModelNotFoundError) as exc_info:
                extract_label(sample_image)
            assert "was not found" in str(exc_info.value)
            assert "ollama pull" in str(exc_info.value)

    def test_retry_on_malformed_json_then_success(self, sample_image):
        """Verify that parsing failure retries exactly once."""
        mock_fail = mock.Mock()
        mock_fail.status_code = 200
        mock_fail.json.return_value = {"message": {"content": "not valid json"}}

        mock_ok = mock.Mock()
        mock_ok.status_code = 200
        mock_ok.json.return_value = {
            "message": {"content": json.dumps(MOCK_LABEL_JSON)}
        }

        with mock.patch("requests.post", side_effect=[mock_fail, mock_ok]) as mock_post:
            result = extract_label(sample_image)
            assert result.product_name.text == "Rogor 30 EC"
            assert mock_post.call_count == 2
