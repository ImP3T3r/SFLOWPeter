import io
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL


class Transcriber:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def transcribe(self, wav_buffer: io.BytesIO) -> str:
        """Send WAV audio to Groq Whisper and return transcribed text."""
        wav_buffer.seek(0)
        data = wav_buffer.read()
        if len(data) < 100:
            return ""
        transcription = self.client.audio.transcriptions.create(
            file=("recording.wav", data),
            model=GROQ_MODEL,
            response_format="text",
            temperature=0.0,
        )
        text = transcription.strip() if isinstance(transcription, str) else str(transcription).strip()
        return text
