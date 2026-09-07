import os
import wave
import struct
import math
from typing import Optional
from config.settings import get_settings
from config.logger import logger

settings = get_settings()


class AudioSynthesizer:
    """Synthesizes interview questions to spoken audio."""

    def synthesize(self, text: str, output_path: str = None) -> str:
        dest_dir = settings.TEMP_MEDIA_DIR
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = output_path or os.path.join(dest_dir, f"question_speech_{abs(hash(text)) % 100000}.mp3")

        # 1. Try gTTS
        try:
            from gtts import gTTS
            tts = gTTS(text=text[:300], lang="en", slow=False)
            tts.save(dest_path)
            logger.info(f"Synthesized question speech via gTTS to: {dest_path}")
            return dest_path
        except Exception as e:
            logger.warning(f"gTTS synthesis failed ({e}). Generating fallback WAV audio.")

        # 2. Offline audio synthesis fallback: generate pure PCM audio wav file
        wav_path = dest_path.replace(".mp3", ".wav")
        sample_rate = 16000
        duration_sec = 2.0
        num_samples = int(sample_rate * duration_sec)

        with wave.open(wav_path, "w") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            # Generate gentle chime tone
            for i in range(num_samples):
                t = float(i) / sample_rate
                value = int(10000.0 * math.sin(2.0 * math.pi * 440.0 * t) * math.exp(-2.0 * t))
                data = struct.pack("<h", value)
                wav_file.writeframesraw(data)

        logger.info(f"Generated offline audio chime: {wav_path}")
        return wav_path


audio_synthesizer = AudioSynthesizer()
