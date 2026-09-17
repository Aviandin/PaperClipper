import os
import threading
import subprocess

import pystray
from PIL import Image


class Tray:
    def __init__(self, recorder, settings, save_settings,
                 primary_clip_callback, secondary_clip_callback):

        self.recorder = recorder
        self.settings = settings
        self.save_settings = save_settings

        self.primary_clip_callback = primary_clip_callback
        self.secondary_clip_callback = secondary_clip_callback

        self.base_folder = os.path.dirname(
            os.path.abspath(__file__)
        )

        self.icon_path = os.path.join(
            self.base_folder,
            "icon.png"
        )

        self.icon = None

    def start(self):
        try:
            image = Image.open(self.icon_path).convert("RGBA")

        except Exception:
            # Fallback icon if icon.png can't be loaded
            image = Image.new(
                "RGBA",
                (64, 64),
                (40, 40, 40, 255)
            )

        self.icon = pystray.Icon(
            "PaperClipper",
            image,
            "PaperClipper",
            self._create_menu()
        )

        self.icon.run()

    def _create_menu(self):

        primary_menu = pystray.Menu(
            *[
                pystray.MenuItem(
                    f"{seconds} seconds",
                    self._set_primary(seconds),
                    checked=lambda item, s=seconds:
                        self.settings["primary_clip_seconds"] == s,
                    radio=True
                )
                for seconds in [30, 60, 120, 180, 300]
            ]
        )

        secondary_menu = pystray.Menu(
            *[
                pystray.MenuItem(
                    f"{seconds} seconds",
                    self._set_secondary(seconds),
                    checked=lambda item, s=seconds:
                        self.settings["secondary_clip_seconds"] == s,
                    radio=True
                )
                for seconds in [30, 60, 120, 180, 300]
            ]
        )

        return pystray.Menu(

            pystray.MenuItem(
                "Clip Primary (F8)",
                self._primary
            ),

            pystray.MenuItem(
                "Clip Secondary (F9)",
                self._secondary
            ),

            pystray.Menu.SEPARATOR,

            pystray.MenuItem(
                "Primary Clip Length",
                primary_menu
            ),

            pystray.MenuItem(
                "Secondary Clip Length",
                secondary_menu
            ),

            pystray.Menu.SEPARATOR,

            pystray.MenuItem(
                "Open Clips Folder",
                self._open_clips
            ),

            pystray.MenuItem(
                "Exit PaperClipper",
                self._exit
            )
        )

    def _set_primary(self, seconds):
        def callback(icon, item):
            self.settings["primary_clip_seconds"] = seconds
            self.save_settings()

        return callback

    def _set_secondary(self, seconds):
        def callback(icon, item):
            self.settings["secondary_clip_seconds"] = seconds
            self.save_settings()

        return callback

    def _primary(self, icon, item):
        threading.Thread(
            target=self.primary_clip_callback,
            daemon=True
        ).start()

    def _secondary(self, icon, item):
        threading.Thread(
            target=self.secondary_clip_callback,
            daemon=True
        ).start()

    def _open_clips(self, icon, item):

        clips_folder = os.path.join(
            self.base_folder,
            "clips"
        )

        os.makedirs(
            clips_folder,
            exist_ok=True
        )

        os.startfile(clips_folder)

    def _exit(self, icon, item):

        try:
            self.recorder.stop()
        except Exception:
            pass

        try:
            self.icon.stop()
        except Exception:
            pass