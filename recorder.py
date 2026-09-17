import os
import subprocess
import threading
import time
from datetime import datetime


class Recorder:
    def __init__(self):
        self.base_folder = os.path.dirname(os.path.abspath(__file__))

        self.ffmpeg_path = os.path.join(
            self.base_folder,
            "ffmpeg",
            "ffmpeg.exe"
        )

        self.clips_folder = os.path.join(
            self.base_folder,
            "clips"
        )

        self.temp_folder = os.path.join(
            self.base_folder,
            "temp"
        )

        os.makedirs(self.clips_folder, exist_ok=True)
        os.makedirs(self.temp_folder, exist_ok=True)

        self.process = None
        self.lock = threading.Lock()

        self.segment_seconds = 1
        self.max_segments = 320

    def start(self):
        if self.process and self.process.poll() is None:
            return

        for filename in os.listdir(self.temp_folder):
            if filename.startswith("buffer_") and filename.endswith(".ts"):
                try:
                    os.remove(os.path.join(self.temp_folder, filename))
                except Exception:
                    pass

        output_pattern = os.path.join(
            self.temp_folder,
            "buffer_%03d.ts"
        )

        command = [
            self.ffmpeg_path,

            "-hide_banner",
            "-loglevel", "warning",

            "-f", "gdigrab",
            "-framerate", "30",
            "-draw_mouse", "1",
            "-i", "desktop",

            "-an",

            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",

            "-g", "30",
            "-keyint_min", "30",
            "-sc_threshold", "0",

            "-f", "segment",
            "-segment_time", "1",
            "-segment_wrap", str(self.max_segments),
            "-reset_timestamps", "1",
            "-segment_format", "mpegts",

            output_pattern
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            threading.Thread(
                target=self._read_errors,
                daemon=True
            ).start()

            threading.Thread(
                target=self._watch_process,
                daemon=True
            ).start()

            print("Recording started.")

        except Exception as e:
            print(f"Failed to start FFmpeg: {e}")
            self.process = None

    def _read_errors(self):
        if not self.process or not self.process.stderr:
            return

        try:
            for line in self.process.stderr:
                line = line.decode(errors="ignore").strip()

                if line:
                    print("FFmpeg:", line)

        except Exception:
            pass

    def _watch_process(self):
        process = self.process

        if process:
            process.wait()

            if self.process == process:
                self.process = None

    def stop(self):
        if not self.process:
            return

        try:
            self.process.terminate()
            self.process.wait(timeout=3)
        except Exception:
            try:
                self.process.kill()
            except Exception:
                pass

        self.process = None

    def _get_complete_segments(self):
        segments = []

        try:
            for filename in os.listdir(self.temp_folder):

                if not (
                    filename.startswith("buffer_")
                    and filename.endswith(".ts")
                ):
                    continue

                path = os.path.join(
                    self.temp_folder,
                    filename
                )

                try:
                    size = os.path.getsize(path)
                    modified = os.path.getmtime(path)

                    if size < 1024:
                        continue

                    segments.append(
                        (modified, path)
                    )

                except OSError:
                    continue

        except Exception:
            return []

        segments.sort(key=lambda x: x[0])

        # The newest file is probably still being written.
        if len(segments) > 1:
            segments = segments[:-1]

        return [
            path
            for _, path in segments
        ]

    def clip(self, seconds):

        with self.lock:

            if not self.process or self.process.poll() is not None:
                print("Recorder is not running.")
                return None

            seconds = int(seconds)

            print(
                f"Preparing {seconds}-second clip..."
            )

            # Give FFmpeg time to finish the current segment.
            time.sleep(0.25)

            segments = self._get_complete_segments()

            if not segments:
                print("No completed recording segments yet.")
                return None

            wanted = min(
                seconds,
                len(segments)
            )

            selected = segments[-wanted:]

            if not selected:
                print("Not enough recording data.")
                return None

            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            output = os.path.join(
                self.clips_folder,
                f"PaperClip_{timestamp}_{seconds}s.mp4"
            )

            concat_file = os.path.join(
                self.temp_folder,
                "clip_list.txt"
            )

            try:

                with open(
                    concat_file,
                    "w",
                    encoding="utf-8"
                ) as f:

                    for path in selected:

                        safe_path = os.path.abspath(
                            path
                        ).replace("\\", "/")

                        f.write(
                            "file '" +
                            safe_path.replace(
                                "'",
                                "'\\''"
                            ) +
                            "'\n"
                        )

                command = [
                    self.ffmpeg_path,

                    "-hide_banner",
                    "-loglevel", "error",

                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file,

                    "-t", str(seconds),

                    "-c:v", "copy",

                    "-avoid_negative_ts",
                    "make_zero",

                    "-movflags",
                    "+faststart",

                    "-y",
                    output
                ]

                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if result.returncode != 0:

                    error = result.stderr.decode(
                        errors="ignore"
                    ).strip()

                    print(
                        "Clip creation failed:"
                    )
                    print(error)

                    if os.path.exists(output):
                        try:
                            os.remove(output)
                        except Exception:
                            pass

                    return None

                if not os.path.exists(output):
                    print(
                        "FFmpeg finished but no clip was created."
                    )
                    return None

                if os.path.getsize(output) < 1024:
                    print(
                        "Created clip was too small."
                    )
                    return None

                print(
                    f"Saved: {output}"
                )

                return output

            except Exception as e:

                print(
                    f"Clip error: {e}"
                )

                return None

            finally:

                try:
                    if os.path.exists(concat_file):
                        os.remove(concat_file)
                except Exception:
                    pass