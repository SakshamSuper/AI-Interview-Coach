import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from voice.speech_to_text import audio_transcriber
from voice.text_to_speech import audio_synthesizer
from config.settings import get_settings

router = APIRouter(prefix="/voice", tags=["Voice Interview"])
settings = get_settings()


class SpeakRequest(BaseModel):
    text: str


class SpeakResponse(BaseModel):
    audio_path: str
    text: str


class TranscribeResponse(BaseModel):
    transcript: str
    audio_filename: str


@router.post("/speak", response_model=SpeakResponse)
def speak_question(req: SpeakRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    audio_file = audio_synthesizer.synthesize(req.text)
    return SpeakResponse(audio_path=audio_file, text=req.text)


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_answer(file: UploadFile = File(...)):
    dest_dir = settings.TEMP_MEDIA_DIR
    os.makedirs(dest_dir, exist_ok=True)
    temp_path = os.path.join(dest_dir, f"{uuid.uuid4().hex}_{file.filename}")

    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    transcript = audio_transcriber.transcribe(temp_path)
    return TranscribeResponse(transcript=transcript, audio_filename=file.filename)
