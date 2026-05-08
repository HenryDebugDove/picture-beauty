# Picture Beauty：打包为 Windows 桌面 exe（单文件、无黑框）
# 在项目根目录执行：powershell -ExecutionPolicy Bypass -File .\pack_desktop.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Installing build dependencies..."
pip install -r requirements-build.txt -q

Write-Host "Running PyInstaller..."
pyinstaller --clean --noconfirm picture-beauty.spec

$exe = Join-Path $PSScriptRoot "dist\PictureBeauty.exe"
if (Test-Path $exe) {
    Write-Host "OK: $exe"
} else {
    Write-Host "Build finished but exe not found at expected path."
    exit 1
}
