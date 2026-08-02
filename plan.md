## Fix MyPy Errors
1. Fix missing/implicit optional types in `src/model_config.py`.
2. Fix missing/implicit optional types in `src/agent.py`.
3. Add proper type hints in `src/match.py` for variables like `logs` to ensure `.append` calls don't result in union-attr errors.

## Address Code Security Concerns (Based on memory constraints)
1. In `src/environment.py`, use the Docker SDK's `put_archive` API with an in-memory tar stream to safely inject files (like secret flags) into containers, instead of using `exec_run` with bash which is vulnerable to command injection.

## Add a New Working Tested Feature (Replay Viewer)
1. Add `src/replay.py` as described in `AGENTS.md` ("Match logs are generated as JSON files and can be visualized turn-by-turn using the CLI match replay viewer located at `src/replay.py`."). It will parse a log JSON and play back the turns on standard output.
2. Add a `tests/test_replay.py` script to test `src/replay.py`.

## Pre Commit Steps
1. Run mypy again to make sure everything passes.
2. Run `tests/test_replay.py` to make sure unit test passes.
