$desktop = [Environment]::GetFolderPath('Desktop')
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$desktop\SFlow.lnk")
$Shortcut.TargetPath = 'C:\ProyectosIA\SFLOWPeter\sflow\SFlow.vbs'
$Shortcut.IconLocation = 'C:\ProyectosIA\SFLOWPeter\sflow\sflow.ico'
$Shortcut.Description = 'SFlow - Voice to text'
$Shortcut.Save()
Write-Host "Acceso directo actualizado en: $desktop\SFlow.lnk"
