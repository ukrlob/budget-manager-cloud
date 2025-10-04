@echo off
echo Creating desktop shortcut...

set "desktop=%USERPROFILE%\Desktop"
set "target=%~dp0start.bat"
set "shortcut=%desktop%\Budget Manager.lnk"

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%shortcut%'); $Shortcut.TargetPath = '%target%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.Description = 'Budget Manager Cloud - Personal Finance Management'; $Shortcut.Save()"

echo Desktop shortcut created: Budget Manager.lnk
echo.
echo Now you can double-click the shortcut on your desktop to start the application!
pause

