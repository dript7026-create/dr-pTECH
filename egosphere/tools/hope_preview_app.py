from __future__ import annotations

import argparse
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk

try:
    from hope_runtime_sample import build_preview_snapshot
except ImportError:
    from egosphere.tools.hope_runtime_sample import build_preview_snapshot


def _format_scene_card(scene: dict) -> str:
    return (
        f"{scene['scene_id']}\n"
        f"type: {scene['scene_type']}\n"
        f"tail: {scene['tail_ms']} ms\n"
        f"coherence: {scene['coherence']}\n"
        f"ecology: {scene['ecology_stability']}\n"
        f"transition: {scene['transition_bias']}"
    )


def launch_preview(project_path: Path, *, ticks: int = 2, cycles: int = 1) -> int:
    snapshot = build_preview_snapshot(project_path, ticks=ticks, cycles=cycles)
    root = tk.Tk()
    root.title(f"HOPE Preview :: {snapshot['project_name']}")
    root.geometry("920x640")

    container = ttk.Frame(root, padding=12)
    container.pack(fill=tk.BOTH, expand=True)

    heading = ttk.Label(container, text=snapshot["project_name"], font=("Segoe UI Semibold", 16))
    heading.pack(anchor="w")

    graph = ttk.Label(container, text=" -> ".join(snapshot["system_graph"]), wraplength=860, justify=tk.LEFT)
    graph.pack(anchor="w", pady=(6, 12))

    sanctuary = snapshot["sanctuary_state"]
    sanctuary_text = (
        f"Sanctuary harmony: {sanctuary['harmony']}\n"
        f"Care: {sanctuary['care']}\n"
        f"Memory: {sanctuary['memory']}\n"
        f"Transitions: {sanctuary['transitions']}\n"
        f"Current scene: {sanctuary['current_scene']}"
    )
    ttk.Label(container, text=sanctuary_text, justify=tk.LEFT).pack(anchor="w", pady=(0, 12))

    cards_frame = ttk.Frame(container)
    cards_frame.pack(fill=tk.BOTH, expand=True)
    for index, scene in enumerate(snapshot["scene_cards"]):
        card = ttk.LabelFrame(cards_frame, text=scene["scene_id"], padding=10)
        card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=6, pady=6)
        ttk.Label(card, text=_format_scene_card(scene), justify=tk.LEFT).pack(anchor="w")

    for column in range(2):
        cards_frame.columnconfigure(column, weight=1)

    export_path = project_path.with_name("hope_preview_snapshot.json")
    export_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    ttk.Label(container, text=f"Snapshot exported to {export_path}", wraplength=860).pack(anchor="w", pady=(12, 0))

    root.mainloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the HOPE preview app")
    parser.add_argument("project", type=Path)
    parser.add_argument("--ticks", type=int, default=2)
    parser.add_argument("--cycles", type=int, default=1)
    args = parser.parse_args()
    return launch_preview(args.project, ticks=args.ticks, cycles=args.cycles)


if __name__ == "__main__":
    raise SystemExit(main())