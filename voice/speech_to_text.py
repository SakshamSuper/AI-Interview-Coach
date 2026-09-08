"""
Local speech-to-text transcription using faster-whisper.

No API key required. All audio processing happens on-device.
The Whisper model is downloaded from HuggingFace on first use and cached.
Subsequent requests use the in-memory cached model.
"""

import os
import time
import threading
from typing import Optional

from config.settings import get_settings
from config.logger import logger

settings = get_settings()

# Module-level lock prevents multiple threads loading the model simultaneously
_model_lock = threading.Lock()


class AudioTranscriber:
    """
    Transcribes spoken audio to text using faster-whisper (CTranslate2 backend).

    Configuration (via .env / environment):
        WHISPER_MODEL        — model size: tiny, base, small (default), medium,
                               large-v2, large-v3
        WHISPER_DEVICE       — cpu (default) or cuda
        WHISPER_COMPUTE_TYPE — int8 (default/cpu), float16 (cuda), float32
    """

    def __init__(self) -> None:
        self._model = None          # loaded lazily on first transcription
        self._model_name: str = settings.WHISPER_MODEL
        self._device: str = settings.WHISPER_DEVICE
        self._compute_type: str = settings.WHISPER_COMPUTE_TYPE
        self._load_time_s: Optional[float] = None
        logger.info(
            f"AudioTranscriber configured: model={self._model_name} "
            f"device={self._device} compute_type={self._compute_type}"
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def is_available(self) -> bool:
        """Always True — faster-whisper runs locally without any API key."""
        return True

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def device(self) -> str:
        return self._device

    @property
    def load_time_seconds(self) -> Optional[float]:
        """Wall-clock seconds spent loading the model (None if not yet loaded)."""
        return self._load_time_s

    # ------------------------------------------------------------------
    # Internal model loader (thread-safe, lazy)
    # ------------------------------------------------------------------

    def _get_model(self):
        """Return the cached WhisperModel, loading it on first call."""
        if self._model is not None:
            return self._model

        with _model_lock:
            if self._model is not None:   # double-checked locking
                return self._model

            logger.info(
                f"Loading faster-whisper model '{self._model_name}' "
                f"(device={self._device}, compute_type={self._compute_type}). "
                "First use may download model weights from HuggingFace (~140 MB for 'small')."
            )
            t0 = time.perf_counter()
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self._model_name,
                    device=self._device,
                    compute_type=self._compute_type,
                )
                self._load_time_s = time.perf_counter() - t0
                logger.info(
                    f"faster-whisper model '{self._model_name}' loaded in "
                    f"{self._load_time_s:.2f}s."
                )
            except Exception as exc:
                logger.error(f"Failed to load faster-whisper model: {exc}")
                raise RuntimeError(
                    f"Could not load Whisper model '{self._model_name}': {exc}"
                ) from exc

        return self._model

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file to text using faster-whisper locally.

        Accepts any format supported by PyAV (WAV, WebM, OGG, MP4, FLAC, …).

        Args:
            audio_file_path: Absolute or relative path to the audio file.

        Returns:
            Transcribed text string (stripped, non-empty).

        Raises:
            FileNotFoundError: Audio file path does not exist.
            ValueError:        Audio file is empty (0 bytes).
            RuntimeError:      Model failed to load, or transcription produced
                               no speech.
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            raise ValueError(
                "Audio file is empty (0 bytes). "
                "Ensure the microphone was active before stopping the recording."
            )

        logger.info(
            f"Transcribing audio: {audio_file_path} ({file_size} bytes)"
        )

        model = self._get_model()
        t0 = time.perf_counter()
        try:
            segments, info = model.transcribe(
                audio_file_path,
                beam_size=5,
                language=None,          # auto-detect language
                vad_filter=True,        # skip silent regions
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            # segments is a generator — consume it to get all text
            text = " ".join(seg.text.strip() for seg in segments).strip()
        except Exception as exc:
            logger.error(f"faster-whisper transcription error: {exc}")
            raise RuntimeError(f"Transcription failed: {exc}") from exc

        elapsed = time.perf_counter() - t0
        logger.info(
            f"Transcription complete in {elapsed:.2f}s. "
            f"Detected language: {info.language} (prob={info.language_probability:.2f}). "
            f"Transcript length: {len(text)} chars."
        )

        if not text:
            raise RuntimeError(
                "Whisper returned an empty transcript. "
                "The recording may have been silent or too short."
            )

        return text


# Module-level singleton — imported by voice route and tests
audio_transcriber = AudioTranscriber()
