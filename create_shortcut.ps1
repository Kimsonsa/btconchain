$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $ws.CreateShortcut("$desktop\BTC 온체인 대시보드.lnk")
$shortcut.TargetPath = "C:\projects\btconchain\BTCDashboard.vbs"
$shortcut.WorkingDirectory = "C:\projects\btconchain"
$shortcut.Description = "BTC 온체인 대시보드"
$shortcut.IconLocation = "shell32.dll,134"
$shortcut.Save()
Write-Host "Desktop shortcut created: $desktop\BTC 온체인 대시보드.lnk"
