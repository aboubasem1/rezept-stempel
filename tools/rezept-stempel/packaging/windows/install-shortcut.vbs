' Desktop- und Startmenue-Verknuepfung ohne PowerShell-Ausfuehrungsrichtlinie.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)
root = fso.GetParentFolderName(fso.GetParentFolderName(here))
exe = root & "\dist\Rezept-Stempel.exe"
pyw = root & "\Rezept-Stempel.pyw"
pythonw = root & "\venv\Scripts\pythonw.exe"
If Not fso.FileExists(pythonw) Then pythonw = root & "\.venv\Scripts\pythonw.exe"

target = ""
args = ""
work = root
If fso.FileExists(exe) Then
  target = exe
  work = fso.GetParentFolderName(exe)
ElseIf fso.FileExists(pythonw) And fso.FileExists(pyw) Then
  target = pythonw
  args = """" & pyw & """"
Else
  WScript.Echo "Bitte zuerst packaging\windows\build.ps1 ausfuehren oder ein venv anlegen."
  WScript.Quit 1
End If

Sub MakeLink(path)
  Set sc = sh.CreateShortcut(path)
  sc.TargetPath = target
  sc.Arguments = args
  sc.WorkingDirectory = work
  sc.WindowStyle = 1
  sc.Description = "Rezept-PDFs stempeln (Menge und Datum)"
  sc.Save
End Sub

desktop = sh.SpecialFolders("Desktop")
startMenu = sh.SpecialFolders("Programs")
MakeLink desktop & "\Rezept-Stempel.lnk"
MakeLink startMenu & "\Rezept-Stempel.lnk"
WScript.Echo "Verknuepfungen erstellt: Desktop und Startmenue."
