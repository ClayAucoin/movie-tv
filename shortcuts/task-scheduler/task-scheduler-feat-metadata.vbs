' silent_launch_importmetadata.vbs
Dim objShell
Set objShell = CreateObject("WScript.Shell")

' Use pythonw.exe to run the Python script, and ensure no terminal window appears
' objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\importMetaData\movies\importmetadata.py"" /task_scheduler", 0, False
objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\importMetaData\featurettes\importfeaturettesmetadata.py"" /task_scheduler", 0, False

Set objShell = Nothing