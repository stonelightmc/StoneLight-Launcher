Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = folder & "\.venv\Scripts\pythonw.exe"
bootstrap = folder & "\bootstrap.py"

If Not fso.FileExists(pythonw) Then
    MsgBox "Virtual environment not found. Run setup.cmd first.", 48, "StoneLight Launcher"
    WScript.Quit 1
End If

shell.CurrentDirectory = folder
shell.Run """" & pythonw & """ """ & bootstrap & """", 0, False
