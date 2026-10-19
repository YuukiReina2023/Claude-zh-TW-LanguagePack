@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0LanguagePack.ps1" -Install -PauseAtEnd
