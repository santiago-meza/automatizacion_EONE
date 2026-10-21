"""
Interfaz gráfica para generar los informes en español (Word y PDF).

Uso:
    python gui.py
"""

import json
import os
import queue
import threading
import tkinter as tk

from pathlib import Path

import customtkinter as ctk

from config import INPUT, OUTPUT
from genda_ui import (
    COLORS,
    FolderPicker,
    GendaApp,
    StatusLog,
    card,
    font,
    primary_button,
    secondary_button,
    section_label
)
from pipeline import process_folder


# ============================================================
# Settings
# ============================================================

def get_settings_file():

    app_data = os.getenv("LOCALAPPDATA")

    if app_data:

        settings_dir = (
            Path(app_data) /
            "EONE"
        )

    else:

        settings_dir = (
            Path.home() /
            ".eone"
        )

    settings_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return settings_dir / "settings.json"


SETTINGS_FILE = get_settings_file()


def load_settings():

    if not SETTINGS_FILE.exists():
        return {}

    try:

        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return {}


def save_settings(
    input_folder,
    output_folder
):

    settings = {
        "input_folder": input_folder,
        "output_folder": output_folder
    }

    try:

        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                settings,
                file,
                indent=4
            )

    except OSError:

        pass


def log_kind(line):
    """
    Color de cada línea del registro según su contenido.
    """

    if "[ERROR]" in line or line.startswith("NO SE PUDO"):
        return "error"

    if "[AVISO]" in line or line.startswith("REVISAR"):
        return "warning"

    if "[INFO]" in line:
        return "info"

    if line.startswith("="):
        return "muted"

    return None


# ============================================================
# Application
# ============================================================

class ReportApp(GendaApp):

    def __init__(self):

        super().__init__(
            "EONE",
            subtitle="Generación de informes de microarray",
            size=(820, 780),
            resizable=True,
            app_id="GENDA.EONE"
        )

        self.messages = queue.Queue()

        self.input_folder = tk.StringVar(value=str(INPUT))
        self.output_folder = tk.StringVar(value=str(OUTPUT))

        self.load_saved_folders()

        self.create_widgets()

        self.after(
            100,
            self.poll_messages
        )

    # ========================================================
    # Settings
    # ========================================================

    def load_saved_folders(self):

        settings = load_settings()

        input_folder = settings.get(
            "input_folder",
            ""
        )

        output_folder = settings.get(
            "output_folder",
            ""
        )

        if (
            input_folder and
            Path(input_folder).is_dir()
        ):

            self.input_folder.set(
                input_folder
            )

        if (
            output_folder and
            Path(output_folder).is_dir()
        ):

            self.output_folder.set(
                output_folder
            )

    def save_folders(self):

        save_settings(
            self.input_folder.get(),
            self.output_folder.get()
        )

    # ========================================================
    # Widgets
    # ========================================================

    def create_widgets(self):

        # ----------------------------------------------------
        # Folders
        # ----------------------------------------------------

        folders = card(self.body)

        folders.pack(
            fill="x"
        )

        FolderPicker(
            folders,
            "Carpeta de informes PDF",
            self.input_folder,
            dialog_title="Seleccionar carpeta de informes PDF",
            on_change=self.save_folders
        ).pack(
            fill="x",
            padx=20,
            pady=(16, 12)
        )

        FolderPicker(
            folders,
            "Carpeta de salida",
            self.output_folder,
            dialog_title="Seleccionar carpeta de salida",
            on_change=self.save_folders
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 18)
        )

        # ----------------------------------------------------
        # Generate button
        # ----------------------------------------------------

        self.generate_button = primary_button(
            self.body,
            "Generar informes",
            self.start_generation,
            width=240
        )

        self.generate_button.pack(
            pady=(20, 14)
        )

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        self.progress = ctk.CTkProgressBar(
            self.body,
            height=10
        )

        self.progress.pack(
            fill="x",
            pady=(0, 6)
        )

        self.progress.set(0)

        self.progress_label = ctk.CTkLabel(
            self.body,
            text="Listo",
            font=font(12),
            text_color=COLORS["muted"]
        )

        self.progress_label.pack(
            pady=(0, 12)
        )

        # ----------------------------------------------------
        # Open output button
        # (packed before the status box so it always stays
        # visible at the bottom)
        # ----------------------------------------------------

        self.open_output_button = secondary_button(
            self.body,
            "Abrir carpeta de salida",
            self.open_output_folder,
            width=220,
            state="disabled"
        )

        self.open_output_button.pack(
            side="bottom",
            pady=(16, 0)
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = card(self.body)

        status.pack(
            fill="both",
            expand=True
        )

        section_label(
            status,
            "Estado"
        ).pack(
            anchor="w",
            padx=20,
            pady=(14, 4)
        )

        self.status_box = StatusLog(
            status
        )

        self.status_box.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 16)
        )

    # ========================================================
    # Open output folder
    # ========================================================

    def open_output_folder(self):

        folder = self.output_folder.get()

        if folder and Path(folder).is_dir():

            os.startfile(folder)

    # ========================================================
    # Start generation
    # ========================================================

    def start_generation(self):

        input_folder = self.input_folder.get().strip()
        output_folder = self.output_folder.get().strip()

        if not input_folder:

            self.show_status(
                "Seleccione una carpeta de informes PDF.",
                "warning"
            )

            return

        if not output_folder:

            self.show_status(
                "Seleccione una carpeta de salida.",
                "warning"
            )

            return

        if not Path(input_folder).is_dir():

            self.show_status(
                "La carpeta de informes PDF no existe.",
                "error"
            )

            return

        self.save_folders()

        self.status_box.clear()

        self.open_output_button.configure(
            state="disabled"
        )

        self.generate_button.configure(
            state="disabled",
            text="Generando…"
        )

        self.progress.set(0)

        self.progress_label.configure(
            text="Iniciando…"
        )

        thread = threading.Thread(
            target=self.generate_reports_thread,
            args=(
                input_folder,
                output_folder
            ),
            daemon=True
        )

        thread.start()

    # ========================================================
    # Report generation
    # (runs in another thread: it only talks to the window
    # through the queue)
    # ========================================================

    def generate_reports_thread(
        self,
        input_folder,
        output_folder
    ):

        try:

            results = process_folder(
                input_folder,
                output_folder,
                log=lambda line: self.messages.put(
                    ("log", line)
                ),
                on_progress=lambda current, total: self.messages.put(
                    ("progress", (current, total))
                )
            )

        except Exception as error:

            self.messages.put((
                "log",
                f"NO SE PUDO PROCESAR LA CARPETA: {error}"
            ))

            results = []

        self.messages.put(
            ("done", results)
        )

    def poll_messages(self):

        try:

            while True:

                kind, value = self.messages.get_nowait()

                if kind == "log":

                    self.show_status(
                        value,
                        log_kind(value)
                    )

                elif kind == "progress":

                    self.update_progress(*value)

                elif kind == "done":

                    self.generation_finished(value)

        except queue.Empty:

            pass

        self.after(
            100,
            self.poll_messages
        )

    # ========================================================
    # Progress
    # ========================================================

    def update_progress(
        self,
        current,
        total
    ):

        self.progress.set(
            current / total
        )

        self.progress_label.configure(
            text=f"Procesado {current} de {total}"
        )

    # ========================================================
    # Generation finished
    # ========================================================

    def generation_finished(
        self,
        results
    ):

        successful = sum(
            1
            for result in results
            if not result["error"]
        )

        errors = len(results) - successful

        with_errors = sum(
            1
            for result in results
            if any(
                issue["level"] == "ERROR"
                for issue in result["issues"]
            )
        )

        with_warnings = sum(
            1
            for result in results
            if result["issues"]
        )

        without_pdf = sum(
            1
            for result in results
            if result["output"] and not result["pdf_output"]
        )

        self.progress.set(1)

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        self.show_status("")
        self.show_status(
            "==============================",
            "muted"
        )

        if errors == 0 and with_errors == 0:

            self.show_status(
                "✓ GENERACIÓN COMPLETA",
                "success"
            )

        else:

            self.show_status(
                "⚠ GENERACIÓN COMPLETA CON ERRORES",
                "error"
            )

        self.show_status(
            f"Informes procesados: {len(results)}"
        )

        self.show_status(
            f"Generados (Word): {successful}"
        )

        self.show_status(
            f"Generados (PDF): {successful - without_pdf}"
        )

        self.show_status(
            f"No generados: {errors}"
        )

        self.show_status(
            f"Informes con errores para revisar: {with_errors}"
        )

        self.show_status(
            f"Informes con advertencias: {with_warnings}"
        )

        self.show_status(
            "==============================",
            "muted"
        )

        # ----------------------------------------------------
        # Final state
        # ----------------------------------------------------

        if errors == 0:

            self.progress_label.configure(
                text=(
                    f"Completado — "
                    f"{successful} informes generados"
                )
            )

        else:

            self.progress_label.configure(
                text=(
                    f"Completado con errores — "
                    f"{successful} generados, "
                    f"{errors} con error"
                )
            )

        self.generate_button.configure(
            state="normal",
            text="Generar informes"
        )

        if successful > 0:

            self.open_output_button.configure(
                state="normal"
            )

    # ========================================================
    # Status
    # ========================================================

    def show_status(self, message, kind=None):

        self.status_box.write(
            message,
            kind
        )


# ============================================================
# Run application
# ============================================================

if __name__ == "__main__":

    app = ReportApp()

    app.mainloop()
