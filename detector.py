
import subprocess
import numpy as np
import streamlit as st
import imageio_ffmpeg
from transformers import pipeline

MODEL_NAME = "MelodyMachine/Deepfake-audio-detection"

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_DURATION_SECONDS = 30
MIN_DURATION_SECONDS = 1


@st.cache_resource(show_spinner="Loading the AI model...")
def load_detector():
    """Load the AI model once."""
    return pipeline(
        task="audio-classification",
        model=MODEL_NAME,
        device=-1,
    )


def decode_audio(audio_bytes, target_sample_rate):
    """Decode MPEG, MP3, WAV and other FFmpeg-supported audio formats."""

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-vn",
        "-ac", "1",
        "-ar", str(target_sample_rate),
        "-f", "f32le",
        "-acodec", "pcm_f32le",
        "pipe:1",
    ]

    try:
        result = subprocess.run(
            command,
            input=audio_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(
            "Audio decoding timed out. Try a shorter audio file."
        ) from error
    except Exception as error:
        raise RuntimeError(
            f"Could not start the audio decoder: {error}"
        ) from error

    if result.returncode != 0 or not result.stdout:
        details = result.stderr.decode(
            "utf-8", errors="replace"
        ).strip()

        raise ValueError(
            "Could not decode this audio file. "
            "It may be malformed or use an unsupported codec. "
            f"Decoder details: {details[-1000:]}"
        )

    # FFmpeg outputs 32-bit floating-point mono audio.
    audio = np.frombuffer(result.stdout, dtype="<f4").copy()

    if audio.size == 0:
        raise ValueError("No audio samples were decoded.")

    if not np.all(np.isfinite(audio)):
        raise ValueError("The decoded audio contains invalid values.")

    return audio


def analyze_audio(uploaded_file):
    """Validate, decode and classify uploaded audio."""

    if uploaded_file is None:
        raise ValueError("Please upload an audio file.")

    audio_bytes = uploaded_file.getvalue()

    if not audio_bytes:
        raise ValueError("The uploaded file is empty.")

    if len(audio_bytes) > MAX_FILE_BYTES:
        raise ValueError("The file must be 10 MB or smaller.")

    # Load model to get its expected sample rate.
    model = load_detector()
    sample_rate = int(model.feature_extractor.sampling_rate)

    # Decode the original file, including supported MPEG/MP3 formats.
    audio = decode_audio(audio_bytes, sample_rate)

    duration = len(audio) / sample_rate

    if duration < MIN_DURATION_SECONDS:
        raise ValueError("Audio must be at least 1 second long.")

    if duration > MAX_DURATION_SECONDS:
        raise ValueError("Audio must be 30 seconds or shorter.")

    # Send decoded audio directly to the model.
    predictions = model(
        {
            "raw": audio,
            "sampling_rate": sample_rate,
        },
        top_k=None,
    )

    if not predictions:
        raise RuntimeError("The model returned no predictions.")

    return {
        "predictions": predictions,
        "duration": float(duration),
        "sample_rate": sample_rate,
        "channels": 1,
    }
