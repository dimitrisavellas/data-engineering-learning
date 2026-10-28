## IndexError on sys.argv[1] in pipeline.py  (01)
- **Error:** `IndexError: list index out of range` on `month = sys.argv[1]`
- **Checked:** the `Arguments:` print showed the list only contained the script path
- **Cause:** ran `uv run python pipeline.py` without passing a value, so `sys.argv` had only index 0
- **Fix:** pass the argument on the command line: `uv run python pipeline.py 12`
- **Lesson:** `sys.argv[0]` is always the script itself; anything typed after the script name starts at index 1, and every value arrives as a string


## Cause:           (02)
  
  1. The `.` in `docker build .` means "use only this folder". My `uv.lock` was in the main repo folder, so Docker couldn't see it.
  2. `uv init` connected this folder to the main repo project instead of making a separate one (it said so in its first output line), so no `.python-version` was created here.
  3. `pyproject.toml` had a `[build-system]` section, which tells uv the folder is a library. uv then looked for library code that doesn't exist.
  4. I changed `pyproject.toml` without running `uv lock`, so the lock file no longer matched, and `--locked` stopped the build.
- **Lesson:**
  - The Python version in `.python-version` must match the one in the Dockerfile's `FROM` line.