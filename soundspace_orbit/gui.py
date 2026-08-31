"""Tkinter desktop app for SoundSpace Orbit."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import BooleanVar, DoubleVar, StringVar, Tk, filedialog, messagebox, ttk

from .converter import OrbitSettings, convert_to_8d
from .version import __version__


class SoundSpaceOrbitApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title(f"SoundSpace Orbit v{__version__}")
        self.root.geometry("720x430")
        self.root.minsize(640, 390)

        self.source = StringVar()
        self.output_dir = StringVar(value=str((Path.cwd() / "output").resolve()))
        self.output_format = StringVar(value="mp3")
        self.cycle_seconds = DoubleVar(value=8.0)
        self.depth = DoubleVar(value=0.85)
        self.spatial_reverb = BooleanVar(value=False)
        self.status = StringVar(value=f"SoundSpace Orbit v{__version__} ready.")

        self._build_layout()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frame = ttk.Frame(self.root, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        title = ttk.Label(frame, text=f"SoundSpace Orbit v{__version__}", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(frame, text="Audio file or URL").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.source).grid(row=1, column=1, sticky="ew", padx=(10, 8))
        ttk.Button(frame, text="Browse", command=self._choose_file).grid(row=1, column=2, sticky="ew")

        ttk.Label(frame, text="Output folder").grid(row=2, column=0, sticky="w", pady=(10, 0))
        ttk.Entry(frame, textvariable=self.output_dir).grid(row=2, column=1, sticky="ew", padx=(10, 8), pady=(10, 0))
        ttk.Button(frame, text="Choose", command=self._choose_output_dir).grid(row=2, column=2, sticky="ew", pady=(10, 0))

        controls = ttk.Frame(frame)
        controls.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=1)

        ttk.Label(controls, text="Cycle seconds").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(
            controls,
            from_=1.0,
            to=60.0,
            increment=0.5,
            textvariable=self.cycle_seconds,
            width=10,
        ).grid(row=0, column=1, sticky="w", padx=(10, 28))

        ttk.Label(controls, text="Output").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            controls,
            textvariable=self.output_format,
            values=("mp3", "wav"),
            width=8,
            state="readonly",
        ).grid(row=0, column=3, sticky="w", padx=(10, 0))

        ttk.Label(controls, text="Pan depth").grid(row=1, column=0, sticky="w", pady=(18, 0))
        ttk.Scale(
            controls,
            from_=0.0,
            to=0.95,
            variable=self.depth,
            orient="horizontal",
        ).grid(row=1, column=1, columnspan=3, sticky="ew", padx=(10, 0), pady=(18, 0))

        ttk.Checkbutton(
            frame,
            text="Add light spatial ambience",
            variable=self.spatial_reverb,
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(18, 0))

        self.convert_button = ttk.Button(frame, text="Create 8D Audio", command=self._start_conversion)
        self.convert_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(24, 0))

        status_label = ttk.Label(frame, textvariable=self.status, wraplength=660, foreground="#29527a")
        status_label.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(18, 0))

    def _choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose audio file",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.opus"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.source.set(path)

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_dir.set(path)

    def _start_conversion(self) -> None:
        self.convert_button.configure(state="disabled")
        self.status.set("Working... decoding, orbiting, and exporting audio.")

        worker = threading.Thread(target=self._convert, daemon=True)
        worker.start()

    def _convert(self) -> None:
        try:
            settings = OrbitSettings(
                cycle_seconds=float(self.cycle_seconds.get()),
                depth=float(self.depth.get()),
                output_format=self.output_format.get(),
                spatial_reverb=self.spatial_reverb.get(),
            )
            result = convert_to_8d(self.source.get(), self.output_dir.get(), settings)
        except Exception as exc:
            self.root.after(0, self._conversion_failed, exc)
            return

        self.root.after(0, self._conversion_finished, result.output_path)

    def _conversion_finished(self, output_path: Path) -> None:
        self.convert_button.configure(state="normal")
        self.status.set(f"Created: {output_path}")
        messagebox.showinfo("SoundSpace Orbit", f"Created:\n{output_path}")

    def _conversion_failed(self, exc: Exception) -> None:
        self.convert_button.configure(state="normal")
        self.status.set(f"Failed: {exc}")
        messagebox.showerror("SoundSpace Orbit", str(exc))


def run_app() -> None:
    root = Tk()
    app = SoundSpaceOrbitApp(root)
    app.root.mainloop()
