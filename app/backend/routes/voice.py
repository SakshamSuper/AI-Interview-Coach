import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from voice.speech_to_text import audio_transcriber
from voice.text_to_speech import audio_synthesizer
from config.settings import get_settings

router = APIRouter(prefix="/voice", tags=["Voice Interview"])
settings = get_settings()


class SpeakRequest(BaseModel):
    text: str


class SpeakResponse(BaseModel):
    audio_url: str   # browser-accessible URL: /voice/audio/<filename>
    audio_path: str  # server-side path (kept for backwards-compat)
    text: str


class TranscribeResponse(BaseModel):
    transcript: str
    audio_filename: str


@router.post("/speak", response_model=SpeakResponse)
def speak_question(req: SpeakRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    audio_file = audio_synthesizer.synthesize(req.text)
    filename = os.path.basename(audio_file)
    return SpeakResponse(
        audio_url=f"/voice/audio/{filename}",
        audio_path=audio_file,
        text=req.text,
    )


@router.get("/audio/{filename}")
def serve_audio(filename: str):
    """Serve a generated TTS audio file to the browser by filename only.
    The full filesystem path is never exposed; only the basename is accepted.
    Rejects path traversal attempts.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    file_path = os.path.join(settings.TEMP_MEDIA_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(file_path, media_type=media_type)


@router.get("/status")
def voice_status():
    """
    Report transcription availability and model configuration.
    With faster-whisper, transcription is always available locally —
    no API key is required.
    """
    return {
        "transcription_available": audio_transcriber.is_available,
        "model": audio_transcriber.model_name,
        "device": audio_transcriber.device,
        "message": (
            f"Local Whisper transcription available "
            f"(model={audio_transcriber.model_name}, device={audio_transcriber.device})."
        ),
    }


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_answer(file: UploadFile = File(...)):
    dest_dir = settings.TEMP_MEDIA_DIR
    os.makedirs(dest_dir, exist_ok=True)

    content = await file.read()

    # Reject empty uploads immediately — saves a disk write
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Audio file is empty. No audio data was received. "
                   "Check that the microphone recorded audio before stopping.",
        )

    temp_path = os.path.join(dest_dir, f"{uuid.uuid4().hex}_{file.filename or 'audio'}")
    with open(temp_path, "wb") as f:
        f.write(content)

    try:
        transcript = audio_transcriber.transcribe(temp_path)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {e}")
    finally:
        # Clean up the temp file regardless of outcome
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return TranscribeResponse(transcript=transcript, audio_filename=file.filename or "audio")
