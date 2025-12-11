$ErrorActionPreference = "Stop"
.\packaging\build_windows.ps1
# Placeholder for MSIX packaging commands (makeappx / signtool) if available in environment.
Write-Host "Build complete. For MSIX, run makeappx + signtool with dist output."
