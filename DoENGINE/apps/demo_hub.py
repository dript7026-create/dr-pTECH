from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_profiles() -> list[dict]:
    return [
        {
            "profile_id": "playhub_adaptive_mode",
            "label": "PlayHub Adaptive Mode",
            "platform": "playhub",
            "power_mode": "desktop",
            "consent": {
                "local_only": True,
                "allow_camera": False,
                "allow_microphone": False,
                "allow_wearables": True,
                "allow_spectral_accessory": True,
                "retain_raw_signals": False,
                "retain_derived_signals": True,
            },
            "band_windows": [
                {
                    "id": "high_response",
                    "label": "High Response Band",
                    "role": "direct-control",
                    "nominal_hz_low": 18.0,
                    "nominal_hz_high": 40.0,
                    "source": "dry-eeg",
                    "confidence_gate": 0.72,
                    "note": "Provisional high-response routing for reflex-style direct character control when accessory quality is strong.",
                },
                {
                    "id": "mid_response",
                    "label": "Mid Response Band",
                    "role": "game-logic",
                    "nominal_hz_low": 8.0,
                    "nominal_hz_high": 18.0,
                    "source": "dry-eeg",
                    "confidence_gate": 0.68,
                    "note": "Feeds encounter pacing, assist surfacing, and environment intensity rather than raw movement.",
                },
                {
                    "id": "low_response",
                    "label": "Low Response Band",
                    "role": "menu-loadout",
                    "nominal_hz_low": 1.0,
                    "nominal_hz_high": 8.0,
                    "source": "dry-eeg",
                    "confidence_gate": 0.7,
                    "note": "Reserved for menus, inventory, loadout, and item-use intent only when stable and user-consented.",
                },
            ],
            "input_routes": [
                {
                    "route_id": "move_aim_primary",
                    "label": "Character control",
                    "role": "direct-control",
                    "target": "move_x,move_y,look_assist",
                    "smoothing_ms": 28,
                    "deadzone": 0.12,
                    "confidence_gate": 0.78,
                    "fallback": "controller cadence and stick input only",
                },
                {
                    "route_id": "combat_flow",
                    "label": "Combat and pacing modulation",
                    "role": "game-logic",
                    "target": "hint_cadence,fx_density,reaction_assist",
                    "smoothing_ms": 140,
                    "deadzone": 0.08,
                    "confidence_gate": 0.66,
                    "fallback": "engagement and retry telemetry",
                },
                {
                    "route_id": "menu_focus",
                    "label": "Menu and inventory control",
                    "role": "menu-loadout",
                    "target": "menu_focus,item_use,inventory_scroll",
                    "smoothing_ms": 220,
                    "deadzone": 0.16,
                    "confidence_gate": 0.74,
                    "fallback": "d-pad or pointer navigation",
                },
            ],
            "haptics": {
                "profile_id": "playhub_fiber_feedback",
                "label": "PlayHub fiber haptics",
                "overload_clamp": 0.72,
                "notes": [
                    "Keep desktop chair or desk-band outputs below distraction threshold.",
                    "Use mid-band game-logic state to modulate ambience rather than direct force cues.",
                ],
                "channels": [
                    {
                        "channel_id": "left_grip",
                        "label": "Left grip fiber",
                        "placement": "left-grip",
                        "amplitude": 0.65,
                        "carrier_hz": 145.0,
                        "envelope_ms": 80,
                        "duty_cycle_limit": 0.45,
                    },
                    {
                        "channel_id": "right_grip",
                        "label": "Right grip fiber",
                        "placement": "right-grip",
                        "amplitude": 0.65,
                        "carrier_hz": 145.0,
                        "envelope_ms": 80,
                        "duty_cycle_limit": 0.45,
                    },
                    {
                        "channel_id": "desk_band",
                        "label": "Desk or seat feedback fiber",
                        "placement": "desk",
                        "amplitude": 0.32,
                        "carrier_hz": 92.0,
                        "envelope_ms": 160,
                        "duty_cycle_limit": 0.25,
                    },
                ],
            },
            "wireless_isolation": {
                "profile_id": "playhub_secure_local",
                "label": "PlayHub secure local transport",
                "bluetooth_allowed": True,
                "wifi_allowed": True,
                "require_pairing_handshake": True,
                "rotate_session_keys": True,
                "local_only_control_plane": True,
                "allow_inbound_remote_control": False,
                "sensor_bus_segregated": True,
                "notes": [
                    "Sensor and control buses stay isolated after handshake.",
                    "No inbound remote control ports are open by default.",
                    "Wireless radios may transport only paired accessory payloads, never unauthenticated command injection.",
                ],
            },
            "runtime_state": {
                "receptivity_score": 0.63,
                "cognitive_load_score": 0.41,
                "stress_activation_score": 0.34,
                "fatigue_score": 0.26,
                "engagement_score": 0.77,
                "confidence": 0.69,
                "signal_quality": [
                    {"source": "controller-cadence", "quality": 0.92, "confidence": 0.88, "enabled": True},
                    {"source": "desktop-telemetry", "quality": 0.86, "confidence": 0.83, "enabled": True},
                    {"source": "dry-eeg", "quality": 0.63, "confidence": 0.69, "enabled": True},
                ],
                "adaptation_recommendations": [
                    "Keep high-response direct control assist active only while spectral confidence remains above gate.",
                    "Reduce HUD clutter slightly during sustained high combat density.",
                ],
            },
            "notes": [
                "PlayHub is the proving ground for software-first adaptive validation.",
                "Direct control routing is accessory-assisted and must always degrade to standard controller input.",
            ],
        },
        {
            "profile_id": "nanoplayt_handheld_profile",
            "label": "NanoPlay_t Handheld Profile",
            "platform": "nanoplayt",
            "power_mode": "battery-disciplined",
            "consent": {
                "local_only": True,
                "allow_camera": False,
                "allow_microphone": False,
                "allow_wearables": True,
                "allow_spectral_accessory": True,
                "retain_raw_signals": False,
                "retain_derived_signals": True,
            },
            "band_windows": [
                {
                    "id": "high_response",
                    "label": "High Response Band",
                    "role": "direct-control",
                    "nominal_hz_low": 20.0,
                    "nominal_hz_high": 38.0,
                    "source": "ear-eeg",
                    "confidence_gate": 0.76,
                    "note": "Handheld direct-control route only when accessory fit and power budget permit; otherwise fall back immediately.",
                },
                {
                    "id": "mid_response",
                    "label": "Mid Response Band",
                    "role": "game-logic",
                    "nominal_hz_low": 8.0,
                    "nominal_hz_high": 16.0,
                    "source": "ear-eeg",
                    "confidence_gate": 0.7,
                    "note": "Used for handheld pacing, haptic softening, and UI compression.",
                },
                {
                    "id": "low_response",
                    "label": "Low Response Band",
                    "role": "menu-loadout",
                    "nominal_hz_low": 1.5,
                    "nominal_hz_high": 8.0,
                    "source": "ear-eeg",
                    "confidence_gate": 0.74,
                    "note": "Reserved for menu focus and item-use confirmation, never mandatory for baseline navigation.",
                },
            ],
            "input_routes": [
                {
                    "route_id": "nanoplayt_traversal",
                    "label": "Traversal assist",
                    "role": "direct-control",
                    "target": "aim_bias,gyro_targeting,assist_lock",
                    "smoothing_ms": 24,
                    "deadzone": 0.14,
                    "confidence_gate": 0.8,
                    "fallback": "sticks plus gyro only",
                },
                {
                    "route_id": "nanoplayt_state_shaping",
                    "label": "Experience shaping",
                    "role": "game-logic",
                    "target": "hud_density,hint_cadence,rumble_softening",
                    "smoothing_ms": 180,
                    "deadzone": 0.1,
                    "confidence_gate": 0.68,
                    "fallback": "session fatigue trend and gameplay telemetry",
                },
                {
                    "route_id": "nanoplayt_menu_focus",
                    "label": "Menu and loadout focus",
                    "role": "menu-loadout",
                    "target": "inventory_focus,menu_tab_shift,item_use_focus",
                    "smoothing_ms": 260,
                    "deadzone": 0.18,
                    "confidence_gate": 0.76,
                    "fallback": "d-pad and shoulder menu shortcuts",
                },
            ],
            "haptics": {
                "profile_id": "nanoplayt_fiber_feedback",
                "label": "NanoPlay_t fiber haptics",
                "overload_clamp": 0.64,
                "notes": [
                    "Handheld haptics must remain battery-aware.",
                    "Vibrational fibers emphasize clarity over force.",
                ],
                "channels": [
                    {
                        "channel_id": "left_grip",
                        "label": "Left grip fiber",
                        "placement": "left-grip",
                        "amplitude": 0.58,
                        "carrier_hz": 132.0,
                        "envelope_ms": 72,
                        "duty_cycle_limit": 0.38,
                    },
                    {
                        "channel_id": "right_grip",
                        "label": "Right grip fiber",
                        "placement": "right-grip",
                        "amplitude": 0.58,
                        "carrier_hz": 132.0,
                        "envelope_ms": 72,
                        "duty_cycle_limit": 0.38,
                    },
                    {
                        "channel_id": "shoulder_band",
                        "label": "Shoulder feedback fiber",
                        "placement": "shoulder-band",
                        "amplitude": 0.24,
                        "carrier_hz": 84.0,
                        "envelope_ms": 110,
                        "duty_cycle_limit": 0.18,
                    },
                ],
            },
            "wireless_isolation": {
                "profile_id": "nanoplayt_secure_local",
                "label": "NanoPlay_t secure local transport",
                "bluetooth_allowed": True,
                "wifi_allowed": True,
                "require_pairing_handshake": True,
                "rotate_session_keys": True,
                "local_only_control_plane": True,
                "allow_inbound_remote_control": False,
                "sensor_bus_segregated": True,
                "notes": [
                    "Reserve RF headroom for accessories without letting radios share raw control payloads post-handshake.",
                    "Use signed local session brokers and reject new pairing while gameplay-critical control streams are active.",
                    "No backdoor management channel is exposed on consumer builds.",
                ],
            },
            "runtime_state": {
                "receptivity_score": 0.58,
                "cognitive_load_score": 0.49,
                "stress_activation_score": 0.29,
                "fatigue_score": 0.33,
                "engagement_score": 0.72,
                "confidence": 0.64,
                "signal_quality": [
                    {"source": "controller-cadence", "quality": 0.9, "confidence": 0.87, "enabled": True},
                    {"source": "imu", "quality": 0.82, "confidence": 0.79, "enabled": True},
                    {"source": "ear-eeg", "quality": 0.59, "confidence": 0.64, "enabled": True},
                ],
                "adaptation_recommendations": [
                    "Compress HUD density on small-screen combat moments.",
                    "Clamp haptic output while fatigue trend is rising.",
                ],
            },
            "notes": [
                "NanoPlay_t inherits the PlayHub contract but stays battery- and suspend-safe first.",
                "Spectral input routes are optional overlays, never exclusive control requirements.",
            ],
        },
    ]


def build_state() -> dict:
    profiles = build_profiles()
    return {
        "app": "drIpTECH Demo Hub",
        "mode": "Adaptive Resonance Prototype",
        "profiles": profiles,
        "shared_contract": {
            "fields": [
                "receptivity_score",
                "cognitive_load_score",
                "stress_activation_score",
                "fatigue_score",
                "engagement_score",
                "confidence",
                "signal_quality",
                "adaptation_recommendations",
            ],
            "routing_rule": "Direct-control only when spectral confidence clears the per-route gate; otherwise use standard input fallback.",
            "security_rule": "Sensor acquisition, control mapping, and wireless transport remain isolated after pairing handshake with no inbound remote control plane.",
        },
    }


class DemoHubApp:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("drIpTECH Demo Hub")
        self.master.geometry("1280x900")
        self.master.configure(bg="#0a1016")

        self.state = build_state()
        self.profile_index = 0
        self.status_var = tk.StringVar(value="Adaptive Resonance prototype ready.")
        self.profile_var = tk.StringVar(value=self.state["profiles"][0]["label"])

        self._build_header()
        self._build_controls()
        self._build_body()
        self.refresh_views()

    def _build_header(self) -> None:
        header = tk.Frame(self.master, bg="#0a1016")
        header.pack(fill="x", padx=18, pady=(18, 8))

        canvas = tk.Canvas(header, width=260, height=124, bg="#0a1016", highlightthickness=0)
        canvas.pack(side="left")
        canvas.create_rectangle(24, 18, 236, 108, outline="", fill="#111c25")
        canvas.create_text(38, 38, text="drIpTECH", anchor="w", fill="#f1f6fb", font=("Segoe UI", 18, "bold"))
        canvas.create_text(38, 66, text="DEMO HUB", anchor="w", fill="#7dd3fc", font=("Segoe UI", 26, "bold"))
        canvas.create_text(38, 92, text="NanoPlay_t + PlayHub adaptive control lab", anchor="w", fill="#97a9bb", font=("Segoe UI", 10))

        text_block = tk.Frame(header, bg="#0a1016")
        text_block.pack(side="left", fill="both", expand=True, padx=12)
        tk.Label(text_block, text="Adaptive Resonance Prototype", fg="#f1f6fb", bg="#0a1016", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(
            text_block,
            text="Prototype shell for Receptivity Sandbox, PlayHub Adaptive Mode, and NanoPlay_t handheld profiles with haptics, spectral routing, and secure local transport assumptions.",
            fg="#9cb0c3",
            bg="#0a1016",
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(4, 0))

    def _build_controls(self) -> None:
        controls = tk.Frame(self.master, bg="#0a1016")
        controls.pack(fill="x", padx=18, pady=(0, 10))

        ttk.Label(controls, text="Runtime profile").pack(side="left")
        profile_box = ttk.Combobox(
            controls,
            textvariable=self.profile_var,
            values=[profile["label"] for profile in self.state["profiles"]],
            state="readonly",
            width=30,
        )
        profile_box.pack(side="left", padx=(8, 14))
        profile_box.bind("<<ComboboxSelected>>", self._on_profile_changed)

        tk.Button(controls, text="Refresh", command=self.refresh_state, bg="#1d2a36", fg="#f0f6ff", activebackground="#25506e", relief="flat", padx=12, pady=8).pack(side="left", padx=(0, 8))
        tk.Button(controls, text="Export Snapshot", command=self.export_snapshot, bg="#163f2d", fg="#f0f6ff", activebackground="#1d5f43", relief="flat", padx=12, pady=8).pack(side="left")

        tk.Label(controls, textvariable=self.status_var, fg="#7ee787", bg="#0a1016", font=("Segoe UI", 10)).pack(side="left", padx=12)

    def _build_body(self) -> None:
        notebook = ttk.Notebook(self.master)
        notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self.summary_text = self._add_tab(notebook, "Summary")
        self.spectral_text = self._add_tab(notebook, "Spectral Routing")
        self.haptics_text = self._add_tab(notebook, "Haptics")
        self.security_text = self._add_tab(notebook, "Wireless Isolation")
        self.runtime_text = self._add_tab(notebook, "Runtime State")
        self.contract_text = self._add_tab(notebook, "Shared Contract")

    def _add_tab(self, notebook: ttk.Notebook, label: str) -> tk.Text:
        frame = tk.Frame(notebook, bg="#111922")
        notebook.add(frame, text=label)
        text = tk.Text(frame, wrap="word", bg="#111922", fg="#d6e2ef", insertbackground="#d6e2ef", relief="flat", font=("Cascadia Mono", 10))
        text.pack(fill="both", expand=True)
        return text

    def _current_profile(self) -> dict:
        return self.state["profiles"][self.profile_index]

    def _write_text(self, widget: tk.Text, payload: object) -> None:
        widget.delete("1.0", "end")
        widget.insert("1.0", json.dumps(payload, indent=2))

    def refresh_views(self) -> None:
        profile = self._current_profile()
        summary = {
            "app": self.state["app"],
            "mode": self.state["mode"],
            "profile": profile["label"],
            "platform": profile["platform"],
            "power_mode": profile["power_mode"],
            "notes": profile["notes"],
        }
        self._write_text(self.summary_text, summary)
        self._write_text(self.spectral_text, {"band_windows": profile["band_windows"], "input_routes": profile["input_routes"]})
        self._write_text(self.haptics_text, profile["haptics"])
        self._write_text(self.security_text, {"consent": profile["consent"], "wireless_isolation": profile["wireless_isolation"]})
        self._write_text(self.runtime_text, profile["runtime_state"])
        self._write_text(self.contract_text, self.state["shared_contract"])

    def refresh_state(self) -> None:
        self.state = build_state()
        self.refresh_views()
        self.status_var.set("Refreshed adaptive profiles.")

    def export_snapshot(self) -> None:
        out_dir = ROOT / "generated" / "demo_hub"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "adaptive_resonance_demo_state.json"
        out_path.write_text(json.dumps(self.state, indent=2) + "\n", encoding="utf-8")
        self.status_var.set(f"Exported snapshot to {out_path}")

    def _on_profile_changed(self, _event: object) -> None:
        labels = [profile["label"] for profile in self.state["profiles"]]
        self.profile_index = labels.index(self.profile_var.get())
        self.refresh_views()
        self.status_var.set(f"Loaded {self.profile_var.get()}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="drIpTECH Demo Hub adaptive prototype")
    parser.add_argument("--dump-state", action="store_true")
    args = parser.parse_args()

    state = build_state()
    if args.dump_state:
        print(json.dumps(state, indent=2))
        return 0

    root = tk.Tk()
    ttk.Style().theme_use("default")
    DemoHubApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())