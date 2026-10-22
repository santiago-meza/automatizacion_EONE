import json
import os
import queue
import sys
import threading
import traceback
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from config import BASE_DIR, INPUT, OUTPUT
from main import main as run_pipeline


SETTINGS_FILE = BASE_DIR / "eone_settings.json"

# Paleta violeta
BG = "#1A1325"
CARD = "#251A38"
FIELD = "#30234A"
BORDER = "#4C3775"
ACCENT = "#8B5CF6"
ACCENT_HOVER = "#7C3AED"
TEXT = "#F3EEFF"
MUTED = "#B9A6E8"
SUCCESS = "#A3E635"
ERROR = "#F87171"


class QueueWriter:
    """Redirige print() hacia la cola que lee la GUI."""

    def __init__(self, q):
        self.q = q

    def write(self, text):
        if text:
            self.q.put(("log", text))

    def flush(self):
        pass


def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(data):
    try:
        SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")

        self.title("EONE · Generador de informes")
        self.geometry("760x600")
        self.minsize(640, 520)
        self.configure(fg_color=BG)

        self.queue = queue.Queue()
        self.total = 0
        self.done = 0

        settings = load_settings()
        self.input_var = ctk.StringVar(value=settings.get("input", str(INPUT)))
        self.output_var = ctk.StringVar(value=settings.get("output", str(OUTPUT)))

        self._build()
        self.after(100, self._poll_queue)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Encabezado
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 12))

        ctk.CTkLabel(
            header, text="EONE", text_color=ACCENT,
            font=ctk.CTkFont(size=30, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Generador de informes de microarray",
            text_color=MUTED, font=ctk.CTkFont(size=14),
        ).pack(anchor="w")

        # Tarjeta de carpetas
        card = ctk.CTkFrame(
            self, fg_color=CARD, corner_radius=14,
            border_width=1, border_color=BORDER,
        )
        card.grid(row=1, column=0, sticky="ew", padx=28, pady=8)
        card.grid_columnconfigure(1, weight=1)

        self._folder_row(card, 0, "Carpeta de entrada (PDFs)", self.input_var)
        self._folder_row(card, 1, "Carpeta de salida (informes)", self.output_var)

        # Botón principal + progreso
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=28, pady=(14, 8))
        actions.grid_columnconfigure(0, weight=1)

        self.run_btn = ctk.CTkButton(
            actions, text="Generar informes", height=46, corner_radius=12,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="white",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._start,
        )
        self.run_btn.grid(row=0, column=0, sticky="ew")

        self.open_btn = ctk.CTkButton(
            actions, text="Abrir salida", height=46, width=130, corner_radius=12,
            fg_color=FIELD, hover_color=BORDER, text_color=TEXT,
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=14),
            command=self._open_output,
        )
        self.open_btn.grid(row=0, column=1, padx=(10, 0))

        self.progress = ctk.CTkProgressBar(
            actions, height=8, corner_radius=4,
            fg_color=FIELD, progress_color=ACCENT,
        )
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        self.progress.set(0)

        self.status = ctk.CTkLabel(
            actions, text="Listo.", text_color=MUTED,
            font=ctk.CTkFont(size=13), anchor="w",
        )
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew")

        # Registro
        self.log = ctk.CTkTextbox(
            self, fg_color=CARD, text_color=TEXT, corner_radius=14,
            border_width=1, border_color=BORDER,
            font=ctk.CTkFont(family="Consolas", size=12),
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT,
        )
        self.log.grid(row=3, column=0, sticky="nsew", padx=28, pady=(8, 24))
        self.log.configure(state="disabled")

    def _folder_row(self, parent, row, label, var):
        pady = (18, 6) if row == 0 else (6, 18)

        ctk.CTkLabel(
            parent, text=label, text_color=TEXT,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=row, column=0, sticky="w", padx=(18, 12), pady=pady)

        ctk.CTkEntry(
            parent, textvariable=var, height=36, corner_radius=8,
            fg_color=FIELD, border_color=BORDER, text_color=TEXT,
        ).grid(row=row, column=1, sticky="ew", pady=pady)

        ctk.CTkButton(
            parent, text="Examinar…", width=110, height=36, corner_radius=8,
            fg_color=FIELD, hover_color=BORDER, text_color=TEXT,
            border_width=1, border_color=ACCENT,
            command=lambda: self._browse(var),
        ).grid(row=row, column=2, padx=(10, 18), pady=pady)

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _browse(self, var):
        initial = var.get() if Path(var.get()).is_dir() else str(BASE_DIR)
        folder = filedialog.askdirectory(initialdir=initial, parent=self)
        if folder:
            var.set(folder)

    def _open_output(self):
        folder = Path(self.output_var.get())
        if folder.is_dir():
            os.startfile(folder)
        else:
            self._set_status("La carpeta de salida todavía no existe.", ERROR)

    def _start(self):
        input_dir = Path(self.input_var.get().strip())
        output_dir = Path(self.output_var.get().strip())

        if not input_dir.is_dir():
            self._set_status("Seleccione una carpeta de entrada válida.", ERROR)
            return

        self.total = len(list(input_dir.glob("*.pdf")))
        if self.total == 0:
            self._set_status("No se encontraron PDFs en la carpeta de entrada.", ERROR)
            return

        save_settings({"input": str(input_dir), "output": str(output_dir)})

        self.done = 0
        self.progress.set(0)
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.run_btn.configure(state="disabled", text="Procesando…")
        self._set_status(f"Procesando 0 de {self.total} PDF(s)…", MUTED)

        threading.Thread(
            target=self._worker, args=(input_dir, output_dir), daemon=True
        ).start()

    def _worker(self, input_dir, output_dir):
        old_stdout = sys.stdout
        sys.stdout = QueueWriter(self.queue)
        try:
            run_pipeline(input_dir, output_dir)
            self.queue.put(("done", None))
        except Exception:
            self.queue.put(("log", traceback.format_exc()))
            self.queue.put(("error", None))
        finally:
            sys.stdout = old_stdout

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self.queue.get_nowait()

                if kind == "log":
                    self._append_log(payload)
                    if "Generado:" in payload:
                        self.done += 1
                        self.progress.set(self.done / self.total)
                        self._set_status(
                            f"Procesando {self.done} de {self.total} PDF(s)…", MUTED
                        )

                elif kind == "done":
                    self.progress.set(1)
                    self._set_status(
                        f"✔ {self.done} informe(s) generado(s) correctamente.", SUCCESS
                    )
                    self.run_btn.configure(state="normal", text="Generar informes")

                elif kind == "error":
                    self._set_status(
                        "✖ Ocurrió un error. Revise el registro.", ERROR
                    )
                    self.run_btn.configure(state="normal", text="Generar informes")
        except queue.Empty:
            pass

        self.after(100, self._poll_queue)

    def _append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_status(self, text, color):
        self.status.configure(text=text, text_color=color)


if __name__ == "__main__":
    App().mainloop()
