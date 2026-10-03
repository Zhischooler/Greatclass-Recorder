import os
import shutil
import subprocess


def find_ffmpeg():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base, "bin", "ffmpeg.exe"),
        os.path.join(base, "bin", "ffmpeg"),
        "ffmpeg",
        "ffmpeg.exe",
    ]
    for path in candidates:
        try:
            subprocess.run([path, "-version"], capture_output=True, check=True, timeout=5)
            return path
        except Exception:
            continue
    return None


def export_video(input_path, output_path, ffmpeg_path=None):
    if ffmpeg_path:
        cmd = [
            ffmpeg_path, "-y", "-i", input_path,
            "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    else:
        shutil.copy2(input_path, output_path)
    return output_path