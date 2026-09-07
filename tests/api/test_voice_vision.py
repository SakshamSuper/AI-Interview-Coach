import io
import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from database.database import init_db


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def test_voice_speak_endpoint(client):
    resp = client.post("/voice/speak", json={"text": "Explain Python GIL."})
    assert resp.status_code == 200
    data = resp.json()
    assert "audio_path" in data
    assert data["text"] == "Explain Python GIL."


def test_voice_transcribe_endpoint(client):
    dummy_wav = b"RIFF....WAVEfmt ...."
    files = {"file": ("answer.wav", io.BytesIO(dummy_wav), "audio/wav")}
    resp = client.post("/voice/transcribe", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert "transcript" in data
    assert len(data["transcript"]) > 0


def test_vision_analyze_endpoint(client):
    # First create a session
    start_resp = client.post("/interviews/start", json={"target_role": "Backend Engineer", "total_questions": 1})
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # Call vision analysis
    vision_resp = client.post("/vision/analyze", json={"session_id": session_id, "frame_count": 20})
    assert vision_resp.status_code == 200
    vdata = vision_resp.json()
    assert vdata["session_id"] == session_id
    assert vdata["frame_count"] == 20
    assert 0 <= vdata["avg_posture_stability"] <= 100
    assert len(vdata["objective_observations"]) > 0

    # Verify Responsible AI compliance: observations must never claim psychological states
    obs_text = " ".join(vdata["objective_observations"]).lower()
    assert "nervous" not in obs_text
    assert "anxious" not in obs_text
    assert "personality" not in obs_text
