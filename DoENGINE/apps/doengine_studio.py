from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bango_integration_paths import resolve_bango_asset_root, resolve_bango_project_root, resolve_clip_blend_id_dir, resolve_playnow_finalstage_path


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def collect_state() -> dict:
    asset_root = resolve_bango_asset_root()
    bango_root = resolve_clip_blend_id_dir(asset_root)
    return {
        'asset_root': str(asset_root),
        'doengine_gui_summary': load_json(ROOT / 'generated' / 'doengine_gui_asset_summary.json'),
        'donow_manifest': load_json(bango_root / 'donow_runtime_manifest.json'),
        'bango_pipeline_report': load_json(bango_root / 'pipeline_report.json'),
        'bango_protocol': load_json(bango_root / 'bango_patoot_clip_blend_id_protocol.json'),
        'playnow_finalstage': load_json(resolve_playnow_finalstage_path(asset_root)),
    }


def run_command(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


class DoEngineStudio:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        master.title('DoENGINE Studio')
        master.geometry('1180x820')
        master.configure(bg='#0d1218')

        self.state = collect_state()
        self.status_var = tk.StringVar(value='Ready.')

        self._build_header()
        self._build_controls()
        self._build_body()
        self.refresh_views()

    def _build_header(self) -> None:
        header = tk.Frame(self.master, bg='#0d1218')
        header.pack(fill='x', padx=16, pady=(16, 8))

        canvas = tk.Canvas(header, width=240, height=120, bg='#0d1218', highlightthickness=0)
        canvas.pack(side='left')
        canvas.create_rectangle(78, 18, 120, 102, fill='#0a0a0a', outline='')
        canvas.create_polygon(74, 22, 124, 22, 134, 102, 70, 102, fill='#1aa34a', outline='')
        canvas.create_text(60, 28, text='Do', anchor='w', fill='#29a7ff', font=('Segoe UI', 26, 'bold'))
        canvas.create_polygon(128, 8, 170, 18, 154, 112, 130, 116, 118, 104, 136, 34, fill='#ff2837', outline='')
        canvas.create_text(128, 92, text='ENGINE STUDIO', anchor='w', fill='#f0f6ff', font=('Segoe UI', 12, 'bold'))

        text_block = tk.Frame(header, bg='#0d1218')
        text_block.pack(side='left', fill='both', expand=True, padx=12)
        tk.Label(text_block, text='DoENGINE Studio', fg='#f0f6ff', bg='#0d1218', font=('Segoe UI', 24, 'bold')).pack(anchor='w')
        tk.Label(
            text_block,
            text='Standalone DoENGINE GUI for DoNOW ingest, Bango pipeline review, GUI asset generation, and engine-ready stream setup.',
            fg='#8fa7bd',
            bg='#0d1218',
            font=('Segoe UI', 11),
        ).pack(anchor='w', pady=(4, 0))

    def _build_controls(self) -> None:
        controls = tk.Frame(self.master, bg='#0d1218')
        controls.pack(fill='x', padx=16, pady=(0, 8))

        buttons = [
            ('Refresh', self.refresh_state),
            ('Build GUI Manifest', self.build_gui_manifest),
            ('Build DoNOW Manifest', self.build_donow_manifest),
        ]
        for label, command in buttons:
            tk.Button(controls, text=label, command=command, bg='#1d2a36', fg='#f0f6ff', activebackground='#25506e', relief='flat', padx=12, pady=8).pack(side='left', padx=(0, 8))

        tk.Label(controls, textvariable=self.status_var, fg='#7ee787', bg='#0d1218', font=('Segoe UI', 10)).pack(side='left', padx=12)

    def _build_body(self) -> None:
        notebook = ttk.Notebook(self.master)
        notebook.pack(fill='both', expand=True, padx=16, pady=(0, 16))

        self.summary_text = self._add_tab(notebook, 'Summary')
        self.donow_text = self._add_tab(notebook, 'DoNOW')
        self.pipeline_text = self._add_tab(notebook, 'Bango Pipeline')
        self.gui_text = self._add_tab(notebook, 'GUI Assets')

    def _add_tab(self, notebook: ttk.Notebook, label: str) -> tk.Text:
        frame = tk.Frame(notebook, bg='#111922')
        notebook.add(frame, text=label)
        text = tk.Text(frame, wrap='word', bg='#111922', fg='#d6e2ef', insertbackground='#d6e2ef', relief='flat', font=('Cascadia Mono', 10))
        text.pack(fill='both', expand=True)
        return text

    def refresh_views(self) -> None:
        summary = {
            'asset_root': self.state.get('asset_root'),
            'doengine_gui_summary': self.state.get('doengine_gui_summary'),
            'donow_manifest_present': self.state.get('donow_manifest') is not None,
            'pipeline_report_present': self.state.get('bango_pipeline_report') is not None,
            'playnow_finalstage_present': self.state.get('playnow_finalstage') is not None,
        }
        self._write_text(self.summary_text, summary)
        self._write_text(self.donow_text, self.state.get('donow_manifest') or {'status': 'missing'})
        self._write_text(self.pipeline_text, self.state.get('bango_pipeline_report') or {'status': 'missing'})
        self._write_text(self.gui_text, self.state.get('doengine_gui_summary') or {'status': 'missing'})

    def _write_text(self, widget: tk.Text, payload: object) -> None:
        widget.delete('1.0', 'end')
        widget.insert('1.0', json.dumps(payload, indent=2))

    def refresh_state(self) -> None:
        self.state = collect_state()
        self.refresh_views()
        self.status_var.set('Refreshed state from generated manifests.')

    def build_gui_manifest(self) -> None:
        command = [sys.executable, str(ROOT / 'tools' / 'build_doengine_gui_asset_manifest.py')]
        returncode, stdout, stderr = run_command(command)
        self.status_var.set(f'GUI manifest build returned {returncode}.')
        self.refresh_state()
        if stdout:
            self._write_text(self.gui_text, json.loads(stdout))
        elif stderr:
            self._write_text(self.gui_text, {'stderr': stderr, 'returncode': returncode})

    def build_donow_manifest(self) -> None:
        bango_project_root = resolve_bango_project_root()
        asset_root = resolve_bango_asset_root()
        source = bango_project_root / 'recraft' / 'bango_patoot_production_21000_credit_manifest.json'
        out = resolve_clip_blend_id_dir(asset_root) / 'donow_runtime_manifest.json'
        command = [sys.executable, str(ROOT / 'tools' / 'build_donow_runtime_manifest.py'), '--source', str(source), '--out', str(out)]
        returncode, stdout, stderr = run_command(command)
        self.status_var.set(f'DoNOW manifest build returned {returncode}.')
        self.refresh_state()
        if stdout:
            self._write_text(self.donow_text, json.loads(stdout))
        elif stderr:
            self._write_text(self.donow_text, {'stderr': stderr, 'returncode': returncode})


def main() -> int:
    parser = argparse.ArgumentParser(description='DoENGINE Studio GUI')
    parser.add_argument('--dump-state', action='store_true')
    args = parser.parse_args()

    state = collect_state()
    if args.dump_state:
        print(json.dumps(state, indent=2))
        return 0

    root = tk.Tk()
    ttk.Style().theme_use('default')
    DoEngineStudio(root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())