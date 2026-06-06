' BTC On-chain Dashboard Launcher (console hidden)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c streamlit run app.py --server.port 8503", 0, False
WScript.Sleep 2500
WshShell.Run "http://localhost:8503"
