
import os

import streamlit as st

from detector import analyze_audio
from database import initialize_database, save_analysis, get_history
from safety import get_prevention_advice


st.set_page_config(
    page_title="VoiceShield AI",
    page_icon="🛡️",
    layout="centered",
)

# Create the database table at application startup.
initialize_database()


st.title("🛡️ VoiceShield AI")
st.subheader("Voice Cloning Assessment & Scam Prevention")

st.write(
    "Upload a short WAV recording to inspect an AI model's "
    "prediction and learn how to verify suspicious voice requests."
)

st.warning(
    "This is an experimental prototype. Model predictions can be "
    "wrong and cannot prove whether a voice is genuine or fraudulent."
)


# AUDIO UPLOAD
st.header("1. Upload Audio")

uploaded_file = st.file_uploader(
    "Choose a WAV audio file",
    type=["wav"],
    help="Maximum file size: 10 MB. Maximum duration: 30 seconds.",
)

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/wav")


# AUDIO ANALYSIS
st.header("2. Analyze Audio")

if st.button("Analyze audio", type="primary"):

    if uploaded_file is None:
        st.error("Please upload a WAV file first.")

    else:
        try:
            with st.spinner("Analyzing audio. Please wait..."):
                result = analyze_audio(uploaded_file)

            # Select the highest-scoring class.
            top_result = max(
                result["predictions"],
                key=lambda item: item["score"],
            )

            # Store metadata only, not the audio recording.
            save_analysis(
                filename=os.path.basename(uploaded_file.name),
                prediction=top_result["label"],
                score=float(top_result["score"]),
                duration=float(result["duration"]),
            )

            st.success("Analysis completed!")

            st.metric(
                "Audio duration",
                f"{result['duration']:.1f} seconds",
            )

            st.caption(
                f"Sample rate: {result['sample_rate']} Hz | "
                f"Channels: {result['channels']}"
            )

            st.subheader("Model Predictions")

            for prediction in result["predictions"]:
                st.write(f"**Label:** {prediction['label']}")

                score = float(prediction["score"])
                st.progress(max(0.0, min(1.0, score)))
                st.write(f"Model score: {score:.2%}")
                st.divider()

            st.info(
                "A model score is not necessarily a calibrated "
                "probability that audio is fake. Check the model's "
                "label definitions and limitations before interpreting it."
            )

        except ValueError as error:
            st.error(str(error))

        except Exception:
            st.error(
                "Analysis failed. Check the terminal for technical "
                "details and try again with a valid WAV recording."
            )


# PREVENTION GUIDANCE
st.divider()
st.header("3. Prevent Voice Impersonation")

st.write(
    "Regardless of the model's output, independently verify "
    "sensitive requests before taking action."
)

for advice in get_prevention_advice():
    st.markdown(f"- {advice}")


# DATABASE HISTORY
st.divider()
st.header("4. Analysis History")

history = get_history(limit=50)

if history:
    st.dataframe(
        history,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info(
        "No analysis history yet. Upload a WAV file and run an analysis."
    )


# PRIVACY INFORMATION
st.divider()
st.caption(
    "Privacy: VoiceShield does not intentionally save audio recordings "
    "in its database. Temporary processing and hosting infrastructure "
    "may still handle uploaded audio. Do not upload confidential recordings."
)
