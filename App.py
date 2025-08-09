import subprocess
import whisper
import os
import streamlit as st
from pathlib import Path

# ---- Streamlit UI ----
st.set_page_config(page_title="Video Captioning App", page_icon="🎬", layout="centered")
st.title("🎬 Video Captioning + Vertical Format Processor")
st.write("Upload a video, generate captions with Whisper, and get a vertical 1080×1920 export with burned captions.")

# File uploader
uploaded_file = st.file_uploader("📂 Upload a video file", type=["mp4", "mov", "mkv", "avi"])
model_size = st.selectbox("Whisper Model Size", ["tiny", "base", "small", "medium"], index=2)

if uploaded_file:
    # Save uploaded file
    input_path = Path("input_video.mp4")
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    output_srt = "captions.srt"
    output_video = "output_vertical.mp4"
    audio_file = "audio.wav"

    if st.button("🚀 Process Video"):
        st.info("Extracting audio...")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(input_path), "-vn", "-acodec", "pcm_s16le", "-ar", "16000", audio_file
        ])

        st.info("Transcribing with Whisper...")
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_file)

        st.info("Saving captions...")
        def to_srt(transcription, file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                for i, segment in enumerate(transcription["segments"], start=1):
                    start = segment["start"]
                    end = segment["end"]

                    def srt_time(t):
                        hours = int(t // 3600)
                        minutes = int((t % 3600) // 60)
                        seconds = int(t % 60)
                        millis = int((t * 1000) % 1000)
                        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

                    f.write(f"{i}\n")
                    f.write(f"{srt_time(start)} --> {srt_time(end)}\n")
                    f.write(segment["text"].strip() + "\n\n")

        to_srt(result, output_srt)

        st.info("Processing video with FFmpeg...")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(input_path),
            "-vf", f"scale=1080:1920,subtitles={output_srt}:force_style='Fontsize=24',fps=30",
            "-af", "loudnorm",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-movflags", "+faststart",
            "-avoid_negative_ts", "make_zero",
            output_video
        ])

        # Remove temp files
        os.remove(audio_file)

        st.success("✅ Done! Your processed video is ready.")
        with open(output_video, "rb") as f:
            st.download_button("⬇️ Download Processed Video", f, file_name=output_video)
