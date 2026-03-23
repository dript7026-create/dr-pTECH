import argparse
import json
import os
import subprocess
import sys
import threading
import traceback
from pathlib import Path
from queue import Empty, Queue
import tkinter as tk
from tkinter import messagebox, ttk

from validate_pipeline_core import ROOT, ValidationFailure, run_validation_suite


def _open_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    if hasattr(os, "startfile"):
        os.startfile(path)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
        return
    subprocess.Popen(["xdg-open", str(path)])


class ValidatorApp:
    def __init__(self, root: tk.Tk, *, initial_suite: str = "sample", auto_run: bool = False) -> None:
        self.root = root
        self.root.title("egosphere Pipeline Validator")
        self.root.geometry("1220x860")
        self.root.minsize(960, 700)

        self.queue: Queue[tuple[str, object]] = Queue()
        self.worker: threading.Thread | None = None

        self.suite_var = tk.StringVar(value=initial_suite)
        self.status_var = tk.StringVar(value="Ready")
        self.sample_var = tk.StringVar(value="Sample: idle")
        self.pertinence_var = tk.StringVar(value="Pertinence: idle")
        self.output_var = tk.StringVar(value=f"Output root: {(ROOT / 'pipeline' / 'out').as_posix()}")

        self._build_layout()
        self.root.after(100, self._process_queue)

        if auto_run:
            self.root.after(250, self.start_validation)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        toolbar = ttk.Frame(self.root, padding=12)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(6, weight=1)

        ttk.Label(toolbar, text="Suite").grid(row=0, column=0, sticky="w")
        suite_box = ttk.Combobox(
            toolbar,
            textvariable=self.suite_var,
            values=("sample", "pertinence", "all"),
            state="readonly",
            width=16,
        )
        suite_box.grid(row=0, column=1, padx=(8, 16), sticky="w")

        self.run_button = ttk.Button(toolbar, text="Run Validation", command=self.start_validation)
        self.run_button.grid(row=0, column=2, sticky="w")

        ttk.Button(toolbar, text="Open Output Folder", command=self.open_output_folder).grid(
            row=0,
            column=3,
            padx=(8, 0),
            sticky="w",
        )
        ttk.Button(toolbar, text="Copy JSON", command=self.copy_json).grid(row=0, column=4, padx=(8, 0), sticky="w")

        ttk.Label(toolbar, textvariable=self.status_var, anchor="e").grid(row=0, column=6, sticky="e")

        metrics = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        metrics.grid(row=1, column=0, sticky="ew")
        metrics.columnconfigure(0, weight=1)
        metrics.columnconfigure(1, weight=1)
        metrics.columnconfigure(2, weight=1)

        ttk.Label(metrics, textvariable=self.sample_var, relief="groove", padding=10).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(metrics, textvariable=self.pertinence_var, relief="groove", padding=10).grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Label(metrics, textvariable=self.output_var, relief="groove", padding=10).grid(row=0, column=2, sticky="ew")

        panes = ttk.Panedwindow(self.root, orient="horizontal")
        panes.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        log_frame = ttk.Labelframe(panes, text="Execution Log", padding=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, wrap="word", height=20)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

        summary_frame = ttk.Labelframe(panes, text="Validation Summary", padding=8)
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)
        self.summary_text = tk.Text(summary_frame, wrap="none", height=20)
        summary_y = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary_text.yview)
        summary_x = ttk.Scrollbar(summary_frame, orient="horizontal", command=self.summary_text.xview)
        self.summary_text.configure(yscrollcommand=summary_y.set, xscrollcommand=summary_x.set)
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        summary_y.grid(row=0, column=1, sticky="ns")
        summary_x.grid(row=1, column=0, sticky="ew")

        panes.add(log_frame, weight=1)
        panes.add(summary_frame, weight=1)

    def append_log(self, text: str) -> None:
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def set_summary(self, payload: dict) -> None:
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", json.dumps(payload, indent=2))
        self._update_metrics(payload)

    def _update_metrics(self, payload: dict) -> None:
        sample = next((item for item in payload.get("results", []) if item.get("project") == "sample"), None)
        pertinence = next((item for item in payload.get("results", []) if item.get("project") == "pertinence"), None)

        if sample is None:
            self.sample_var.set("Sample: not run")
        else:
            self.sample_var.set(
                "Sample: "
                f"{sample.get('project_name', 'unknown')} | systems {sample.get('system_count', 0)} | "
                f"entities {sample.get('entity_count', 0)} | precache {sample.get('precache_count', 0)}"
            )

        if pertinence is None:
            self.pertinence_var.set("Pertinence: not run")
        else:
            blender = pertinence.get("blender_report", {})
            idtech = pertinence.get("idtech_summary", {})
            self.pertinence_var.set(
                "Pertinence: "
                f"png {pertinence.get('png_assets_checked', 0)} | scenes {blender.get('scene_count', 0)} | "
                f"assets {idtech.get('asset_count', 0)} | precache {idtech.get('precache_count', 0)}"
            )

    def start_validation(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            return

        suite = self.suite_var.get()
        self.status_var.set(f"Running {suite} suite...")
        self.append_log(f"Starting validation suite: {suite}")
        self.run_button.state(["disabled"])

        def worker() -> None:
            def on_event(level: str, message: str, details: dict) -> None:
                self.queue.put(("event", (level, message, details)))

            try:
                summary = run_validation_suite(suite, on_event=on_event)
            except Exception as exc:
                trace = traceback.format_exc()
                payload = {
                    "error": str(exc),
                    "details": exc.details if isinstance(exc, ValidationFailure) else {},
                    "traceback": trace,
                }
                self.queue.put(("error", payload))
            else:
                self.queue.put(("result", summary))
            finally:
                self.queue.put(("done", suite))

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def _process_queue(self) -> None:
        try:
            while True:
                kind, payload = self.queue.get_nowait()
                if kind == "event":
                    level, message, details = payload
                    line = f"[{level}] {message}"
                    text = details.get("text") if isinstance(details, dict) else None
                    if text:
                        line = f"{line}\n{text}"
                    self.append_log(line)
                elif kind == "result":
                    self.status_var.set("Validation passed")
                    self.set_summary(payload)
                    self.append_log("Validation suite completed successfully.")
                elif kind == "error":
                    self.status_var.set("Validation failed")
                    self.set_summary(payload)
                    self.append_log("Validation suite failed. See summary pane for details.")
                    messagebox.showerror("egosphere Pipeline Validator", str(payload.get("error", "Validation failed")))
                elif kind == "done":
                    self.run_button.state(["!disabled"])
        except Empty:
            pass
        finally:
            self.root.after(100, self._process_queue)

    def open_output_folder(self) -> None:
        target = ROOT / "pipeline" / "out"
        try:
            _open_path(target)
        except FileNotFoundError:
            messagebox.showinfo("egosphere Pipeline Validator", f"Output folder does not exist yet:\n{target}")

    def copy_json(self) -> None:
        content = self.summary_text.get("1.0", "end").strip()
        if not content:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set("Summary JSON copied to clipboard")


def launch_app(*, initial_suite: str = "sample", auto_run: bool = False) -> int:
    root = tk.Tk()
    ValidatorApp(root, initial_suite=initial_suite, auto_run=auto_run)
    root.mainloop()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the egosphere pipeline validation desktop app")
    parser.add_argument("--suite", choices=["sample", "pertinence", "all"], default="sample")
    parser.add_argument("--run", action="store_true", help="Start validation immediately after launch")
    args = parser.parse_args(argv)
    return launch_app(initial_suite=args.suite, auto_run=args.run)


if __name__ == "__main__":
    raise SystemExit(main())