' BTC On-chain Dashboard Launcher
' - Streamlit을 백그라운드(콘솔 숨김)로 실행하고
' - Edge/Chrome 앱 모드(--app)로 주소창 없는 독립 창으로 띄운다.
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
WshShell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)

url = "http://localhost:8503"

' 1) Streamlit 실행 (headless, 콘솔창 숨김)
WshShell.Run "cmd /c streamlit run app.py --server.port 8503 --server.headless true", 0, False

' 2) 서버 기동 대기 (첫 실행은 다소 느림)
WScript.Sleep 5000

' 3) 앱 모드로 열 Chromium 브라우저 찾기 (Edge 우선, 없으면 Chrome)
browser = ""
paths = Array( _
  "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", _
  "C:\Program Files\Microsoft\Edge\Application\msedge.exe", _
  "C:\Program Files\Google\Chrome\Application\chrome.exe", _
  "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" )
For Each p In paths
  If browser = "" Then
    If fso.FileExists(p) Then browser = p
  End If
Next

' 4) 독립 앱 창으로 열기 (실패 시 기본 브라우저)
If browser <> "" Then
  WshShell.Run """" & browser & """ --app=" & url & " --window-size=1200,900", 1, False
Else
  WshShell.Run url
End If
