# MemoInfinity Lite Plugin: Installing It into Hermes (Detailed Guide)

This guide covers only the Lite version, with 2 Python files. It does not cover the old Chroma version.
The 2 files are: `memo_infinity_lite.py` (the memory store) and `plugin_local_continuity_lite.py` (the plugin, renamed before use).

## 3 mistakes that are easy to make

1. Do not hard-code a username in the Hermes home path. Always use `%LOCALAPPDATA%\hermes`.
   On your computer it expands to something like `C:\Users\Administrator\AppData\Local\hermes`,
   on someone else's computer the username is different, so a hard-coded Administrator path will not be found.
2. A plugin is not loose files. Hermes recognises a plugin by "folder + `__init__.py` inside it".
   It must be placed as `plugins\local_continuity\__init__.py`, as a whole folder.
   Two files scattered directly under `plugins\` will not be recognised.
3. Do not put it in `desktop-plugins`. That is Hermes' own desktop plugin directory. Do not touch it.
   Our plugin goes only under `plugins\`, the same form as the old installed version.

## Step 0: Quit Hermes completely first

Closing the Hermes window is not enough. Quit Hermes completely, including the tray icon,
and make sure no Hermes process is still running, then start. A plugin is only loaded when Hermes starts.
If you copy files while Hermes is running, Hermes will not see them until it restarts.

## Step 1: Find the Hermes home directory, and back it up

1. Press Win+R, type `explorer %LOCALAPPDATA%\hermes`, press Enter. That is the home directory.
2. Back up 2 things first, so you can go back if something goes wrong:
   - `config.yaml` in the home directory. Copy it and rename the copy to `config.yaml.bak`, in the same place.
   - If `plugins\` already contains an old `local_continuity` folder, copy that whole old folder
     somewhere else for backup (for example, a backup folder on your desktop). Do not just delete it without a backup.
3. The Lite version and the old version do not use the same database file.
   The old version used `E:\MemoInfinity\Hermes_Memory_DB\continuity\continuity.sqlite3`,
   the Lite version creates a new file called `memo_infinity.sqlite3`. Installing Lite starts a new, empty memory store.
   Old memory is not migrated automatically. Do not delete the old database file; keeping it is keeping the old memory.

## Step 2: Place the plugin: 2 files, rename 1 of them

1. In the home directory, check whether there is a `plugins` folder. If not, create one.
2. Inside `plugins`, create (or clear and reuse) a folder named `local_continuity`.
   Why this name: the old configuration already uses `local_continuity` as the memory provider,
   so using the same name means the configuration does not need a big change.
   If the old folder is still there, move it away for backup first, then create the new one.
   Do not mix the old and new `local_continuity` folders together.
3. Copy these 2 files into `plugins\local_continuity\`:
   - `memo_infinity_lite.py`: keep this name unchanged, copy it as-is.
   - `plugin_local_continuity_lite.py`: rename it to `__init__.py` before copying it in.
   After copying, the folder should contain:
   ```
   %LOCALAPPDATA%\hermes\plugins\local_continuity\__init__.py
   %LOCALAPPDATA%\hermes\plugins\local_continuity\memo_infinity_lite.py
   ```
   You may also copy `plugin.yaml` from this package. Hermes can recognise the plugin with or without it;
   the old installed version on the host had no yaml and was still recognised and enabled, so copying it does no harm.

## Step 3: Decide which drive stores the memory, before starting Hermes

This step must be done before starting Hermes. Hermes only reads this setting when it starts.
Setting it after Hermes has started will not take effect.

- If you do not want it on the C drive (recommended): set a Windows system environment variable, then restart Hermes:
  - `MEMOINFINITY_ROOT` = `E:\MemoInfinity`
    This means: the memory file is `memo_infinity.sqlite3` inside the MemoInfinity folder on drive E.
  - Or, more directly: `MEMOINFINITY_DB` = `E:\MemoInfinity\memo_infinity.sqlite3`
    This means: the memory file is exactly this full path.
  - If both are set, `MEMOINFINITY_DB` wins. Setting only one is enough. Change the drive letter D, E, etc. as you like.
- If you set nothing: the memory file is `memo_infinity.sqlite3` in the plugin folder.
  The plugin folder is under the Hermes home directory, which is on the C drive by default.
  Reinstalling Windows would lose the memory, which is the danger already marked in the drive-location guide.
- If you already have Lite memory on the C drive and want to keep using it:
  copy that old `memo_infinity.sqlite3` file to the new path first, then set the environment variable,
  then restart Hermes. That way you continue with the old memory, not a new empty one.

## Step 4: Edit config.yaml: only the plugin section, do not touch the model

The file is: `%LOCALAPPDATA%\hermes\config.yaml`, the same file you backed up in Step 1.

1. Open it in Notepad. Press Ctrl+F and search for `plugins`. There must be only ONE `plugins:` in the whole file.
   The old version once had 2 `plugins:` sections, which caused Hermes to report a formatting error and not load plugins.
   If there are 2, delete the duplicated one and keep one.
2. In that section, confirm:
   ```
   plugins:
     enabled: [local_continuity]
   ```
   The Lite version has only this 1 plugin. Do not write `local_continuity_guard` again.
   The Lite version has no guard plugin. The old guard relied on the old continuity runtime and yaml configuration.
   The Lite version provides no yaml, so a guard would not find its configuration. Enable only `local_continuity`.
3. Confirm this line is present (keep it if it is already there; add it if it is not):
   ```
   memory:
     provider: local_continuity
   ```
   If there was a line `context.engine: local_continuity_guard`, delete it for the Lite version,
   otherwise Hermes will look for a guard that does not exist.
4. Do not touch the `model` or `base_url` section. The model endpoint is chosen by the user inside Hermes.
   Installing a plugin does not touch the model. Save and close Notepad.
5. If you have no `config.yaml` at all, or you are not sure about its format, do not invent a whole file yourself.
   Start Hermes once so it generates one, then edit only the plugin section as above.

## Step 5: Restart Hermes, and activate infinite context

This section is written in two parts. The detailed version is for people who think and want to know why.
The spoon-fed version is for beginners who do not want to think, just copy and click.

### 5A. Spoon-fed version (for beginners: just follow these 3 steps, do not think)

Step 1: Restart Hermes from the Start menu. Do not use the old launcher.
Step 2: In a new window, as the first message, copy and paste exactly this, do not change it, do not add anything else:
```
continue
```
Step 3: When the context goes over 80%, copy and paste exactly this, do not change it, do not add anything else:
```
The context is over 80%. First archive this turn's conversation and task state into MemoInfinity, confirm it is saved, then clear the old context, keep only the summary, and continue working.
```
After these 3 steps, it is activated. If Hermes returns the old objective, latest request, and constraints correctly, continue with your next step.
If it does not return them, check the troubleshooting section below. Do not guess by yourself.

### 5B. Detailed version (for people who want to know why)

- Working in the same window: no manual activation is needed. The plugin archives each turn automatically when it ends.
  Before compression, when the context is about to be compressed, the plugin archives once more first.
  So in the same window you just keep talking and working, without opening a new window. That is single-window infinite work.
- The 80% archive-transfer-clear cycle: work until the context goes over 80%. Do not wait until 100%.
  First, archive: the plugin writes this turn's original conversation plus the task state
  (objective, latest request, your original constraints, to-dos) into SQLite in one transaction. Only when it is saved is it a successful archive.
  Then, transfer: the old long conversation is already in the memory store, so it no longer needs to stay in the window.
  The window keeps only the summary and state. Then, clear: Hermes clears and compresses the old window, and enters the new window with only that summary.
  Then, continue: in the new window, say "continue" as the first message, confirm the returned objective and constraints are correct, then keep working.
  When it reaches 80% again, repeat this cycle. That way a task can go on indefinitely.
  The order must be: archive first, then clear. Never clear the window first and then try to find the memory.
- A new window, the next day, or a new session after compression: the first message must be the activation message.
  Do not chat about other things first, and do not start a new task first. The most stable activation message is:
  ```
  continue
  ```
  "Continue from where we left off" and "Restore the last task" mean the same thing, but "continue" is the simplest and most stable.
  Wait for Hermes to reply. It should return the last task: what the objective was, what the latest request was,
  and what constraints you originally set (for example, "do not go online"). When those three match, activation succeeded, then say your next step.
- If the same project has several unfinished tasks, Hermes will not pick one automatically. It will list the candidates.
  Pick one by its objective, for example, say "Restore the bookkeeping one", then keep working after it is selected. Do not let it guess.
- Do not say "do not continue", "no need to restore", "start a new task", or "switch tasks" when you want to resume.
  The plugin will hear that as a refusal to bind and will not resume.
- One more precondition: the new window and the old window must be in the same project directory.
  Memory is scoped by working directory. The same directory is the same project. A different directory is a different project.
  Saying "continue" in a different project will not find the old task.
- Verification: in `logs\agent.log` in the home directory, look for `Memory provider 'local_continuity' registered`.
  If it is there, the plugin was recognised.

## If it does not install, check in this order

- No `local_continuity` in the plugin list: first check the folder structure.
  Is it `plugins\local_continuity\__init__.py`? Not loose files, not `desktop-plugins`,
  and not `__init__.py` left unrenamed (the original name `plugin_local_continuity_lite.py` is not recognised by Hermes).
- Hermes reports a config formatting error on startup: open `config.yaml`, press Ctrl+F and search for `plugins:`.
  Are there 2 of them? Delete the duplicated one, save, and restart.
- The plugin is recognised, but "continue" does nothing: first confirm Hermes was fully quit and restarted,
  not just its window closed. Then confirm the session is in the same project (scope is set by working directory; changing directory changes the project).
- The memory went back to the C drive: was the environment variable set as a system variable before Hermes started,
  not just temporarily in a command line? Was Hermes restarted after setting it?
- The old memory cannot be found: this is expected. The Lite version is a new store. The old store file is still in its original place and was not migrated automatically.
  Do not delete the old store. If you need old memory, go back and check it the old way.

## Uninstall / Roll back

- To go back to the old version: quit Hermes completely, move the Lite folder `plugins\local_continuity\` away,
  put the old folder you backed up in Step 1 back, rename `config.yaml.bak` back to `config.yaml`, then restart Hermes.
- To stop using the Lite version completely: quit Hermes completely, delete the `plugins\local_continuity\` folder,
  remove `local_continuity` from `enabled` in `config.yaml`, and restart.
  Keep the memory file `memo_infinity.sqlite3` separately if you do not delete it; keeping it is keeping a backup of the memory.
