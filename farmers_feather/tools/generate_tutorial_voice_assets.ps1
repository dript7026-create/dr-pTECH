[CmdletBinding()]
param(
    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Speech

$projectRoot = Split-Path -Parent $PSScriptRoot
$voiceMapPath = Join-Path $projectRoot 'audio\tutorial_voice\character_voice_map.json'
$dialoguePath = Join-Path $projectRoot 'audio\tutorial_voice\dialogue_script.json'

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $projectRoot 'audio\generated\tutorial_voice'
}

$linesDir = Join-Path $OutputRoot 'lines'
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
New-Item -ItemType Directory -Force -Path $linesDir | Out-Null

$voiceMap = Get-Content $voiceMapPath -Raw | ConvertFrom-Json
$dialogue = Get-Content $dialoguePath -Raw | ConvertFrom-Json

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$installedVoices = @{}
foreach ($voice in $synth.GetInstalledVoices()) {
    $installedVoices[$voice.VoiceInfo.Name] = $voice.VoiceInfo
}

$profileIndex = @{}
foreach ($profile in $voiceMap.profiles) {
    if (-not $installedVoices.ContainsKey([string]$profile.voice)) {
        throw "Voice '$($profile.voice)' is not installed on this machine."
    }
    $profileIndex[[string]$profile.id] = $profile
}

$coverage = [System.Collections.Generic.List[string]]::new()
$coverage.Add('# Farmer''s Feather Tutorial Voice Coverage')
$coverage.Add('')
$coverage.Add("Generated: $((Get-Date).ToString('o'))")
$coverage.Add('')
$coverage.Add('Profiles:')
foreach ($profile in $voiceMap.profiles) {
    $coverage.Add("- $($profile.display_name) [$($profile.id)] -> $($profile.voice), rate $($profile.rate), volume $($profile.volume)")
}
$coverage.Add('')
$coverage.Add('Cues:')

$generatedManifest = [ordered]@{
    project = $dialogue.project
    generated_at = (Get-Date).ToString('o')
    output_root = $OutputRoot
    profiles = @()
    cues = @()
}

foreach ($profile in $voiceMap.profiles) {
    $generatedManifest.profiles += [ordered]@{
        id = $profile.id
        display_name = $profile.display_name
        role = $profile.role
        voice = $profile.voice
        rate = [int]$profile.rate
        volume = [int]$profile.volume
        objective_icon = $profile.objective_icon
        world_anchor = $profile.world_anchor
    }
}

$index = 0
foreach ($cue in $dialogue.cues) {
    $profile = $profileIndex[[string]$cue.speaker]
    $fileName = ('{0:D2}_{1}.wav' -f $index, [string]$cue.id)
    $filePath = Join-Path $linesDir $fileName

    $synth.SelectVoice([string]$profile.voice)
    $synth.Rate = [int]$profile.rate
    $synth.Volume = [int]$profile.volume
    $synth.SetOutputToWaveFile($filePath)
    $synth.Speak([string]$cue.text)
    $synth.SetOutputToNull()

    $generatedManifest.cues += [ordered]@{
        id = $cue.id
        stage = $cue.stage
        speaker = $cue.speaker
        prompt_icon = $cue.prompt_icon
        text = $cue.text
        file = $filePath
    }
    $coverage.Add("- $($cue.stage): $($profile.display_name) -> lines/$fileName")
    $index += 1
}

$generatedMapPath = Join-Path $OutputRoot 'character_voice_map.generated.json'
$manifestPath = Join-Path $OutputRoot 'generated_manifest.json'
$coveragePath = Join-Path $OutputRoot 'TUTORIAL_VOICE_COVERAGE.md'

$voiceMap | ConvertTo-Json -Depth 8 | Set-Content -Path $generatedMapPath -Encoding ASCII
$generatedManifest | ConvertTo-Json -Depth 8 | Set-Content -Path $manifestPath -Encoding ASCII
$coverage | Set-Content -Path $coveragePath -Encoding ASCII

$synth.Dispose()

Write-Output "Generated tutorial voice assets in $OutputRoot"