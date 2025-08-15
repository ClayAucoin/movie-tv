' silent_launch_importmetadata.vbs
Dim objShell
Set objShell = CreateObject("WScript.Shell")

' Use pythonw.exe to run the Python script, and ensure no terminal window appears
objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\importMetaData\importmetadata.py""", 0, False

Set objShell = Nothing