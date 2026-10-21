"""
Interfaz gráfica para generar los informes en español.

Uso:
    python gui.py
"""

import json
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config import INPUT, OUTPUT

from pipeline import process_folder


# Recuerda las últimas carpetas elegidas
SETTINGS_FILE = Path.home() / ".eone_informes.json"


def load_settings():

    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)

    except (OSError, ValueError):
        return {}


def save_settings(settings):

    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    except OSError:
        pass


class App:

    def __init__(self, root):

        self.root = root
        self.messages = queue.Queue()

        settings = load_settings()

        self.input_dir = tk.StringVar(value=settings.get("input", str(INPUT)))
        self.output_dir = tk.StringVar(value=settings.get("output", str(OUTPUT)))

        root.title("Informes EONE - Microarray")
        root.geometry("860x560")
        root.minsize(640, 400)

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(4, weight=1)

        # -----------------------------------------
        # Carpetas
        # -----------------------------------------

        ttk.Label(frame, text="Informes originales (PDF):").grid(
            row=0, column=0, sticky="w", pady=4
        )
        ttk.Entry(frame, textvariable=self.input_dir).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(
            frame, text="Elegir...",
            command=lambda: self.choose_folder(self.input_dir)
        ).grid(row=0, column=2)

        ttk.Label(frame, text="Informes traducidos (salida):").grid(
            row=1, column=0, sticky="w", pady=4
        )
        ttk.Entry(frame, textvariable=self.output_dir).grid(
            row=1, column=1, sticky="ew", padx=8
        )
        ttk.Button(
            frame, text="Elegir...",
            command=lambda: self.choose_folder(self.output_dir)
        ).grid(row=1, column=2)

        # -----------------------------------------
        # Acciones
        # -----------------------------------------

        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 6))

        self.run_button = ttk.Button(
            buttons, text="Generar informes", command=self.run
        )
        self.run_button.pack(side="left")

        ttk.Button(
            buttons, text="Abrir carpeta de salida", command=self.open_output
        ).pack(side="left", padx=8)

        self.progress = ttk.Progressbar(frame, mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=3, sticky="ew", pady=4)

        # -----------------------------------------
        # Registro
        # -----------------------------------------

        log_frame = ttk.Frame(frame)
        log_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame, wrap="word", state="disabled", font=("Consolas", 9)
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.tag_configure("ERROR", foreground="#b00020")
        self.log_text.tag_configure("AVISO", foreground="#9a6700")

        self.root.after(100, self.poll_messages)

    def choose_folder(self, variable):

        folder = filedialog.askdirectory(
            initialdir=variable.get() or str(Path.home())
        )

        if folder:
            variable.set(str(Path(folder)))

    def open_output(self):

        folder = Path(self.output_dir.get())

        if folder.is_dir():
            os.startfile(folder)
        else:
            messagebox.showwarning(
                "Carpeta de salida", "La carpeta de salida todavía no existe."
            )

    def write_log(self, line):

        if "[ERROR]" in line or line.startswith("NO SE PUDO"):
            tag = "ERROR"
        elif "[AVISO]" in line:
            tag = "AVISO"
        else:
            tag = ""

        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def run(self):

        input_dir = Path(self.input_dir.get().strip())
        output_dir = Path(self.output_dir.get().strip())

        if not input_dir.is_dir():

            messagebox.showerror(
                "Carpeta de informes",
                "La carpeta de informes originales no existe."
            )
            return

        if not self.output_dir.get().strip():

            messagebox.showerror(
                "Carpeta de salida", "Elegí una carpeta de salida."
            )
            return

        save_settings({"input": str(input_dir), "output": str(output_dir)})

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self.progress["value"] = 0
        self.run_button.configure(state="disabled")

        threading.Thread(
            target=self.worker,
            args=(input_dir, output_dir),
            daemon=True
        ).start()

    def worker(self, input_dir, output_dir):
        """
        Corre en otro hilo: solo se comunica con la ventana por la cola.
        """

        try:

            results = process_folder(
                input_dir,
                output_dir,
                log=lambda line: self.messages.put(("log", line)),
                on_progress=lambda done, total: self.messages.put(
                    ("progress", (done, total))
                )
            )

        except Exception as error:

            self.messages.put(("log", f"NO SE PUDO PROCESAR LA CARPETA: {error}"))
            results = []

        self.messages.put(("done", results))

    def poll_messages(self):

        try:

            while True:

                kind, value = self.messages.get_nowait()

                if kind == "log":
                    self.write_log(value)

                elif kind == "progress":
                    self.progress["maximum"] = value[1]
                    self.progress["value"] = value[0]

                elif kind == "done":
                    self.finish(value)

        except queue.Empty:
            pass

        self.root.after(100, self.poll_messages)

    def finish(self, results):

        self.run_button.configure(state="normal")

        if not results:
            return

        failed = sum(1 for r in results if r["error"])

        with_errors = sum(
            1 for r in results
            if any(issue["level"] == "ERROR" for issue in r["issues"])
        )

        summary = f"Informes generados: {len(results) - failed} de {len(results)}."

        if with_errors:
            summary += f"\nCon errores en la tabla para revisar: {with_errors}."

        if failed:
            summary += f"\nNo generados: {failed}."

        if failed or with_errors:
            messagebox.showwarning("Proceso terminado", summary)
        else:
            messagebox.showinfo("Proceso terminado", summary)


def main():

    root = tk.Tk()

    App(root)

    root.mainloop()


if __name__ == "__main__":
    main()
