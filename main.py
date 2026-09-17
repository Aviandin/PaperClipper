import os
import sys
import json
import threading
import tkinter as tk
from tkinter import messagebox

from recorder import Recorder
from overlay import show_clipped
from hotkeys import Hotkeys
from tray import Tray


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "primary_clip_seconds": 30,
    "secondary_clip_seconds": 60,
    "primary_hotkey": "f8",
    "secondary_hotkey": "f9",
    "clips_folder": "clips"
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            settings = json.load(file)

        for key, value in DEFAULT_SETTINGS.items():
            settings.setdefault(key, value)

        return settings

    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)


def main():
    settings = load_settings()

    ffmpeg = os.path.join(
        BASE_DIR,
        "ffmpeg",
        "ffmpeg.exe"
    )

    ffprobe = os.path.join(
        BASE_DIR,
        "ffmpeg",
        "ffprobe.exe"
    )

    if not os.path.isfile(ffmpeg):
        root = tk.Tk()
        root.withdraw()

        messagebox.showerror(
            "PaperClipper",
            "FFmpeg was not found.\n\n"
            "Put ffmpeg.exe inside the ffmpeg folder."
        )

        root.destroy()
        return

    if not os.path.isfile(ffprobe):
        root = tk.Tk()
        root.withdraw()

        messagebox.showerror(
            "PaperClipper",
            "FFprobe was not found.\n\n"
            "Put ffprobe.exe inside the ffmpeg folder."
        )

        root.destroy()
        return

    recorder = Recorder()

    print("Starting PaperClipper...")
    print("Starting rolling recording buffer...")

    recorder.start()

    def primary_clip():
        seconds = int(
            settings["primary_clip_seconds"]
        )

        print(
            f"Saving primary clip ({seconds} seconds)..."
        )

        result = recorder.clip(seconds)

        if result:
            print(f"Saved: {result}")
            show_clipped("Primary")
        else:
            print("Failed to create clip.")

    def secondary_clip():
        seconds = int(
            settings["secondary_clip_seconds"]
        )

        print(
            f"Saving secondary clip ({seconds} seconds)..."
        )

        result = recorder.clip(seconds)

        if result:
            print(f"Saved: {result}")
            show_clipped("Secondary")
        else:
            print("Failed to create clip.")

    hotkeys = Hotkeys(
        primary_clip,
        secondary_clip
    )

    hotkeys.start()

    print("")
    print("==============================")
    print("       PAPERCLIPPER")
    print("==============================")
    print("")
    print("F8 = Primary clip")
    print("F9 = Secondary clip")
    print("")
    print("PaperClipper is running.")
    print("")

    try:
        while True:
            threading.Event().wait(1)

    except KeyboardInterrupt:
        print("Stopping PaperClipper...")

    finally:
        hotkeys.stop()
        recorder.stop()


if __name__ == "__main__":
    main()