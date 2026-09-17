import keyboard


class Hotkeys:
    def __init__(self, primary_callback, secondary_callback):
        self.primary_callback = primary_callback
        self.secondary_callback = secondary_callback

    def start(self):
        keyboard.add_hotkey(
            "f8",
            self.primary_callback
        )

        keyboard.add_hotkey(
            "f9",
            self.secondary_callback
        )

    def stop(self):
        keyboard.unhook_all()