# Search for conflicting files system-wide
Write-Host "Searching for PIL.py and image.py files system-wide..."
Get-ChildItem -Path C:\ -Recurse -ErrorAction SilentlyContinue -Include PIL.py,image.py | Select-Object FullName

# Check Pillow installation for Blender's Python
$blenderPython = "C:\Program Files\Blender Foundation\Blender 5.0\5.0\python\bin\python.exe"
if (Test-Path $blenderPython) {
    Write-Host "`nChecking Pillow installation in Blender's Python..."
    & $blenderPython -m pip show pillow
    Write-Host "`nBlender Python sys.path:"
    & $blenderPython -c "import sys; print('\n'.join(sys.path))"
} else {
    Write-Host "Blender Python not found at $blenderPython"
}