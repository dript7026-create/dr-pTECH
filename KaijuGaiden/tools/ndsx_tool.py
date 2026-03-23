import argparse
import hashlib
import json
import subprocess
import shutil
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path


FORMAT_NAME = "NDSX"
SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def first_existing_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_tool_candidates(tool_name: str, devkitpro: Path | None = None) -> list[Path]:
    workspace_root = resolve_workspace_root()
    candidates: list[Path] = []
    if devkitpro is not None:
        candidates.append(devkitpro / "tools" / "bin" / f"{tool_name}.exe")
    if tool_name == "makerom":
        candidates.append(workspace_root.parent / "makerom" / "makerom.exe")
        candidates.append(workspace_root.parent / "makerom.exe")
    elif tool_name == "bannertool":
        candidates.append(workspace_root.parent / "bannertool" / "windows-x86_64" / "bannertool.exe")
        candidates.append(workspace_root.parent / "bannertool" / "windows-i686" / "bannertool.exe")
        candidates.append(workspace_root.parent / "bannertool.exe")
    return candidates


def resolve_packaging_tools(devkitpro: Path | None = None) -> dict[str, Path | None]:
    return {
        "3dsxtool": first_existing_path(resolve_tool_candidates("3dsxtool", devkitpro)),
        "makerom": first_existing_path(resolve_tool_candidates("makerom", devkitpro)),
        "bannertool": first_existing_path(resolve_tool_candidates("bannertool", devkitpro)),
    }


def run_checked(command: list[str]) -> None:
    subprocess.run(command, check=True)


def build_file_metadata(path: Path) -> dict:
    return {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def ensure_runtime_artifacts(dist_dir: Path, build_3ds_dir: Path) -> dict[str, Path]:
    artifacts = {
        "3dsx": dist_dir / "kaijugaiden.3dsx",
        "smdh": dist_dir / "kaijugaiden.smdh",
    }
    fallbacks = {
        "3dsx": build_3ds_dir / "kaijugaiden.3dsx",
        "smdh": build_3ds_dir / "kaijugaiden.smdh",
    }
    for key, path in artifacts.items():
        if not path.exists() and fallbacks[key].exists():
            ensure_parent(path)
            shutil.copy2(fallbacks[key], path)
    return artifacts


def pack_ndsx(exe: Path, smdh: Path, profile_path: Path, out_path: Path, icon: Path | None = None) -> dict:
    ensure_parent(out_path)
    profile = load_json(profile_path)
    manifest = build_manifest(exe, smdh, profile, icon if icon and icon.exists() else None)

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ndsx/manifest.json", json.dumps(manifest, indent=2))
        archive.writestr("adaptive/profile.json", json.dumps(profile, indent=2))
        archive.writestr("docs/LAUNCH.txt", launch_text(manifest))
        archive.write(exe, "payload/kaijugaiden.3dsx")
        archive.write(smdh, "payload/kaijugaiden.smdh")
        if icon is not None and icon.exists():
            archive.write(icon, "payload/icon.png")

    return {
        "artifact": str(out_path),
        "size": out_path.stat().st_size,
        "manifest": manifest,
    }


def build_cia(
    makerom: Path,
    bannertool: Path,
    elf: Path,
    smdh: Path,
    rsf: Path,
    banner_image: Path,
    banner_audio: Path,
    banner_output: Path,
    cia_output: Path,
    target: str,
    desc: str,
) -> dict:
    ensure_parent(banner_output)
    ensure_parent(cia_output)

    run_checked([
        str(bannertool),
        "makebanner",
        "--image", str(banner_image),
        "--audio", str(banner_audio),
        "--output", str(banner_output),
    ])
    run_checked([
        str(makerom),
        "-f", "cia",
        "-o", str(cia_output),
        "-rsf", str(rsf),
        "-target", target,
        "-desc", desc,
        "-exefslogo",
        "-elf", str(elf),
        "-icon", str(smdh),
        "-banner", str(banner_output),
    ])
    return {
        "artifact": str(cia_output),
        "size": cia_output.stat().st_size,
        "makerom": str(makerom),
        "bannertool": str(bannertool),
        "banner": str(banner_output),
    }


def release_checksums_text(release_dir: Path) -> str:
    lines: list[str] = []
    for path in sorted(p for p in release_dir.iterdir() if p.is_file()):
        if path.name == "SHA256SUMS.txt":
            continue
        lines.append(f"{sha256_file(path)}  {path.name}")
    return "\n".join(lines) + "\n"


def build_release_manifest(release_dir: Path) -> dict:
    files = {
        path.name: build_file_metadata(path)
        for path in sorted(release_dir.iterdir())
        if path.is_file() and path.name not in {"release_manifest.json"}
    }
    return {
        "format": "KaijuGaiden3DSRelease",
        "generatedUtc": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def build_target_report(archive_path: Path, target_dir: Path, app_name: str, layout: str) -> dict:
    app_dir, resolved_layout = resolve_target_app_dir(target_dir, app_name, layout)
    homebrew_root = app_dir.parent if resolved_layout != "app-dir" else target_dir
    target_exists = target_dir.exists()
    archive_exists = archive_path.exists()
    has_nintendo_3ds = target_exists and (target_dir / "Nintendo 3DS").exists()
    has_homebrew_root = target_exists and (target_dir / "3ds").exists()
    warnings: list[str] = []

    if not archive_exists:
        warnings.append("Archive does not exist.")
    if not target_exists:
        warnings.append("Target path does not exist yet.")
    if resolved_layout == "sd-root" and target_exists and not (has_nintendo_3ds or has_homebrew_root):
        warnings.append("Target does not currently look like a mounted 3DS SD root.")
    if resolved_layout == "homebrew-root" and target_exists and target_dir.name.lower() != "3ds":
        warnings.append("Target path is not named '3ds'; verify you are pointing at the homebrew folder.")

    return {
        "archive": str(archive_path),
        "archiveExists": archive_exists,
        "targetInput": str(target_dir),
        "targetExists": target_exists,
        "requestedLayout": layout,
        "resolvedLayout": resolved_layout,
        "resolvedHomebrewRoot": str(homebrew_root),
        "resolvedAppDir": str(app_dir),
        "looksLike3dsSdRoot": bool(has_nintendo_3ds or has_homebrew_root),
        "hasNintendo3DSFolder": has_nintendo_3ds,
        "has3dsFolder": has_homebrew_root,
        "appDirExists": app_dir.exists(),
        "existingFiles": sorted(path.name for path in app_dir.iterdir()) if app_dir.exists() else [],
        "warnings": warnings,
        "readyForDeploy": archive_exists and target_exists,
    }


def resolve_target_app_dir(target_dir: Path, app_name: str, layout: str) -> tuple[Path, str]:
    normalized = layout.lower()
    if normalized == "auto":
        if target_dir.name.lower() == "3ds":
            normalized = "homebrew-root"
        elif (target_dir / "3ds").exists() or (target_dir / "Nintendo 3DS").exists():
            normalized = "sd-root"
        else:
            normalized = "homebrew-root"

    if normalized == "sd-root":
        homebrew_root = target_dir / "3ds"
        return homebrew_root / app_name, normalized
    if normalized == "homebrew-root":
        return target_dir / app_name, normalized
    if normalized == "app-dir":
        return target_dir, normalized
    raise ValueError(f"Unsupported target layout: {layout}")


def build_manifest(exe: Path, smdh: Path, profile: dict, icon: Path | None) -> dict:
    payloads = {
        "executable": {
            "path": "payload/kaijugaiden.3dsx",
            "source": str(exe),
            "size": exe.stat().st_size,
            "sha256": sha256_file(exe),
            "launch_role": "primary-3ds-homebrew",
        },
        "metadata": {
            "path": "payload/kaijugaiden.smdh",
            "source": str(smdh),
            "size": smdh.stat().st_size,
            "sha256": sha256_file(smdh),
            "launch_role": "homebrew-metadata",
        },
    }
    if icon is not None:
        payloads["icon"] = {
            "path": "payload/icon.png",
            "source": str(icon),
            "size": icon.stat().st_size,
            "sha256": sha256_file(icon),
            "launch_role": "branding",
        }
    return {
        "format": FORMAT_NAME,
        "schemaVersion": SCHEMA_VERSION,
        "title": profile["title"],
        "wrapperId": profile["wrapperId"],
        "version": profile["version"],
        "createdUtc": datetime.now(timezone.utc).isoformat(),
        "directLaunch": {
            "supportedBy3DS": False,
            "embeddedLaunchTarget": "payload/kaijugaiden.3dsx",
            "requiredRuntime": "Nintendo 3DS Homebrew Launcher",
            "note": "NDSX is a self-contained distribution wrapper embedding the runnable 3DSX build and adaptive stereo profile.",
        },
        "adaptiveStereo3D": profile["adaptiveStereo3D"],
        "embeddedPayloads": payloads,
        "releaseBundle": profile["releaseBundle"],
    }


def launch_text(manifest: dict) -> str:
    stereo = manifest["adaptiveStereo3D"]
    presets = stereo.get("calibrationPresets", [])
    preset_labels = ", ".join(preset["name"] for preset in presets) if presets else "none"
    return textwrap.dedent(
        f"""\
        Kaiju Gaiden NDSX Release
        ========================

        This .ndsx file is a self-contained distribution wrapper for the embedded 3DS build.

        Runnable payload:
        - payload/kaijugaiden.3dsx

        Adaptive stereo profile:
        - adaptive/profile.json

        Launch notes:
        - Copy payload/kaijugaiden.3dsx and payload/kaijugaiden.smdh to your 3DS homebrew location.
        - The embedded build already contains the adaptive stereo comfort runtime.
        - Wrapper defaults: comfort={stereo['comfortDefault']}, mono={stereo['forceFlatDefault']}, smoothing={stereo['smoothingDefault']}.
        - Calibration presets: {preset_labels}.
        - In-game 3DS options overlay: press L.
        """
    )


def cmd_pack(args: argparse.Namespace) -> int:
    exe = Path(args.exe).resolve()
    smdh = Path(args.smdh).resolve()
    profile_path = Path(args.profile).resolve()
    icon = Path(args.icon).resolve() if args.icon else None
    out_path = Path(args.out).resolve()
    print(json.dumps(pack_ndsx(exe, smdh, profile_path, out_path, icon), indent=2))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    path = Path(args.archive).resolve()
    with zipfile.ZipFile(path, "r") as archive:
        manifest = json.loads(archive.read("ndsx/manifest.json").decode("utf-8"))
    print(json.dumps(manifest, indent=2))
    return 0


def cmd_unpack(args: argparse.Namespace) -> int:
    archive_path = Path(args.archive).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        archive.extractall(out_dir)
    print(json.dumps({"archive": str(archive_path), "outDir": str(out_dir)}, indent=2))
    return 0


def cmd_verify_target(args: argparse.Namespace) -> int:
    archive_path = Path(args.archive).resolve()
    target_dir = Path(args.target_dir).resolve()
    report = build_target_report(archive_path, target_dir, args.app_name, args.target_layout)
    print(json.dumps(report, indent=2))
    return 0 if report["readyForDeploy"] else 1


def cmd_deploy(args: argparse.Namespace) -> int:
    archive_path = Path(args.archive).resolve()
    target_dir = Path(args.target_dir).resolve()
    if args.verify_first:
        report = build_target_report(archive_path, target_dir, args.app_name, args.target_layout)
        if not report["readyForDeploy"]:
            print(json.dumps(report, indent=2))
            return 1
    app_dir, resolved_layout = resolve_target_app_dir(target_dir, args.app_name, args.target_layout)
    app_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        exe_bytes = archive.read("payload/kaijugaiden.3dsx")
        smdh_bytes = archive.read("payload/kaijugaiden.smdh")
        profile_bytes = archive.read("adaptive/profile.json")
    (app_dir / "kaijugaiden.3dsx").write_bytes(exe_bytes)
    (app_dir / "kaijugaiden.smdh").write_bytes(smdh_bytes)
    (app_dir / "ndsx_profile.json").write_bytes(profile_bytes)
    launch_path = app_dir / "LAUNCH_FROM_NDSX.txt"
    launch_path.write_text(
        textwrap.dedent(
            """\
            This folder was deployed from a Kaiju Gaiden NDSX wrapper.

            Files copied here:
            - kaijugaiden.3dsx
            - kaijugaiden.smdh
            - ndsx_profile.json

            Launch from your 3DS Homebrew Launcher as the standard 3DSX payload.
            The adaptive stereo defaults are recorded in ndsx_profile.json.
            """
        ),
        encoding="utf-8",
    )
    print(json.dumps({
        "archive": str(archive_path),
        "targetInput": str(target_dir),
        "targetLayout": resolved_layout,
        "deployedTo": str(app_dir),
        "files": sorted(path.name for path in app_dir.iterdir()),
    }, indent=2))
    return 0


def release_readme_text() -> str:
    return textwrap.dedent(
        """\
        Kaiju Gaiden 3DS Release Bundle
        ===============================

        Files in this bundle:
        - kaijugaiden.3dsx: runnable 3DS homebrew executable
        - kaijugaiden.smdh: 3DS homebrew metadata/icon bundle
        - kaijugaiden.ndsx: self-contained distribution wrapper embedding the live 3DSX build
        - kaijugaiden.cia: installable 3DS title, if the CIA packaging toolchain was available when the release was built

        How to run:
        1. Place kaijugaiden.3dsx and kaijugaiden.smdh where your 3DS homebrew setup expects them.
        2. Launch the app from the Homebrew Launcher.
        3. Or install kaijugaiden.cia with FBI for a HOME Menu title.
        4. Press L in-game for the adaptive stereo options overlay.
        5. Or deploy directly from the wrapper with the included PowerShell helper.

        Helper examples:
        - Verify a card first: .\\verify_3ds_sd_layout.ps1 -TargetPath E:\\
        - SD root path: .\\deploy_ndsx_to_3ds_sd.ps1 -TargetPath E:\\
        - Existing 3ds folder: .\\deploy_ndsx_to_3ds_sd.ps1 -TargetPath E:\\3ds
        - Auto-detect a single likely 3DS SD card: .\\deploy_ndsx_to_3ds_sd.ps1 -AutoDetect
        - Stage the CIA for FBI install: .\\install_kaijugaiden_cia_to_3ds_sd.ps1 -TargetPath E:\\

        NDSX note:
        - The .ndsx file is a wrapper/container for release and policy distribution.
        - The embedded .3dsx inside it remains the directly runnable 3DS payload.

        Quality-of-life files:
        - SHA256SUMS.txt: checksums for each release artifact
        - release_manifest.json: machine-readable release inventory
        """
    )


def release_cia_stage_script_text() -> str:
    return textwrap.dedent(
        """\
        param(
            [string]$TargetPath,
            [switch]$AutoDetect
        )

        function Get-3dsSdCandidates {
            Get-PSDrive -PSProvider FileSystem | ForEach-Object {
                $rootPath = $_.Root
                $hasNintendoFolder = Test-Path (Join-Path $rootPath 'Nintendo 3DS')
                $hasHomebrewFolder = Test-Path (Join-Path $rootPath '3ds')
                if ($hasNintendoFolder -or $hasHomebrewFolder) {
                    [PSCustomObject]@{
                        Name = $_.Name
                        Root = $rootPath
                        HasNintendo3DS = $hasNintendoFolder
                        HasHomebrew3ds = $hasHomebrewFolder
                    }
                }
            }
        }

        $root = Split-Path -Parent $MyInvocation.MyCommand.Path
        $cia = Join-Path $root 'kaijugaiden.cia'
        if (-not (Test-Path $cia)) {
            throw 'kaijugaiden.cia is not present in this release bundle.'
        }

        if (-not $TargetPath -and $AutoDetect) {
            $candidates = @(Get-3dsSdCandidates)
            if ($candidates.Count -eq 1) {
                $TargetPath = $candidates[0].Root
            } elseif ($candidates.Count -gt 1) {
                Write-Host 'Multiple 3DS SD card candidates found:'
                $candidates | Format-Table -AutoSize | Out-Host
                throw 'Pass -TargetPath explicitly.'
            } else {
                throw 'No SD card candidates found. Insert the card or pass -TargetPath explicitly.'
            }
        }

        if (-not $TargetPath) {
            throw 'Provide -TargetPath (SD root) or use -AutoDetect.'
        }

        $ciaDir = Join-Path $TargetPath 'cias'
        New-Item -ItemType Directory -Force -Path $ciaDir | Out-Null
        Copy-Item $cia (Join-Path $ciaDir 'kaijugaiden.cia') -Force
        Write-Host "Staged kaijugaiden.cia to $ciaDir"
        """
    )


def release_deploy_script_text() -> str:
    return textwrap.dedent(
        """\
        param(
            [string]$TargetPath,
            [switch]$AutoDetect,
            [switch]$SkipVerify
        )

        function Get-3dsSdCandidates {
            Get-PSDrive -PSProvider FileSystem | ForEach-Object {
                $rootPath = $_.Root
                $hasNintendoFolder = Test-Path (Join-Path $rootPath 'Nintendo 3DS')
                $hasHomebrewFolder = Test-Path (Join-Path $rootPath '3ds')
                if ($hasNintendoFolder -or $hasHomebrewFolder) {
                    [PSCustomObject]@{
                        Name = $_.Name
                        Root = $rootPath
                        HasNintendo3DS = $hasNintendoFolder
                        HasHomebrew3ds = $hasHomebrewFolder
                    }
                }
            }
        }

        $root = Split-Path -Parent $MyInvocation.MyCommand.Path
        $repo = Split-Path -Parent (Split-Path -Parent $root)
        $archive = Join-Path $root 'kaijugaiden.ndsx'
        $pythonCandidates = @(
            (Join-Path $repo 'venv\\Scripts\\python.exe'),
            (Join-Path $repo '.venv\\Scripts\\python.exe')
        )
        $python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

        if (-not $python) {
            $python = 'py'
        }

        if (-not $TargetPath -and $AutoDetect) {
            $candidates = @(Get-3dsSdCandidates)
            if ($candidates.Count -eq 1) {
                $TargetPath = $candidates[0].Root
            } elseif ($candidates.Count -gt 1) {
                Write-Host 'Multiple 3DS SD card candidates found:'
                $candidates | Format-Table -AutoSize | Out-Host
                throw 'Pass -TargetPath explicitly.'
            } else {
                throw 'No SD card candidates found. Insert the card or pass -TargetPath explicitly.'
            }
        }

        if (-not $TargetPath) {
            throw 'Provide -TargetPath (SD root, 3ds folder, or app directory) or use -AutoDetect.'
        }

        if (-not $SkipVerify) {
            if ($python -eq 'py') {
                & $python -3 (Join-Path $repo 'tools\\ndsx_tool.py') verify-target --archive $archive --target-dir $TargetPath --target-layout auto --app-name 'kaijugaiden'
            } else {
                & $python (Join-Path $repo 'tools\\ndsx_tool.py') verify-target --archive $archive --target-dir $TargetPath --target-layout auto --app-name 'kaijugaiden'
            }
            if ($LASTEXITCODE -ne 0) {
                throw 'Target verification failed. Fix the SD path or pass -SkipVerify if you intend to create the target manually.'
            }
        }

        if ($python -eq 'py') {
            & $python -3 (Join-Path $repo 'tools\\ndsx_tool.py') deploy --archive $archive --target-dir $TargetPath --target-layout auto --app-name 'kaijugaiden' --verify-first
        } else {
            & $python (Join-Path $repo 'tools\\ndsx_tool.py') deploy --archive $archive --target-dir $TargetPath --target-layout auto --app-name 'kaijugaiden' --verify-first
        }
        """
    )


def release_verify_script_text() -> str:
    return textwrap.dedent(
        """\
        param(
            [string]$TargetPath,
            [switch]$AutoDetect
        )

        function Get-3dsSdCandidates {
            Get-PSDrive -PSProvider FileSystem | ForEach-Object {
                $rootPath = $_.Root
                $hasNintendoFolder = Test-Path (Join-Path $rootPath 'Nintendo 3DS')
                $hasHomebrewFolder = Test-Path (Join-Path $rootPath '3ds')
                if ($hasNintendoFolder -or $hasHomebrewFolder) {
                    [PSCustomObject]@{
                        Name = $_.Name
                        Root = $rootPath
                        HasNintendo3DS = $hasNintendoFolder
                        HasHomebrew3ds = $hasHomebrewFolder
                    }
                }
            }
        }

        $root = Split-Path -Parent $MyInvocation.MyCommand.Path
        $repo = Split-Path -Parent (Split-Path -Parent $root)
        $archive = Join-Path $root 'kaijugaiden.ndsx'
        $pythonCandidates = @(
            (Join-Path $repo 'venv\\Scripts\\python.exe'),
            (Join-Path $repo '.venv\\Scripts\\python.exe')
        )
        $python = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

        if (-not $python) {
            $python = 'py'
        }

        if (-not $TargetPath -and $AutoDetect) {
            $candidates = @(Get-3dsSdCandidates)
            if ($candidates.Count -eq 1) {
                $TargetPath = $candidates[0].Root
            } elseif ($candidates.Count -gt 1) {
                Write-Host 'Multiple 3DS SD card candidates found:'
                $candidates | Format-Table -AutoSize | Out-Host
                throw 'Pass -TargetPath explicitly.'
            } else {
                throw 'No SD card candidates found. Insert the card or pass -TargetPath explicitly.'
            }
        }

        if (-not $TargetPath) {
            throw 'Provide -TargetPath (SD root, 3ds folder, or app directory) or use -AutoDetect.'
        }

        if ($python -eq 'py') {
            & $python -3 (Join-Path $repo 'tools\\ndsx_tool.py') verify-target --archive $archive --target-dir $TargetPath --target-layout auto --app-name 'kaijugaiden'
        } else {
            & $python (Join-Path $repo 'tools\\ndsx_tool.py') verify-target --archive $archive --target-dir $TargetPath --target-layout auto --app-name 'kaijugaiden'
        }
        """
    )


def cmd_release(args: argparse.Namespace) -> int:
    dist_dir = Path(args.dist_dir).resolve()
    release_dir = Path(args.out_dir).resolve()
    release_dir.mkdir(parents=True, exist_ok=True)
    copies = ["kaijugaiden.3dsx", "kaijugaiden.smdh", "kaijugaiden.ndsx"]
    optional_copies = ["kaijugaiden.cia"]
    for name in copies:
        shutil.copy2(dist_dir / name, release_dir / name)
    for name in optional_copies:
        source = dist_dir / name
        if source.exists():
            shutil.copy2(source, release_dir / name)
    (release_dir / "README_3DS_RELEASE.txt").write_text(release_readme_text(), encoding="utf-8")
    (release_dir / "deploy_ndsx_to_3ds_sd.ps1").write_text(release_deploy_script_text(), encoding="utf-8")
    (release_dir / "install_kaijugaiden_cia_to_3ds_sd.ps1").write_text(release_cia_stage_script_text(), encoding="utf-8")
    (release_dir / "verify_3ds_sd_layout.ps1").write_text(release_verify_script_text(), encoding="utf-8")
    (release_dir / "SHA256SUMS.txt").write_text(release_checksums_text(release_dir), encoding="utf-8")
    (release_dir / "release_manifest.json").write_text(json.dumps(build_release_manifest(release_dir), indent=2), encoding="utf-8")
    print(json.dumps({
        "releaseDir": str(release_dir),
        "files": sorted(path.name for path in release_dir.iterdir()),
    }, indent=2))
    return 0


def cmd_cia_tools(args: argparse.Namespace) -> int:
    root = Path(args.devkitpro).resolve()
    tools = resolve_packaging_tools(root)
    result = {
        "devkitPro": str(root),
        "tools": {
            name: {"path": str(path) if path is not None else None, "present": path is not None}
            for name, path in tools.items()
        },
        "ciaReady": all(tools[name] is not None for name in ("makerom", "bannertool")),
        "note": "CIA packaging requires makerom and bannertool in addition to the existing 3DSX toolchain. Local parent-directory tool folders are checked before reporting unavailable.",
    }
    print(json.dumps(result, indent=2))
    return 0


def cmd_cia_build(args: argparse.Namespace) -> int:
    workspace_root = resolve_workspace_root()
    devkitpro = Path(args.devkitpro).resolve() if args.devkitpro else None
    tools = resolve_packaging_tools(devkitpro)
    makerom = Path(args.makerom).resolve() if args.makerom else tools["makerom"]
    bannertool = Path(args.bannertool).resolve() if args.bannertool else tools["bannertool"]
    elf = Path(args.elf).resolve() if args.elf else workspace_root / "3ds" / "kaijugaiden.elf"
    smdh = Path(args.smdh).resolve() if args.smdh else workspace_root / "3ds" / "kaijugaiden.smdh"
    rsf = Path(args.rsf).resolve() if args.rsf else workspace_root / "3ds" / "kaijugaiden.rsf"
    banner_image = Path(args.banner_image).resolve() if args.banner_image else workspace_root / "3ds" / "banner.png"
    banner_audio = Path(args.banner_audio).resolve() if args.banner_audio else workspace_root / "3ds" / "banner.wav"
    banner_output = Path(args.banner_output).resolve() if args.banner_output else workspace_root / "dist" / "kaijugaiden.bnr"
    cia_output = Path(args.out).resolve() if args.out else workspace_root / "dist" / "kaijugaiden.cia"

    if makerom is None or not makerom.exists():
        raise FileNotFoundError("makerom.exe not found. Pass --makerom or place it in devkitPro/tools/bin or ../makerom/.")
    if bannertool is None or not bannertool.exists():
        raise FileNotFoundError("bannertool.exe not found. Pass --bannertool or place it in devkitPro/tools/bin or ../bannertool/.")

    required_paths = {
        "elf": elf,
        "smdh": smdh,
        "rsf": rsf,
        "bannerImage": banner_image,
        "bannerAudio": banner_audio,
    }
    missing = {name: str(path) for name, path in required_paths.items() if not path.exists()}
    if missing:
        print(json.dumps({"missingInputs": missing}, indent=2))
        return 1

    print(json.dumps(build_cia(
        makerom,
        bannertool,
        elf,
        smdh,
        rsf,
        banner_image,
        banner_audio,
        banner_output,
        cia_output,
        args.target,
        args.desc,
    ), indent=2))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    workspace_root = resolve_workspace_root()
    dist_dir = Path(args.dist_dir).resolve() if args.dist_dir else workspace_root / "dist"
    build_3ds_dir = Path(args.build_3ds_dir).resolve() if args.build_3ds_dir else workspace_root / "3ds"
    devkitpro = Path(args.devkitpro).resolve() if args.devkitpro else None
    tools = resolve_packaging_tools(devkitpro)
    files = {
        "dist3dsx": dist_dir / "kaijugaiden.3dsx",
        "distSmdh": dist_dir / "kaijugaiden.smdh",
        "distNdsx": dist_dir / "kaijugaiden.ndsx",
        "distCia": dist_dir / "kaijugaiden.cia",
        "elf": build_3ds_dir / "kaijugaiden.elf",
        "rsf": build_3ds_dir / "kaijugaiden.rsf",
        "profile": build_3ds_dir / "ndsx_adaptive_profile.json",
        "icon": build_3ds_dir / "icon.png",
        "bannerImage": build_3ds_dir / "banner.png",
        "bannerAudio": build_3ds_dir / "banner.wav",
    }
    result = {
        "workspaceRoot": str(workspace_root),
        "distDir": str(dist_dir),
        "build3dsDir": str(build_3ds_dir),
        "tools": {
            name: {"path": str(path) if path is not None else None, "present": path is not None}
            for name, path in tools.items()
        },
        "files": {
            name: {
                "path": str(path),
                "present": path.exists(),
                **({"size": path.stat().st_size} if path.exists() and path.is_file() else {}),
            }
            for name, path in files.items()
        },
        "ready": {
            "canPackNdsx": all(files[name].exists() for name in ("dist3dsx", "distSmdh", "profile")),
            "canBuildCia": all(files[name].exists() for name in ("elf", "distSmdh", "rsf", "bannerImage", "bannerAudio")) and all(tools[name] is not None for name in ("makerom", "bannertool")),
            "canMakeReleaseBundle": all(files[name].exists() for name in ("dist3dsx", "distSmdh", "distNdsx")),
        },
    }
    print(json.dumps(result, indent=2))
    return 0


def cmd_build_release(args: argparse.Namespace) -> int:
    workspace_root = resolve_workspace_root()
    dist_dir = Path(args.dist_dir).resolve() if args.dist_dir else workspace_root / "dist"
    build_3ds_dir = Path(args.build_3ds_dir).resolve() if args.build_3ds_dir else workspace_root / "3ds"
    release_dir = Path(args.out_dir).resolve() if args.out_dir else dist_dir / "kaijugaiden_3ds_release"
    profile = Path(args.profile).resolve() if args.profile else build_3ds_dir / "ndsx_adaptive_profile.json"
    icon = Path(args.icon).resolve() if args.icon else build_3ds_dir / "icon.png"
    ndsx_out = dist_dir / "kaijugaiden.ndsx"
    artifacts = ensure_runtime_artifacts(dist_dir, build_3ds_dir)
    results: dict[str, object] = {
        "runtimeArtifacts": {key: str(path) for key, path in artifacts.items()},
    }

    missing = {name: str(path) for name, path in {"3dsx": artifacts["3dsx"], "smdh": artifacts["smdh"], "profile": profile}.items() if not path.exists()}
    if missing:
        print(json.dumps({"missingInputs": missing}, indent=2))
        return 1

    results["ndsx"] = pack_ndsx(artifacts["3dsx"], artifacts["smdh"], profile, ndsx_out, icon if icon.exists() else None)

    if not args.skip_cia:
        cia_args = argparse.Namespace(
            devkitpro=args.devkitpro,
            makerom=args.makerom,
            bannertool=args.bannertool,
            elf=str(build_3ds_dir / "kaijugaiden.elf"),
            smdh=str(artifacts["smdh"]),
            rsf=str(build_3ds_dir / "kaijugaiden.rsf"),
            banner_image=str(build_3ds_dir / "banner.png"),
            banner_audio=str(build_3ds_dir / "banner.wav"),
            banner_output=str(dist_dir / "kaijugaiden.bnr"),
            out=str(dist_dir / "kaijugaiden.cia"),
            target=args.target,
            desc=args.desc,
        )
        cia_result = cmd_cia_build(cia_args)
        if cia_result != 0 and args.require_cia:
            return cia_result
        results["ciaBuilt"] = cia_result == 0
    else:
        results["ciaBuilt"] = False

    release_result = cmd_release(argparse.Namespace(dist_dir=str(dist_dir), out_dir=str(release_dir)))
    if release_result != 0:
        return release_result
    results["releaseDir"] = str(release_dir)
    print(json.dumps(results, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NDSX wrapper and 3DS release tooling for KaijuGaiden")
    subparsers = parser.add_subparsers(dest="command", required=True)

    pack = subparsers.add_parser("pack", help="Build a .ndsx wrapper around the live 3DSX payload")
    pack.add_argument("--exe", required=True)
    pack.add_argument("--smdh", required=True)
    pack.add_argument("--profile", required=True)
    pack.add_argument("--out", required=True)
    pack.add_argument("--icon")
    pack.set_defaults(func=cmd_pack)

    inspect_cmd = subparsers.add_parser("inspect", help="Read the manifest from a .ndsx archive")
    inspect_cmd.add_argument("archive")
    inspect_cmd.set_defaults(func=cmd_inspect)

    unpack = subparsers.add_parser("unpack", help="Extract a .ndsx archive")
    unpack.add_argument("archive")
    unpack.add_argument("out_dir")
    unpack.set_defaults(func=cmd_unpack)

    deploy = subparsers.add_parser("deploy", help="Deploy the runnable payload from a .ndsx archive into a target 3DS homebrew directory")
    deploy.add_argument("--archive", required=True)
    deploy.add_argument("--target-dir", required=True)
    deploy.add_argument("--target-layout", choices=["auto", "sd-root", "homebrew-root", "app-dir"], default="auto")
    deploy.add_argument("--app-name", default="kaijugaiden")
    deploy.add_argument("--verify-first", action="store_true")
    deploy.set_defaults(func=cmd_deploy)

    verify = subparsers.add_parser("verify-target", help="Check whether a target path looks ready for NDSX deployment")
    verify.add_argument("--archive", required=True)
    verify.add_argument("--target-dir", required=True)
    verify.add_argument("--target-layout", choices=["auto", "sd-root", "homebrew-root", "app-dir"], default="auto")
    verify.add_argument("--app-name", default="kaijugaiden")
    verify.set_defaults(func=cmd_verify_target)

    release = subparsers.add_parser("release", help="Build a user-facing 3DS release folder")
    release.add_argument("--dist-dir", required=True)
    release.add_argument("--out-dir", required=True)
    release.set_defaults(func=cmd_release)

    doctor = subparsers.add_parser("doctor", help="Report NDSX/CIA tool readiness, required assets, and release-build status")
    doctor.add_argument("--devkitpro", default="C:/devkitPro")
    doctor.add_argument("--dist-dir")
    doctor.add_argument("--build-3ds-dir")
    doctor.set_defaults(func=cmd_doctor)

    build_release = subparsers.add_parser("build-release", help="Pack NDSX, optionally build CIA, and assemble the end-user release bundle")
    build_release.add_argument("--devkitpro", default="C:/devkitPro")
    build_release.add_argument("--dist-dir")
    build_release.add_argument("--build-3ds-dir")
    build_release.add_argument("--out-dir")
    build_release.add_argument("--profile")
    build_release.add_argument("--icon")
    build_release.add_argument("--makerom")
    build_release.add_argument("--bannertool")
    build_release.add_argument("--skip-cia", action="store_true")
    build_release.add_argument("--require-cia", action="store_true")
    build_release.add_argument("--target", default="t")
    build_release.add_argument("--desc", default="app:4")
    build_release.set_defaults(func=cmd_build_release)

    cia_build = subparsers.add_parser("cia-build", help="Build an installable .cia from the current 3DS ELF and banner assets")
    cia_build.add_argument("--devkitpro", default="C:/devkitPro")
    cia_build.add_argument("--makerom")
    cia_build.add_argument("--bannertool")
    cia_build.add_argument("--elf")
    cia_build.add_argument("--smdh")
    cia_build.add_argument("--rsf")
    cia_build.add_argument("--banner-image")
    cia_build.add_argument("--banner-audio")
    cia_build.add_argument("--banner-output")
    cia_build.add_argument("--out")
    cia_build.add_argument("--target", default="t")
    cia_build.add_argument("--desc", default="app:4")
    cia_build.set_defaults(func=cmd_cia_build)

    cia = subparsers.add_parser("cia-tools", help="Check local 3DS CIA packaging tool availability")
    cia.add_argument("--devkitpro", default="C:/devkitPro")
    cia.set_defaults(func=cmd_cia_tools)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())