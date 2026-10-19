
import os
import tempfile

import soundfile as sf
import streamlit as st
from transformers import pipeline

MODEL_NAME = "MelodyMachine/Deepfake-audio-detection"

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_DURATION_SECONDS = 30
MIN_DURATION_SECONDS = 1


@st.cache_resource(show_spinner="Loading the AI model...")
def load_detector():
    """Load the pretrained audio classifier once."""
    return pipeline(
        task="audio-classification",
        model=MODEL_NAME,
        device=-1,
    )


def analyze_audio(uploaded_file):
    """Validate a WAV recording and classify it."""

    if uploaded_file is None:
        raise ValueError("Please upload a WAV file.")

    audio_bytes = uploaded_file.getvalue()

    if not audio_bytes:
        raise ValueError("The file is empty.")

    if len(audio_bytes) > MAX_FILE_BYTES:
        raise ValueError("The file must be 10 MB or smaller.")

    temp_path = None

    try:
        # Save the uploaded bytes to a temporary WAV file.
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        # Validate the audio file before sending it to the model.
        with sf.SoundFile(temp_path) as audio:
            sample_rate = audio.samplerate
            frames = len(audio)
            channels = audio.channels
            duration = frames / sample_rate

        if duration < MIN_DURATION_SECONDS:
            raise ValueError(
                "Audio must be at least 1 second long."
            )

        if duration > MAX_DURATION_SECONDS:
            raise ValueError(
                "Audio must be 30 seconds or shorter."
            )

        if sample_rate < 8000 or sample_rate > 96000:
            raise ValueError(
                "Sample rate must be between 8000 and 96000 Hz."
            )

        # Run the pretrained classifier.
        model = load_detector()
        predictions = model(temp_path, top_k=None)

        if not predictions:
            raise RuntimeError("The model returned no predictions.")

        return {
            "predictions": predictions,
            "duration": duration,
            "sample_rate": sample_rate,
            "channels": channels,
        }

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            "Audio analysis failed. Check the WAV file, internet "
            "connection, model availability, and terminal logs."
        ) from error

    finally:
        # Remove the temporary audio file.
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
