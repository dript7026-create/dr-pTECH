from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import messagebox, ttk


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parents[2]
PROJECTS_ROOT = ROOT / "projects"
JUMPCLIP_ROOT = WORKSPACE_ROOT / "JumpClip"
JUMPCLIP_SRC = JUMPCLIP_ROOT / "src"
JUMPCLIP_PROFILE = JUMPCLIP_ROOT / "examples" / "sample_references.json"
JUMPCLIP_PIPELINE = JUMPCLIP_ROOT / "examples" / "game_pipeline.json"
RECRAFT_RUNNER = WORKSPACE_ROOT / "egosphere" / "tools" / "run_recraft_manifest.py"
FARIM_PACKER = ROOT / "tools" / "make_farim_from_swf.py"

OUTPUT_MODES = ["swf-source", "farim-only", "swf-and-farim"]
RUNTIME_PROFILES = ["timeline-only", "interactive-timeline", "avm1", "avm2"]
ASSET_KINDS = ["actor", "environment", "trigger", "audio", "video"]
PREFAB_ROLES = ["actor", "environment", "trigger"]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    slug = slug.strip("-")
    return slug or "dripwave-game"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_project_tree(project_name: str, output_mode: str, runtime_profile: str, game_prompt: str, code_prompt: str) -> dict[str, Path]:
    slug = slugify(project_name)
    project_root = PROJECTS_ROOT / slug
    paths = {
        "root": project_root,
        "src": project_root / "src",
        "assets": project_root / "assets",
        "visual": project_root / "assets" / "visual",
        "audio": project_root / "assets" / "audio",
        "video": project_root / "assets" / "video",
        "generated": project_root / "generated",
        "build": project_root / "build",
        "bin": project_root / "bin",
        "farim": project_root / "farim",
        "generation": project_root / "generation",
    }
    for path in paths.values():
        if path.suffix:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path.mkdir(parents=True, exist_ok=True)

    project_payload = {
        "name": project_name.strip() or slug,
        "slug": slug,
        "output_mode": output_mode,
        "runtime_profile": runtime_profile,
        "game_prompt": game_prompt.strip(),
        "code_prompt": code_prompt.strip(),
        "outputs": {
            "swf": f"bin/{slug}.swf",
            "farim": f"bin/{slug}.farim",
        },
        "generation": {
            "recraft_manifest": "generation/recraft_manifest.json",
            "audio_manifest": "generation/audio_manifest.json",
            "jumpclip_runs": "generation/jumpclip_runs.json",
        },
    }
    save_json(project_root / "project.json", project_payload)
    if not (project_root / "prefabs.json").exists():
        save_json(project_root / "prefabs.json", {"prefabs": []})
    if not (project_root / "generation" / "recraft_manifest.json").exists():
        save_json(project_root / "generation" / "recraft_manifest.json", {
            "manifest_name": f"{slug}-visual-assets",
            "manifest_version": 1,
            "output_root": "..",
            "assets": [],
        })
    if not (project_root / "generation" / "audio_manifest.json").exists():
        save_json(project_root / "generation" / "audio_manifest.json", {"assets": []})
    if not (project_root / "generation" / "jumpclip_runs.json").exists():
        save_json(project_root / "generation" / "jumpclip_runs.json", {"jobs": []})
    if not (project_root / "farim" / "farim_manifest.json").exists():
        save_json(project_root / "farim" / "farim_manifest.json", {
            "package_name": project_name.strip() or slug,
            "entry_swf": f"{slug}.swf",
            "runtime_profile": runtime_profile,
            "prefab_manifest": "../prefabs.json",
        })
    write_project_readme(paths, project_payload)
    write_build_scripts(paths, slug)
    if not (project_root / "src" / "Main.as").exists():
        (project_root / "src" / "Main.as").write_text(default_main_as(project_name, slug), encoding="utf-8")
    if not (project_root / "src" / "GameScript.as").exists():
        (project_root / "src" / "GameScript.as").write_text(default_game_script_as(project_name, game_prompt, code_prompt), encoding="utf-8")
    return paths


def default_main_as(project_name: str, slug: str) -> str:
    title = project_name.strip() or slug
    return textwrap.dedent(
        f"""
        package {{
            import flash.display.Sprite;
            import flash.events.Event;

            public class Main extends Sprite {{
                private var script:GameScript;

                public function Main() {{
                    script = new GameScript("{title}");
                    addEventListener(Event.ENTER_FRAME, onFrame);
                }}

                private function onFrame(event:Event):void {{
                    script.update();
                }}
            }}
        }}
        """
    ).strip() + "\n"


def default_game_script_as(project_name: str, game_prompt: str, code_prompt: str) -> str:
    summary = (code_prompt or game_prompt or f"{project_name} gameplay loop").replace("\n", " ").strip()
    return textwrap.dedent(
        f"""
        package {{
            public class GameScript {{
                private var title:String;
                private var tick:int = 0;

                public function GameScript(projectTitle:String) {{
                    title = projectTitle;
                }}

                public function update():void {{
                    tick += 1;
                    // Authoring summary: {summary}
                    // Replace or extend this method with translated gameplay logic.
                }}
            }}
        }}
        """
    ).strip() + "\n"


def write_project_readme(paths: dict[str, Path], project_payload: dict[str, Any]) -> None:
    readme = textwrap.dedent(
        f"""
        # {project_payload['name']}

        This project was scaffolded from dripwave authoring.

        Output mode: {project_payload['output_mode']}
        Runtime profile: {project_payload['runtime_profile']}

        Files:

        - `src/Main.as`: SWF entry point scaffold
        - `src/GameScript.as`: translated gameplay stub
        - `prefabs.json`: actor/environment/trigger prefab registry
        - `generation/recraft_manifest.json`: visual asset queue for Recraft
        - `generation/audio_manifest.json`: audio cue queue
        - `generation/jumpclip_runs.json`: sprite/video-style bundle queue
        - `farim/farim_manifest.json`: FARIM packaging manifest
        - `build/build_swf.ps1`: compile scaffold for Apache Flex / mxmlc if installed
        - `build/package_farim.ps1`: package built SWF into FARIM
        """
    ).strip() + "\n"
    (paths["root"] / "README.md").write_text(readme, encoding="utf-8")


def write_build_scripts(paths: dict[str, Path], slug: str) -> None:
    build_swf = textwrap.dedent(
        f"""
        $ErrorActionPreference = 'Stop'
        $projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
        $srcRoot = Join-Path $projectRoot 'src'
        $outDir = Join-Path $projectRoot 'bin'
        $mainClass = 'Main'
        New-Item -ItemType Directory -Force -Path $outDir | Out-Null

        if (-not (Get-Command mxmlc -ErrorAction SilentlyContinue)) {{
            throw 'mxmlc was not found. Install Apache Flex or point your PATH at an ActionScript compiler.'
        }}

        & mxmlc -source-path $srcRoot -output (Join-Path $outDir '{slug}.swf') (Join-Path $srcRoot "$mainClass.as")
        """
    ).strip() + "\n"
    package_farim = textwrap.dedent(
        f"""
        $ErrorActionPreference = 'Stop'
        $projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
        $swfPath = Join-Path $projectRoot 'bin\\{slug}.swf'
        if (-not (Test-Path $swfPath)) {{
            throw 'Build the SWF first.'
        }}
        & "$projectRoot\\..\\..\\tools\\make_farim_from_swf.py" $swfPath
        """
    ).strip() + "\n"
    (paths["build"] / "build_swf.ps1").write_text(build_swf, encoding="utf-8")
    (paths["build"] / "package_farim.ps1").write_text(package_farim, encoding="utf-8")


def append_prefab(project_root: Path, prefab: dict[str, Any]) -> None:
    prefab_path = project_root / "prefabs.json"
    payload = load_json(prefab_path, {"prefabs": []})
    prefabs = [item for item in payload.get("prefabs", []) if item.get("id") != prefab["id"]]
    prefabs.append(prefab)
    payload["prefabs"] = prefabs
    save_json(prefab_path, payload)


def queue_visual_asset(project_root: Path, prefab: dict[str, Any]) -> None:
    manifest_path = project_root / "generation" / "recraft_manifest.json"
    payload = load_json(manifest_path, {"assets": [], "output_root": ".."})
    assets = [item for item in payload.get("assets", []) if item.get("name") != prefab["id"]]
    target_subdir = "assets/video" if prefab["asset_kind"] == "video" else "assets/visual"
    assets.append({
        "name": prefab["id"],
        "prompt": prefab["prompt"],
        "negative_prompt": "text, watermark, logo, crop, blur, unreadable silhouette",
        "out": f"{target_subdir}/{prefab['id']}.png",
        "w": 1024,
        "h": 1024,
        "model": "recraftv4",
        "transparent_background": True,
    })
    payload["assets"] = assets
    save_json(manifest_path, payload)


def queue_audio_asset(project_root: Path, prefab: dict[str, Any]) -> None:
    manifest_path = project_root / "generation" / "audio_manifest.json"
    payload = load_json(manifest_path, {"assets": []})
    assets = [item for item in payload.get("assets", []) if item.get("name") != prefab["id"]]
    assets.append({
        "name": prefab["id"],
        "prompt": prefab["prompt"],
        "voice": "alloy",
        "out": f"assets/audio/{prefab['id']}.mp3",
    })
    payload["assets"] = assets
    save_json(manifest_path, payload)


def queue_jumpclip_job(project_root: Path, prefab: dict[str, Any]) -> None:
    manifest_path = project_root / "generation" / "jumpclip_runs.json"
    payload = load_json(manifest_path, {"jobs": []})
    jobs = [item for item in payload.get("jobs", []) if item.get("name") != prefab["id"]]
    jobs.append({
        "name": prefab["id"],
        "character": prefab["name"],
        "animation": "idle loop" if prefab["asset_kind"] == "video" else "run cycle",
        "prompt": prefab["prompt"],
        "out_dir": f"generated/jumpclip/{prefab['id']}",
    })
    payload["jobs"] = jobs
    save_json(manifest_path, payload)


def generate_prefab_code(prefab: dict[str, Any]) -> str:
    role = prefab["role"]
    class_name = "".join(part.capitalize() for part in prefab["id"].split("-")) + "Prefab"
    if role == "trigger":
        body = "public function activate():void {\n            // Trigger hook generated from plain-text authoring.\n        }"
    elif role == "environment":
        body = "public function decorate():void {\n            // Environment setup hook generated from plain-text authoring.\n        }"
    else:
        body = "public function update():void {\n            // Actor behavior hook generated from plain-text authoring.\n        }"
    return textwrap.dedent(
        f"""
        package prefabs {{
            public class {class_name} {{
                public var prefabId:String = \"{prefab['id']}\";
                public var prefabRole:String = \"{role}\";

                {body}
            }}
        }}
        """
    ).strip() + "\n"


def deterministic_code_translation(project_name: str, code_prompt: str, prefabs: list[dict[str, Any]]) -> str:
    lower = code_prompt.lower()
    behaviors: list[str] = []
    if "move" in lower or "movement" in lower:
        behaviors.append("applyPlayerMovement();")
    if "jump" in lower:
        behaviors.append("applyJumpArc();")
    if "trigger" in lower:
        behaviors.append("resolveTriggers();")
    if "enemy" in lower or "spawn" in lower:
        behaviors.append("updateSpawnQueues();")
    if "collision" in lower:
        behaviors.append("resolveCollisions();")
    if not behaviors:
        behaviors.append("advanceGameplayState();")
    prefab_lines = "\n".join(f'                // Prefab available: {prefab["name"]} ({prefab["role"]})' for prefab in prefabs) or "                // Add prefabs from the authoring shell."
    behavior_lines = "\n".join(f"                {line}" for line in behaviors)
    return textwrap.dedent(
        f"""
        package {{
            public class GameScript {{
                private var title:String;
                private var tick:int = 0;

                public function GameScript(projectTitle:String) {{
                    title = projectTitle;
                }}

                public function update():void {{
                    tick += 1;
{prefab_lines}
{behavior_lines}
                }}

                private function applyPlayerMovement():void {{}}
                private function applyJumpArc():void {{}}
                private function resolveTriggers():void {{}}
                private function updateSpawnQueues():void {{}}
                private function resolveCollisions():void {{}}
                private function advanceGameplayState():void {{}}
            }}
        }}
        """
    ).strip() + "\n"


def ai_code_translation(project_name: str, code_prompt: str, prefabs: list[dict[str, Any]]) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    prefab_summary = "\n".join(f"- {item['name']} :: role={item['role']} :: prompt={item['prompt']}" for item in prefabs) or "- no prefabs yet"
    completion = client.chat.completions.create(
        model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": "Write concise, valid ActionScript 3 gameplay code for a Flash game. Return only code.",
            },
            {
                "role": "user",
                "content": (
                    f"Project: {project_name}\n"
                    f"Gameplay prompt: {code_prompt}\n"
                    f"Available prefabs:\n{prefab_summary}\n"
                    "Create a single ActionScript 3 GameScript class with update logic and small helper methods."
                ),
            },
        ],
    )
    content = completion.choices[0].message.content or ""
    return content.strip() + "\n"


def translate_code(project_root: Path, project_name: str, code_prompt: str, use_ai: bool) -> str:
    prefabs = load_json(project_root / "prefabs.json", {"prefabs": []}).get("prefabs", [])
    if use_ai:
        code = ai_code_translation(project_name, code_prompt, prefabs)
    else:
        code = deterministic_code_translation(project_name, code_prompt, prefabs)
    (project_root / "src" / "GameScript.as").write_text(code, encoding="utf-8")
    return "Translated gameplay prompt into src/GameScript.as"


def run_command(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(command, cwd=str(WORKSPACE_ROOT), env=merged_env, capture_output=True, text=True)


def maybe_run_recraft(project_root: Path) -> str:
    manifest_path = project_root / "generation" / "recraft_manifest.json"
    if not RECRAFT_RUNNER.exists():
        return "Queued visual assets; Recraft runner not found in workspace."
    if not os.environ.get("RECRAFT_API_KEY"):
        return "Queued visual assets; RECRAFT_API_KEY is not set, so live generation was skipped."
    result = run_command([sys.executable, str(RECRAFT_RUNNER), str(manifest_path)])
    if result.returncode != 0:
        return f"Queued visual assets; Recraft run failed: {result.stderr.strip() or result.stdout.strip()}"
    return "Queued visual assets and executed the Recraft manifest."


def maybe_run_jumpclip(project_root: Path, prefab: dict[str, Any]) -> str:
    if not JUMPCLIP_SRC.exists() or not JUMPCLIP_PROFILE.exists() or not JUMPCLIP_PIPELINE.exists():
        return "Queued JumpClip bundle; JumpClip sources were not found."
    env = {"PYTHONPATH": str(JUMPCLIP_SRC) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    out_dir = project_root / "generated" / "jumpclip" / prefab["id"]
    command = [
        sys.executable,
        "-m",
        "jumpclip",
        "bundle",
        "--profile",
        str(JUMPCLIP_PROFILE),
        "--character",
        prefab["name"],
        "--animation",
        "idle loop" if prefab["asset_kind"] == "video" else "run cycle",
        "--prompt",
        prefab["prompt"],
        "--out-dir",
        str(out_dir),
        "--pipeline",
        str(JUMPCLIP_PIPELINE),
    ]
    result = run_command(command, env=env)
    if result.returncode != 0:
        return f"Queued JumpClip bundle; run failed: {result.stderr.strip() or result.stdout.strip()}"
    return f"Generated JumpClip bundle at {out_dir}"


def maybe_generate_audio(project_root: Path, prefab: dict[str, Any]) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        return "Queued audio cue; OPENAI_API_KEY is not set, so live audio generation was skipped."
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    output_path = project_root / "assets" / "audio" / f"{prefab['id']}.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with client.audio.speech.with_streaming_response.create(
        model=os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        voice=os.environ.get("OPENAI_TTS_VOICE", "alloy"),
        input=prefab["prompt"],
        format="mp3",
    ) as response:
        response.stream_to_file(output_path)
    return f"Generated audio cue at {output_path}"


def package_farim(project_root: Path, project_name: str) -> str:
    slug = slugify(project_name)
    swf_path = project_root / "bin" / f"{slug}.swf"
    if not swf_path.exists():
        return f"Cannot package FARIM yet; build {swf_path.name} first."
    result = run_command([sys.executable, str(FARIM_PACKER), str(swf_path)])
    if result.returncode != 0:
        return f"FARIM packaging failed: {result.stderr.strip() or result.stdout.strip()}"
    return f"Packaged FARIM from {swf_path.name}"


def run_headless(args: argparse.Namespace) -> int:
    paths = ensure_project_tree(
        args.project_name,
        args.output_mode,
        args.runtime_profile,
        args.game_prompt,
        args.code_prompt,
    )
    messages = [f"Project ready at {paths['root']}"]
    if args.prefab_name and args.prefab_prompt:
        prefab = {
            "id": slugify(args.prefab_name),
            "name": args.prefab_name,
            "role": args.prefab_role,
            "asset_kind": args.asset_kind,
            "prompt": args.prefab_prompt,
            "runtime_profile": args.runtime_profile,
            "generated_outputs": [],
        }
        append_prefab(paths["root"], prefab)
        (paths["src"] / "prefabs").mkdir(parents=True, exist_ok=True)
        (paths["src"] / "prefabs" / ("".join(part.capitalize() for part in prefab["id"].split("-")) + "Prefab.as")).write_text(generate_prefab_code(prefab), encoding="utf-8")
        messages.append(f"Added prefab {prefab['name']} ({prefab['role']}, {prefab['asset_kind']})")
        if prefab["asset_kind"] in {"actor", "environment", "trigger", "video"}:
            queue_visual_asset(paths["root"], prefab)
            messages.append("Queued Recraft visual asset")
            if args.run_recraft:
                messages.append(maybe_run_recraft(paths["root"]))
        if prefab["asset_kind"] in {"actor", "video"}:
            queue_jumpclip_job(paths["root"], prefab)
            messages.append("Queued JumpClip bundle")
            if args.run_jumpclip:
                messages.append(maybe_run_jumpclip(paths["root"], prefab))
        if prefab["asset_kind"] == "audio":
            queue_audio_asset(paths["root"], prefab)
            messages.append("Queued audio cue")
            if args.run_audio:
                try:
                    messages.append(maybe_generate_audio(paths["root"], prefab))
                except Exception as exc:  # noqa: BLE001
                    messages.append(f"Audio generation failed: {exc}")
    if args.translate_code:
        try:
            messages.append(translate_code(paths["root"], args.project_name, args.code_prompt, args.use_ai_translate))
        except Exception as exc:  # noqa: BLE001
            messages.append(f"AI translation failed, falling back: {exc}")
            messages.append(translate_code(paths["root"], args.project_name, args.code_prompt, False))
    if args.package_farim:
        messages.append(package_farim(paths["root"], args.project_name))
    print(json.dumps({"messages": messages, "project_root": str(paths["root"])}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="dripwave authoring shell and headless project generator")
    parser.add_argument("--headless", action="store_true", help="Run without opening the Tk UI")
    parser.add_argument("--project-name", default="New Dripwave Game")
    parser.add_argument("--output-mode", choices=OUTPUT_MODES, default=OUTPUT_MODES[2])
    parser.add_argument("--runtime-profile", choices=RUNTIME_PROFILES, default=RUNTIME_PROFILES[3])
    parser.add_argument("--game-prompt", default="Arcade action game with reusable prefabs and readable hazards.")
    parser.add_argument("--code-prompt", default="Player movement, trigger activation, collision checks, and spawn management.")
    parser.add_argument("--prefab-name", default="")
    parser.add_argument("--prefab-role", choices=PREFAB_ROLES, default=PREFAB_ROLES[0])
    parser.add_argument("--asset-kind", choices=ASSET_KINDS, default=ASSET_KINDS[0])
    parser.add_argument("--prefab-prompt", default="")
    parser.add_argument("--translate-code", action="store_true")
    parser.add_argument("--use-ai-translate", action="store_true")
    parser.add_argument("--run-recraft", action="store_true")
    parser.add_argument("--run-audio", action="store_true")
    parser.add_argument("--run-jumpclip", action="store_true")
    parser.add_argument("--package-farim", action="store_true")
    return parser


class AuthoringShell(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("dripwave authoring")
        self.geometry("980x760")
        self.project_name = tk.StringVar(value="New Dripwave Game")
        self.output_mode = tk.StringVar(value=OUTPUT_MODES[2])
        self.runtime_profile = tk.StringVar(value=RUNTIME_PROFILES[3])
        self.prefab_name = tk.StringVar(value="player_actor")
        self.asset_kind = tk.StringVar(value=ASSET_KINDS[0])
        self.prefab_role = tk.StringVar(value=PREFAB_ROLES[0])
        self.use_ai_translate = tk.BooleanVar(value=False)
        self.run_visual_generation = tk.BooleanVar(value=False)
        self.run_audio_generation = tk.BooleanVar(value=False)
        self.run_jumpclip_generation = tk.BooleanVar(value=True)
        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(1, weight=1)

        ttk.Label(root, text="Project Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(root, textvariable=self.project_name).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(root, text="Output Mode").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(root, textvariable=self.output_mode, values=OUTPUT_MODES, state="readonly").grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(root, text="Runtime Profile").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(root, textvariable=self.runtime_profile, values=RUNTIME_PROFILES, state="readonly").grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(root, text="Game Prompt").grid(row=3, column=0, sticky="nw", pady=(12, 0))
        self.game_prompt = tk.Text(root, height=7, wrap="word")
        self.game_prompt.grid(row=3, column=1, sticky="nsew", padx=(8, 0), pady=(12, 0))
        self.game_prompt.insert("1.0", "Arcade action game with reusable prefabs, readable hazards, and clean Flash runtime packaging.")

        ttk.Label(root, text="Code Prompt").grid(row=4, column=0, sticky="nw", pady=(12, 0))
        self.code_prompt = tk.Text(root, height=7, wrap="word")
        self.code_prompt.grid(row=4, column=1, sticky="nsew", padx=(8, 0), pady=(12, 0))
        self.code_prompt.insert("1.0", "Player movement, trigger activation, collision checks, and spawn management for a compact Flash game loop.")

        prefab_frame = ttk.LabelFrame(root, text="Prefab + Asset Queue", padding=10)
        prefab_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        prefab_frame.columnconfigure(1, weight=1)

        ttk.Label(prefab_frame, text="Prefab Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(prefab_frame, textvariable=self.prefab_name).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(prefab_frame, text="Asset Kind").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(prefab_frame, textvariable=self.asset_kind, values=ASSET_KINDS, state="readonly").grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(prefab_frame, text="Prefab Role").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(prefab_frame, textvariable=self.prefab_role, values=PREFAB_ROLES, state="readonly").grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        ttk.Label(prefab_frame, text="Prefab Prompt").grid(row=3, column=0, sticky="nw", pady=(8, 0))
        self.prefab_prompt = tk.Text(prefab_frame, height=6, wrap="word")
        self.prefab_prompt.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.prefab_prompt.insert("1.0", "Player actor with readable silhouette, collision-safe idle and run states, and trigger-ready interaction points.")

        options = ttk.Frame(root)
        options.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Checkbutton(options, text="Use AI for code translation when OPENAI_API_KEY is available", variable=self.use_ai_translate).pack(anchor="w")
        ttk.Checkbutton(options, text="Run Recraft after queuing visual assets", variable=self.run_visual_generation).pack(anchor="w")
        ttk.Checkbutton(options, text="Run OpenAI TTS after queuing audio assets", variable=self.run_audio_generation).pack(anchor="w")
        ttk.Checkbutton(options, text="Run JumpClip for actor/video bundle previews", variable=self.run_jumpclip_generation).pack(anchor="w")

        buttons = ttk.Frame(root)
        buttons.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Create Project", command=self.create_project).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Add Prefab", command=self.add_prefab).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(buttons, text="Translate Code", command=self.translate_code).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(buttons, text="Package FARIM", command=self.package_farim).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(root, text="Status").grid(row=8, column=0, sticky="nw", pady=(14, 0))
        self.status = tk.Text(root, height=14, wrap="word")
        self.status.grid(row=8, column=1, sticky="nsew", padx=(8, 0), pady=(14, 0))
        root.rowconfigure(8, weight=1)
        self.log("Ready. Create a project, then add prefabs and translate gameplay prompts into ActionScript scaffolding.")

    def log(self, message: str) -> None:
        self.status.insert(tk.END, message.strip() + "\n")
        self.status.see(tk.END)

    def current_project(self) -> tuple[dict[str, Path], str, str, str, str]:
        project_name = self.project_name.get().strip() or "New Dripwave Game"
        game_prompt = self.game_prompt.get("1.0", tk.END).strip()
        code_prompt = self.code_prompt.get("1.0", tk.END).strip()
        paths = ensure_project_tree(project_name, self.output_mode.get(), self.runtime_profile.get(), game_prompt, code_prompt)
        return paths, project_name, game_prompt, code_prompt, slugify(project_name)

    def create_project(self) -> None:
        paths, project_name, _, _, _ = self.current_project()
        self.log(f"Project ready at {paths['root']}")
        messagebox.showinfo("dripwave authoring", f"Project ready at\n{paths['root']}")

    def add_prefab(self) -> None:
        paths, project_name, _, _, _ = self.current_project()
        prefab_name = self.prefab_name.get().strip() or "prefab"
        prefab_prompt = self.prefab_prompt.get("1.0", tk.END).strip()
        prefab_id = slugify(prefab_name)
        prefab = {
            "id": prefab_id,
            "name": prefab_name,
            "role": self.prefab_role.get(),
            "asset_kind": self.asset_kind.get(),
            "prompt": prefab_prompt,
            "runtime_profile": self.runtime_profile.get(),
            "generated_outputs": [],
        }
        append_prefab(paths["root"], prefab)
        (paths["src"] / "prefabs").mkdir(parents=True, exist_ok=True)
        (paths["src"] / "prefabs" / ("".join(part.capitalize() for part in prefab_id.split("-")) + "Prefab.as")).write_text(generate_prefab_code(prefab), encoding="utf-8")

        if prefab["asset_kind"] in {"actor", "environment", "trigger", "video"}:
            queue_visual_asset(paths["root"], prefab)
            self.log("Queued visual asset in generation/recraft_manifest.json")
            if self.run_visual_generation.get():
                self.log(maybe_run_recraft(paths["root"]))
        if prefab["asset_kind"] in {"actor", "video"}:
            queue_jumpclip_job(paths["root"], prefab)
            self.log("Queued JumpClip bundle in generation/jumpclip_runs.json")
            if self.run_jumpclip_generation.get():
                self.log(maybe_run_jumpclip(paths["root"], prefab))
        if prefab["asset_kind"] == "audio":
            queue_audio_asset(paths["root"], prefab)
            self.log("Queued audio cue in generation/audio_manifest.json")
            if self.run_audio_generation.get():
                try:
                    self.log(maybe_generate_audio(paths["root"], prefab))
                except Exception as exc:  # noqa: BLE001
                    self.log(f"Audio generation failed: {exc}")

        self.log(f"Prefab added to {project_name}: {prefab_name} ({prefab['role']}, {prefab['asset_kind']})")

    def translate_code(self) -> None:
        paths, project_name, _, code_prompt, _ = self.current_project()
        try:
            self.log(translate_code(paths["root"], project_name, code_prompt, self.use_ai_translate.get()))
        except Exception as exc:  # noqa: BLE001
            self.log(f"AI translation failed, falling back to deterministic scaffold: {exc}")
            self.log(translate_code(paths["root"], project_name, code_prompt, False))

    def package_farim(self) -> None:
        paths, project_name, _, _, _ = self.current_project()
        self.log(package_farim(paths["root"], project_name))


def main() -> int:
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    parser = build_parser()
    args = parser.parse_args()
    if args.headless:
        return run_headless(args)
    app = AuthoringShell()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())