import os
import tkinter as tk
from PIL import Image, ImageTk


def show_clipped(clip_type="Primary"):
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.0)
    root.configure(bg="#171717")

    # Load icon.png
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")

    try:
        image = Image.open(icon_path).convert("RGBA")
        image.thumbnail((32, 32), Image.Resampling.LANCZOS)
        icon = ImageTk.PhotoImage(image)
    except Exception:
        icon = None

    frame = tk.Frame(
        root,
        bg="#171717",
        padx=12,
        pady=8
    )
    frame.pack()

    if icon:
        icon_label = tk.Label(
            frame,
            image=icon,
            bg="#171717"
        )
        icon_label.pack(side="left", padx=(0, 9))

    text = tk.Label(
        frame,
        text=f"{clip_type} Clip!",
        font=("Segoe UI", 12, "bold"),
        fg="white",
        bg="#171717"
    )
    text.pack(side="left")

    root.update_idletasks()

    # Position in the top-left
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()

    x = 20
    y = 20

    root.geometry(f"{width}x{height}+{x}+{y}")

    # Fade in
    def fade_in(alpha=0.0):
        if alpha < 1.0:
            alpha += 0.08
            root.attributes("-alpha", alpha)
            root.after(15, fade_in, alpha)
        else:
            # Stay fully visible for about one second
            root.after(1000, fade_out)

    # Fade out
    def fade_out(alpha=1.0):
        if alpha > 0.0:
            alpha -= 0.08
            root.attributes("-alpha", alpha)
            root.after(15, fade_out, alpha)
        else:
            root.destroy()

    fade_in()
    root.mainloop()