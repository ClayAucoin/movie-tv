# Instructions
After cloning, fix script paths in all of the .vbs files.

## Triggering

### Shortcut Links


### Task Scheduler
* Create a task.
* Trigger
    * Daily
    * Repeat task every 5 minutes
* Actions
    * Program/script: `wscript.exe`
    * Add arguments: `"__path to repo__\arr\silent_launch_arrs-task-scheduler.vbs"`
* Settings
    * Allow task to be run on demand
    * Run task as soon as possible after a scheduled start is missed
