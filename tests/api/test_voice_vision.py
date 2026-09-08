"""
Tests for voice (STT + TTS) and vision endpoints.

After migration to local faster-whisper:
  - /voice/status     -> 200, always transcription_available=true, + model/device fields
  - /voice/speak      -> 200 (gTTS, no API key needed)
  - /voice/transcribe ->
        400  empty audio
        500  Whisper produces no speech / model load error
        200  successful local transcription
  No OPENAI_API_KEY is required for any of these.
"""

import io
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.backend.main import app
from database.database import init_db

# Non-empty dummy audio blob (112 bytes)
DUMMY_AUDIO = b"RIFF" + bytes(108)


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


# ─── AudioTranscriber unit tests ──────────────────────────────────────────────

class TestAudioTranscriberService:
    """Unit tests for voice/speech_to_text.py — no HTTP layer."""

    def test_is_available_always_true(self):
        """faster-whisper is always available — no API key required."""
        from voice.speech_to_text import AudioTranscriber
        t = AudioTranscriber()
        assert t.is_available is True

    def test_model_name_default(self):
        from voice.speech_to_text import AudioTranscriber
        t = AudioTranscriber()
        assert t.model_name == "small"

    def test_device_default(self):
        from voice.speech_to_text import AudioTranscriber
        t = AudioTranscriber()
        assert t.device == "cpu"

    def test_load_time_none_before_first_use(self):
        from voice.speech_to_text import AudioTranscriber
        t = AudioTranscriber()
        assert t.load_time_seconds is None

    def test_transcribe_raises_if_file_missing(self, tmp_path):
        from voice.speech_to_text import AudioTranscriber
        t = AudioTranscriber()
        with pytest.raises(FileNotFoundError):
            t.transcribe(str(tmp_path / "nonexistent.wav"))

    def test_transcribe_raises_if_file_empty(self, tmp_path):
        from voice.speech_to_text import AudioTranscriber
        empty = tmp_path / "empty.webm"
        empty.write_bytes(b"")
        t = AudioTranscriber()
        with pytest.raises(ValueError, match="empty"):
            t.transcribe(str(empty))

    def test_transcribe_raises_if_model_load_fails(self, tmp_path):
        from voice.speech_to_text import AudioTranscriber
        audio = tmp_path / "audio.webm"
        audio.write_bytes(DUMMY_AUDIO)
        t = AudioTranscriber()
        with patch("faster_whisper.WhisperModel", side_effect=RuntimeError("model not found")):
            with pytest.raises(RuntimeError, match="Could not load"):
                t.transcribe(str(audio))

    def test_transcribe_returns_actual_transcript(self, tmp_path):
        from voice.speech_to_text import AudioTranscriber
        audio = tmp_path / "audio.webm"
        audio.write_bytes(DUMMY_AUDIO)

        expected = "The quick brown fox jumps over the lazy dog."
        mock_seg = MagicMock()
        mock_seg.text = expected
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99

        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = ([mock_seg], mock_info)

        t = AudioTranscriber()
        with patch("faster_whisper.WhisperModel", return_value=mock_model_instance):
            result = t.transcribe(str(audio))

        assert result == expected

    def test_transcribe_raises_on_empty_whisper_output(self, tmp_path):
        from voice.speech_to_text import AudioTranscriber
        audio = tmp_path / "audio.webm"
        audio.write_bytes(DUMMY_AUDIO)

        mock_seg = MagicMock()
        mock_seg.text = "   "   # whitespace only
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.5

        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = ([mock_seg], mock_info)

        t = AudioTranscriber()
        with patch("faster_whisper.WhisperModel", return_value=mock_model_instance):
            with pytest.raises(RuntimeError, match="empty transcript"):
                t.transcribe(str(audio))

    def test_no_fake_transcript_string(self, tmp_path):
        """The old canned transcript must never appear in any error message."""
        from voice.speech_to_text import AudioTranscriber
        FAKE = "distributed microservice architecture"
        audio = tmp_path / "audio.wav"
        audio.write_bytes(DUMMY_AUDIO)

        t = AudioTranscriber()
        # Patch WhisperModel to raise so we verify no fake text leaks into the error
        with patch("faster_whisper.WhisperModel", side_effect=RuntimeError("model not found")):
            try:
                t.transcribe(str(audio))
            except RuntimeError as e:
                assert FAKE not in str(e)


# ─── /voice/status ────────────────────────────────────────────────────────────

def test_voice_status_transcription_always_available(client):
    """faster-whisper: status always reports transcription_available=True."""
    resp = client.get("/voice/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["transcription_available"] is True
    assert "message" in data
    assert "model" in data
    assert "device" in data


def test_voice_status_no_api_key_required(client):
    """Status is available even with OPENAI_API_KEY unset."""
    import os
    original = os.environ.pop("OPENAI_API_KEY", None)
    try:
        resp = client.get("/voice/status")
        assert resp.status_code == 200
        assert resp.json()["transcription_available"] is True
    finally:
        if original is not None:
            os.environ["OPENAI_API_KEY"] = original


# ─── /voice/speak ─────────────────────────────────────────────────────────────

def test_voice_speak_endpoint(client):
    resp = client.post("/voice/speak", json={"text": "Explain Python GIL."})
    assert resp.status_code == 200
    data = resp.json()
    assert "audio_url" in data
    assert "audio_path" in data
    assert data["text"] == "Explain Python GIL."


def test_voice_speak_empty_text(client):
    resp = client.post("/voice/speak", json={"text": "   "})
    assert resp.status_code == 400


# ─── /voice/transcribe: empty audio -> 400 ────────────────────────────────────

def test_voice_transcribe_empty_audio_rejected(client):
    files = {"file": ("empty.webm", io.BytesIO(b""), "audio/webm")}
    resp = client.post("/voice/transcribe", files=files)
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


# ─── /voice/transcribe: successful local transcription -> 200 ─────────────────

def test_voice_transcribe_success_returns_actual_transcript(client):
    """When local Whisper succeeds, the real spoken transcript is returned."""
    expected = "Today I am testing local whisper transcription."
    files = {"file": ("answer.webm", io.BytesIO(DUMMY_AUDIO), "audio/webm")}

    mock_seg = MagicMock()
    mock_seg.text = expected
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.98

    mock_model_instance = MagicMock()
    mock_model_instance.transcribe.return_value = ([mock_seg], mock_info)

    from voice import speech_to_text as stt_module
    original_model = stt_module.audio_transcriber._model
    stt_module.audio_transcriber._model = mock_model_instance
    try:
        resp = client.post("/voice/transcribe", files=files)
    finally:
        stt_module.audio_transcriber._model = original_model

    assert resp.status_code == 200
    data = resp.json()
    assert data["transcript"] == expected
    assert "audio_filename" in data


def test_voice_transcribe_no_fake_fallback(client):
    """The old canned transcript must NEVER appear in any API response."""
    FAKE = "distributed microservice architecture"
    files = {"file": ("answer.webm", io.BytesIO(DUMMY_AUDIO), "audio/webm")}

    # Force model to raise so we can check error response contains no fake text
    mock_model_instance = MagicMock()
    mock_model_instance.transcribe.side_effect = RuntimeError("forced error")

    from voice import speech_to_text as stt_module
    original_model = stt_module.audio_transcriber._model
    stt_module.audio_transcriber._model = mock_model_instance
    try:
        resp = client.post("/voice/transcribe", files=files)
    finally:
        stt_module.audio_transcriber._model = original_model

    assert FAKE not in resp.text


def test_voice_transcribe_whisper_exception_returns_500(client):
    """If Whisper raises an exception, endpoint returns 500 — not 503."""
    files = {"file": ("answer.webm", io.BytesIO(DUMMY_AUDIO), "audio/webm")}

    mock_model_instance = MagicMock()
    mock_model_instance.transcribe.side_effect = Exception("Simulated Whisper error")

    from voice import speech_to_text as stt_module
    original_model = stt_module.audio_transcriber._model
    stt_module.audio_transcriber._model = mock_model_instance
    try:
        resp = client.post("/voice/transcribe", files=files)
    finally:
        stt_module.audio_transcriber._model = original_model

    assert resp.status_code == 500
    # Must never be 503 (that was the old OpenAI-key-missing code)
    assert resp.status_code != 503


def test_voice_transcribe_silent_audio_returns_500(client):
    """Whisper returning whitespace-only -> 500 with 'empty transcript' message."""
    files = {"file": ("answer.webm", io.BytesIO(DUMMY_AUDIO), "audio/webm")}

    mock_seg = MagicMock()
    mock_seg.text = "   "
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.1

    mock_model_instance = MagicMock()
    mock_model_instance.transcribe.return_value = ([mock_seg], mock_info)

    from voice import speech_to_text as stt_module
    original_model = stt_module.audio_transcriber._model
    stt_module.audio_transcriber._model = mock_model_instance
    try:
        resp = client.post("/voice/transcribe", files=files)
    finally:
        stt_module.audio_transcriber._model = original_model

    assert resp.status_code == 500
    assert "empty" in resp.json()["detail"].lower()


# ─── Vision endpoint (existing, untouched) ────────────────────────────────────

def test_vision_analyze_endpoint(client):
    start_resp = client.post("/interviews/start", json={"target_role": "Backend Engineer", "total_questions": 1})
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    vision_resp = client.post("/vision/analyze", json={"session_id": session_id, "frame_count": 20})
    assert vision_resp.status_code == 200
    vdata = vision_resp.json()
    assert vdata["session_id"] == session_id
    assert vdata["frame_count"] == 20
    assert 0 <= vdata["avg_posture_stability"] <= 100
    assert len(vdata["objective_observations"]) > 0

    obs_text = " ".join(vdata["objective_observations"]).lower()
    assert "nervous" not in obs_text
    assert "anxious" not in obs_text
    assert "personality" not in obs_text

