import os
import sys
import time
import subprocess

from PySide6.QtCore import QObject, Signal, QTimer, QStandardPaths


class RecorderEngine(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._output_path = None
        self._recording = False
        self._ffmpeg = None

    @property
    def recording(self):
        return self._recording

    @property
    def output_path(self):
        return self._output_path

    def set_ffmpeg(self, ffmpeg_path):
        self._ffmpeg = ffmpeg_path

    def _find_windows_audio(self):
        try:
            result = subprocess.run(
                [self._ffmpeg, "-list_devices", "true",
                 "-f", "dshow", "-i", "dummy"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stderr.splitlines():
                if "(audio)" in line and '"' in line:
                    return line.split('"')[1]
        except Exception:
            pass
        return None

    def _build_command(self, output_path):
        plat = sys.platform
        video_out = [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
        ]
        audio_out = ["-c:a", "aac", "-b:a", "160k"]

        if plat == "win32":
            cmd = [
                self._ffmpeg, "-y",
                "-f", "gdigrab",
                "-framerate", "30",
                "-draw_mouse", "1",
                "-i", "desktop",
            ]
            audio_dev = self._find_windows_audio()
            if audio_dev:
                cmd += ["-f", "dshow", "-i", f"audio={audio_dev}"]
                cmd += video_out + audio_out
            else:
                cmd += video_out
            cmd.append(output_path)
            return cmd

        if plat == "darwin":
            cmd = [
                self._ffmpeg, "-y",
                "-f", "avfoundation",
                "-framerate", "30",
                "-capture_cursor", "1",
                "-i", "1:0",
            ]
            cmd += video_out + audio_out + [output_path]
            return cmd

        display = os.environ.get("DISPLAY", ":0.0")
        cmd = [
            self._ffmpeg, "-y",
            "-f", "x11grab",
            "-framerate", "30",
            "-draw_mouse", "1",
            "-i", display,
        ]
        try:
            subprocess.run(
                [self._ffmpeg, "-f", "pulse", "-i", "default",
                 "-t", "0.1", "-f", "null", "-"],
                capture_output=True, timeout=5,
            )
            cmd += ["-f", "pulse", "-i", "default"]
            cmd += video_out + audio_out
        except Exception:
            cmd += video_out
        cmd.append(output_path)
        return cmd

    def start(self, output_path=None):
        if self._recording:
            return False
        if not self._ffmpeg:
            self.failed.emit("未找到 ffmpeg")
            return False
        if output_path is None:
            temp_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
            output_path = os.path.join(
                temp_dir, f"greatclass_rec_{int(time.time())}.mp4"
            )

        self._output_path = output_path
        cmd = self._build_command(output_path)

        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
        except Exception as e:
            self.failed.emit(f"启动 ffmpeg 失败: {e}")
            return False

        self._recording = True
        return True

    def stop(self):
        if not self._recording or not self._process:
            return
        try:
            self._process.stdin.write(b"q")
            self._process.stdin.flush()
            self._process.stdin.close()
        except Exception:
            pass
        QTimer.singleShot(1500, self._finalize)

    def _finalize(self):
        proc = self._process
        self._process = None
        self._recording = False
        if proc is None:
            return
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

        if self._output_path and os.path.exists(self._output_path) \
                and os.path.getsize(self._output_path) > 0:
            self.finished.emit(self._output_path)
        else:
            self.failed.emit("录制失败：未生成视频文件")