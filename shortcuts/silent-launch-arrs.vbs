' silent_launch_arrs.vbs
Dim objShell
Set objShell = CreateObject("WScript.Shell")

' run the scripts without the task scheduler flag
objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\arr\Radarr\updateRadarrData.py""", 0, False
objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\arr\Sonarr\updateSonarrData.py""", 0, False
Set objShell = Nothing

' example of how to run with the task scheduler flag
' objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\arr\Radarr\updateRadarrData.py"" /task_scheduler", 0, False
