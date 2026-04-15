$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$required = @('gcc', 'windres', 'cmake')
$optional = @('cl', 'clang', 'ninja', 'rc', 'msbuild', 'devenv', 'lld-link', 'gdb')

Write-Host '== dotxt toolchain audit ==' -ForegroundColor Cyan
Write-Host "repo root: $root"
Write-Host ''

foreach ($tool in $required) {
    $cmd = Get-Command $tool -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host ("REQUIRED OK   {0} -> {1}" -f $tool, $cmd.Source) -ForegroundColor Green
    } else {
        Write-Host ("REQUIRED MISS {0}" -f $tool) -ForegroundColor Red
    }
}

Write-Host ''
foreach ($tool in $optional) {
    $cmd = Get-Command $tool -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host ("OPTIONAL OK   {0} -> {1}" -f $tool, $cmd.Source) -ForegroundColor Green
    } else {
        Write-Host ("OPTIONAL MISS {0}" -f $tool) -ForegroundColor Yellow
    }
}

Write-Host ''
$winsdkBase = 'C:\Program Files (x86)\Windows Kits\10\Include'
if (Test-Path $winsdkBase) {
    $sdk = Get-ChildItem $winsdkBase -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if ($sdk) {
        $windowsHeader = Join-Path $sdk.FullName 'um\windows.h'
        if (Test-Path $windowsHeader) {
            Write-Host ("WINDOWS SDK OK -> {0}" -f $windowsHeader) -ForegroundColor Green
        } else {
            Write-Host 'WINDOWS SDK MISS windows.h in latest detected SDK' -ForegroundColor Red
        }
    }
} else {
    Write-Host 'WINDOWS SDK MISS include base not found' -ForegroundColor Red
}

Write-Host ''
Write-Host '== configure/build smoke test ==' -ForegroundColor Cyan
cmake -S . -B build | Out-Host
cmake --build build --config Release | Out-Host

$exe = Join-Path $root 'build\dotxt.exe'
if (Test-Path $exe) {
    Get-Item $exe | Select-Object FullName, Length, LastWriteTime | Format-List | Out-Host
    Write-Host 'dotxt build verification succeeded.' -ForegroundColor Green
} else {
    Write-Host 'dotxt executable missing after build.' -ForegroundColor Red
    exit 1
}
