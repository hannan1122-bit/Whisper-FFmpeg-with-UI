import subprocess
import whisper
import os

# ---- CONFIG ----
input_video = "input.mp4"        # Your test video file
output_srt = "captions.srt"
output_video = "output_vertical.mp4"
whisper_model_size = "small"     # Options: tiny, base, small, medium, large

# ---- STEP 1: Extract audio ----
print("Extracting audio...")
audio_file = "audio.wav"
subprocess.run([
    "ffmpeg", "-y", "-i", input_video, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", audio_file
])

# ---- STEP 2: Transcribe audio with Whisper ----
print("Transcribing with Whisper...")
model = whisper.load_model(whisper_model_size)
result = model.transcribe(audio_file)

# ---- STEP 3: Save captions as SRT ----
print("Saving captions to SRT...")
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

# ---- STEP 4: Burn captions into vertical 1080×1920 video + normalize audio ----
print("Processing video with FFmpeg...")
subprocess.run([
    "ffmpeg", "-y", "-i", input_video,
    "-vf", f"scale=1080:1920,subtitles={output_srt}:force_style='Fontsize=24',fps=30",
    "-af", "loudnorm",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-c:a", "aac", "-movflags", "+faststart",
    "-avoid_negative_ts", "make_zero",
    output_video
])

# ---- Cleanup temp audio ----
os.remove(audio_file)

print(f"Done! Processed video saved as {output_video}")
