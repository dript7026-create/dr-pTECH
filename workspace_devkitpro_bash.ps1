param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$Command
)

$bash = "C:\devkitPro\msys2\usr\bin\bash.exe"
if (-not (Test-Path $bash)) {
    Write-Error "devkitPro bash not found at $bash"
    exit 1
}

$commandText = ($Command -join ' ')
$script = @(
    'export DEVKITPRO=/c/devkitPro',
    'export DEVKITARM=/c/devkitPro/devkitARM',
    'export DEVKITPPC=/c/devkitPro/devkitPPC',
    'export DEVKITA64=/c/devkitPro/devkitA64',
    'export PATH=/c/devkitPro/devkitARM/bin:/c/devkitPro/devkitA64/bin:/c/devkitPro/devkitPPC/bin:/c/devkitPro/tools/bin:/c/devkitPro/msys2/usr/bin:$PATH',
    "cd '$((Split-Path -Parent $MyInvocation.MyCommand.Definition) -replace '\\', '/')'",
    $commandText
) -join '; '

& $bash -lc $script
exit $LASTEXITCODE