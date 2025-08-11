' silent_launch_arrs.vbs
Dim objShell
Set objShell = CreateObject("WScript.Shell")

' Pass a flag indicating if the task is running via Task Scheduler
objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\arr\Radarr\updateRadarrData.py"" /task_scheduler", 0, False
objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\arr\Sonarr\updateSonarrData.py"" /task_scheduler", 0, False
objShell.Run """pythonw.exe"" ""C:\Users\Administrator\projects\movie-tv\importMetaData\featurettesDirCheck.py""", 0, False

Set objShell = Nothing
