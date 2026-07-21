Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)

pythonw = folder & "\.venv\Scripts\pythonw.exe"
pythonexe = folder & "\.venv\Scripts\python.exe"
bootstrap = folder & "\bootstrap_web.py"
setupScript = folder & "\setup.cmd"

If Not fso.FileExists(pythonw) Then
    If fso.FileExists(setupScript) Then
        result = shell.Run("cmd.exe /c """ & setupScript & """", 1, True)
        If result <> 0 Then
            MsgBox "Setup failed. Run StoneLightLauncher_debug.cmd and send the console output.", 48, "StoneLight Launcher"
            WScript.Quit result
        End If
    Else
        MsgBox "Virtual environment not found and setup.cmd is missing.", 48, "StoneLight Launcher"
        WScript.Quit 1
    End If
End If

If Not fso.FileExists(pythonw) Then
    MsgBox "pythonw.exe was not found after setup. Run StoneLightLauncher_debug.cmd.", 48, "StoneLight Launcher"
    WScript.Quit 1
End If

If Not fso.FileExists(bootstrap) Then
    MsgBox "bootstrap_web.py not found.", 48, "StoneLight Launcher"
    WScript.Quit 1
End If

shell.CurrentDirectory = folder
shell.Run """" & pythonw & """ """ & bootstrap & """", 0, False
