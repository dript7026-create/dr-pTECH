<#
.SYNOPSIS
  PowerShell wrapper for the `master` Python orchestrator.

.DESCRIPTION
  Allows convenient invocation from Windows. Defaults to dry-run; use
  `-Apply` to actually run installs.
#>

param(
    [switch]$Apply,
    [string]$Root = "drIpTECH",
    [string]$VenvPip = $null,
    [switch]$Quiet
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$python = (Get-Command python -ErrorAction SilentlyContinue).Path
if (-not $python) {
    $python = (Get-Command py -ErrorAction SilentlyContinue).Path
}
if (-not $python) {
    Write-Error "Python executable not found in PATH. Install Python 3 and add to PATH."
    exit 1
}

$args = @()
if ($Apply) { $args += '--apply' }
if ($VenvPip) { $args += '--venv-pip'; $args += "`"$VenvPip`"" }
if ($Quiet) { $args += '--quiet' }
$args += '--root'; $args += "`"$Root`""

& $python "$scriptDir\master" @args
