"""Tkinter desktop app for SoundSpace Orbit."""

from __future__ import annotations

import math
import threading
from pathlib import Path
from tkinter import (
    BooleanVar,
    Button,
    Canvas,
    Checkbutton,
    DoubleVar,
    Entry,
    Frame,
    Label,
    Scale,
    Spinbox,
    StringVar,
    Tk,
    filedialog,
    messagebox,
)

from .converter import OrbitSettings, convert_to_8d
from .version import __version__


BG = "#050812"
PANEL = "#0a1020"
PANEL_2 = "#0e182d"
FIELD = "#111b32"
TEXT = "#eef8ff"
MUTED = "#90a7bd"
SUBTLE = "#34445d"
CYAN = "#38f2da"
CYAN_DIM = "#133b45"
PINK = "#ff4fc4"
VIOLET = "#7c5cff"
BLUE = "#2fa8ff"
SUCCESS = "#7dfcc8"
ERROR = "#ff7d9b"


class SoundSpaceOrbitApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title(f"SoundSpace Orbit v{__version__}")
        self.root.geometry("900x620")
        self.root.minsize(760, 540)
        self.root.configure(bg=BG)

        self.source = StringVar()
        self.output_dir = StringVar(value=str((Path.cwd() / "output").resolve()))
        self.output_format = StringVar(value="mp3")
        self.cycle_seconds = DoubleVar(value=8.0)
        self.depth = DoubleVar(value=0.85)
        self.depth_label = StringVar(value="85%")
        self.spatial_reverb = BooleanVar(value=False)
        self.status = StringVar(value=f"SoundSpace Orbit v{__version__} ready.")

        self._format_buttons: dict[str, Button] = {}
        self._phase = 0.0
        self._working = False

        self._build_layout()
        self._animate_orbit()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        shell = Frame(self.root, bg=BG, padx=26, pady=24)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        self._build_header(shell)
        self._build_control_surface(shell)

    def _build_header(self, parent: Frame) -> None:
        header = Frame(parent, bg=BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        header.columnconfigure(0, weight=1)

        copy = Frame(header, bg=BG)
        copy.grid(row=0, column=0, sticky="w")

        name_row = Frame(copy, bg=BG)
        name_row.grid(row=0, column=0, sticky="w")

        Label(
            name_row,
            text="SoundSpace Orbit",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI Semibold", 30),
        ).grid(row=0, column=0, sticky="w")

        Label(
            name_row,
            text=f"v{__version__}",
            bg=CYAN_DIM,
            fg=CYAN,
            padx=12,
            pady=4,
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=1, sticky="w", padx=(14, 0), pady=(8, 0))

        Label(
            copy,
            text="8D stereo motion studio",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 12),
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.orbit_canvas = Canvas(
            header,
            width=230,
            height=132,
            bg=BG,
            bd=0,
            highlightthickness=0,
        )
        self.orbit_canvas.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_control_surface(self, parent: Frame) -> None:
        panel = Frame(
            parent,
            bg=PANEL,
            padx=22,
            pady=22,
            highlightbackground="#162740",
            highlightcolor="#162740",
            highlightthickness=1,
        )
        panel.grid(row=1, column=0, sticky="nsew")
        panel.columnconfigure(1, weight=1)

        self._add_entry_row(panel, 0, "Source", self.source, "Browse", self._choose_file)
        self._add_entry_row(panel, 1, "Destination", self.output_dir, "Choose", self._choose_output_dir)

        settings = Frame(panel, bg=PANEL)
        settings.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(22, 0))
        settings.columnconfigure(0, weight=1)
        settings.columnconfigure(1, weight=1)

        self._build_cycle_control(settings)
        self._build_format_switch(settings)
        self._build_depth_control(panel)

        Checkbutton(
            panel,
            text="Spatial ambience",
            variable=self.spatial_reverb,
            bg=PANEL,
            fg=TEXT,
            activebackground=PANEL,
            activeforeground=CYAN,
            selectcolor=FIELD,
            font=("Segoe UI", 11),
            bd=0,
            highlightthickness=0,
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(18, 0))

        self.convert_button = Button(
            panel,
            text="Create 8D Orbit Mix",
            command=self._start_conversion,
            bg=CYAN,
            fg="#031015",
            activebackground=SUCCESS,
            activeforeground="#031015",
            disabledforeground="#637789",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 13),
            pady=13,
        )
        self.convert_button.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(26, 0))

        status_bar = Frame(panel, bg=PANEL_2, padx=14, pady=12)
        status_bar.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        status_bar.columnconfigure(1, weight=1)

        self.status_light = Canvas(status_bar, width=15, height=15, bg=PANEL_2, bd=0, highlightthickness=0)
        self.status_light.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self._draw_status_light(CYAN)

        self.status_label = Label(
            status_bar,
            textvariable=self.status,
            bg=PANEL_2,
            fg=MUTED,
            anchor="w",
            justify="left",
            wraplength=760,
            font=("Segoe UI", 10),
        )
        self.status_label.grid(row=0, column=1, sticky="ew")

    def _add_entry_row(
        self,
        parent: Frame,
        row: int,
        label_text: str,
        variable: StringVar,
        button_text: str,
        command,
    ) -> None:
        Label(
            parent,
            text=label_text,
            bg=PANEL,
            fg=MUTED,
            font=("Segoe UI Semibold", 10),
        ).grid(row=row, column=0, sticky="w", pady=(0 if row == 0 else 14, 0))

        entry = Entry(
            parent,
            textvariable=variable,
            bg=FIELD,
            fg=TEXT,
            insertbackground=CYAN,
            relief="flat",
            bd=0,
            highlightbackground=SUBTLE,
            highlightcolor=CYAN,
            highlightthickness=1,
            font=("Segoe UI", 11),
        )
        entry.grid(row=row, column=1, sticky="ew", padx=(18, 10), ipady=10, pady=(0 if row == 0 else 14, 0))

        self._secondary_button(parent, button_text, command).grid(
            row=row,
            column=2,
            sticky="ew",
            ipady=8,
            pady=(0 if row == 0 else 14, 0),
        )

    def _build_cycle_control(self, parent: Frame) -> None:
        block = Frame(parent, bg=PANEL_2, padx=16, pady=14, highlightbackground="#182a45", highlightthickness=1)
        block.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        block.columnconfigure(1, weight=1)

        Label(block, text="Cycle", bg=PANEL_2, fg=MUTED, font=("Segoe UI Semibold", 10)).grid(
            row=0,
            column=0,
            sticky="w",
        )
        Label(block, text="seconds", bg=PANEL_2, fg=SUBTLE, font=("Segoe UI", 9)).grid(
            row=0,
            column=1,
            sticky="e",
        )

        Spinbox(
            block,
            from_=1.0,
            to=60.0,
            increment=0.5,
            textvariable=self.cycle_seconds,
            bg=FIELD,
            fg=TEXT,
            insertbackground=CYAN,
            buttonbackground=PANEL_2,
            relief="flat",
            bd=0,
            highlightbackground=SUBTLE,
            highlightcolor=CYAN,
            highlightthickness=1,
            width=10,
            font=("Segoe UI", 13),
        ).grid(row=1, column=0, columnspan=2, sticky="ew", ipady=7, pady=(10, 0))

    def _build_format_switch(self, parent: Frame) -> None:
        block = Frame(parent, bg=PANEL_2, padx=16, pady=14, highlightbackground="#182a45", highlightthickness=1)
        block.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        block.columnconfigure(0, weight=1)
        block.columnconfigure(1, weight=1)

        Label(block, text="Output", bg=PANEL_2, fg=MUTED, font=("Segoe UI Semibold", 10)).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
        )

        for index, fmt in enumerate(("mp3", "wav")):
            button = Button(
                block,
                text=fmt.upper(),
                command=lambda value=fmt: self._select_format(value),
                relief="flat",
                bd=0,
                cursor="hand2",
                font=("Segoe UI Semibold", 11),
                pady=8,
            )
            button.grid(row=1, column=index, sticky="ew", padx=(0 if index == 0 else 8, 0), pady=(10, 0))
            self._format_buttons[fmt] = button

        self._select_format(self.output_format.get())

    def _build_depth_control(self, parent: Frame) -> None:
        depth_panel = Frame(parent, bg=PANEL_2, padx=16, pady=14, highlightbackground="#182a45", highlightthickness=1)
        depth_panel.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(22, 0))
        depth_panel.columnconfigure(1, weight=1)

        Label(depth_panel, text="Pan depth", bg=PANEL_2, fg=MUTED, font=("Segoe UI Semibold", 10)).grid(
            row=0,
            column=0,
            sticky="w",
        )
        Label(depth_panel, textvariable=self.depth_label, bg=PANEL_2, fg=CYAN, font=("Segoe UI Semibold", 10)).grid(
            row=0,
            column=2,
            sticky="e",
        )

        Scale(
            depth_panel,
            from_=0.0,
            to=0.95,
            resolution=0.01,
            variable=self.depth,
            orient="horizontal",
            command=self._on_depth_change,
            bg=PANEL_2,
            fg=TEXT,
            activebackground=PINK,
            troughcolor=FIELD,
            highlightthickness=0,
            relief="flat",
            bd=0,
            showvalue=False,
        ).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(9, 0))

    def _secondary_button(self, parent: Frame, text: str, command) -> Button:
        return Button(
            parent,
            text=text,
            command=command,
            bg="#14223b",
            fg=TEXT,
            activebackground="#1c355a",
            activeforeground=CYAN,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 10),
            padx=14,
        )

    def _select_format(self, value: str) -> None:
        self.output_format.set(value)
        for fmt, button in self._format_buttons.items():
            selected = fmt == value
            button.configure(
                bg=CYAN if selected else FIELD,
                fg="#031015" if selected else MUTED,
                activebackground=SUCCESS if selected else "#1c355a",
                activeforeground="#031015" if selected else CYAN,
            )

    def _on_depth_change(self, value: str) -> None:
        self.depth_label.set(f"{float(value) * 100:.0f}%")

    def _draw_status_light(self, color: str) -> None:
        self.status_light.delete("all")
        self.status_light.create_oval(3, 3, 12, 12, fill=color, outline="")
        self.status_light.create_oval(1, 1, 14, 14, outline=color)

    def _animate_orbit(self) -> None:
        canvas = self.orbit_canvas
        canvas.delete("all")

        width = int(canvas["width"])
        height = int(canvas["height"])
        cx = width // 2
        cy = height // 2

        for step, color in enumerate(("#132339", "#1b3151", "#27416a")):
            pad_x = 16 + step * 20
            pad_y = 17 + step * 11
            canvas.create_oval(pad_x, pad_y, width - pad_x, height - pad_y, outline=color, width=1)

        for index in range(0, width, 18):
            alpha_color = "#0d1a2b" if index % 36 else "#12233a"
            canvas.create_line(index, 10, index - 52, height - 8, fill=alpha_color)

        wave_points: list[float] = []
        for x_pos in range(18, width - 16, 9):
            y_pos = height - 22 + math.sin((x_pos / 18) + self._phase * 2.1) * 7
            wave_points.extend([x_pos, y_pos])
        if len(wave_points) >= 4:
            canvas.create_line(*wave_points, fill=BLUE, width=2, smooth=True)

        rx = 82
        ry = 37
        left_x = cx - rx + 6
        right_x = cx + rx - 6
        canvas.create_line(left_x, cy, right_x, cy, fill="#1c3150", width=2)
        canvas.create_text(left_x - 12, cy, text="L", fill=MUTED, font=("Segoe UI Semibold", 9))
        canvas.create_text(right_x + 12, cy, text="R", fill=MUTED, font=("Segoe UI Semibold", 9))

        x_pos = cx + math.cos(self._phase) * rx
        y_pos = cy + math.sin(self._phase) * ry
        glow = PINK if self._working else CYAN
        canvas.create_oval(x_pos - 16, y_pos - 16, x_pos + 16, y_pos + 16, outline=glow, width=1)
        canvas.create_oval(x_pos - 8, y_pos - 8, x_pos + 8, y_pos + 8, fill=glow, outline="")
        canvas.create_text(cx, cy, text="8D", fill=TEXT, font=("Segoe UI Semibold", 22))

        self._phase = (self._phase + (0.14 if self._working else 0.055)) % (math.pi * 2)
        self.root.after(45, self._animate_orbit)

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
        self._set_working(True)
        self.status.set("Working... decoding source and creating orbit mix.")
        self.status_label.configure(fg=CYAN)
        self._draw_status_light(PINK)

        worker = threading.Thread(target=self._convert, daemon=True)
        worker.start()

    def _set_working(self, working: bool) -> None:
        self._working = working
        self.convert_button.configure(
            state="disabled" if working else "normal",
            text="Orbiting..." if working else "Create 8D Orbit Mix",
            bg="#27334a" if working else CYAN,
            fg="#7f92a8" if working else "#031015",
        )

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
        self._set_working(False)
        self.status.set(f"Created: {output_path}")
        self.status_label.configure(fg=SUCCESS)
        self._draw_status_light(SUCCESS)
        messagebox.showinfo("SoundSpace Orbit", f"Created:\n{output_path}")

    def _conversion_failed(self, exc: Exception) -> None:
        self._set_working(False)
        self.status.set(f"Failed: {exc}")
        self.status_label.configure(fg=ERROR)
        self._draw_status_light(ERROR)
        messagebox.showerror("SoundSpace Orbit", str(exc))


def run_app() -> None:
    root = Tk()
    app = SoundSpaceOrbitApp(root)
    app.root.mainloop()
