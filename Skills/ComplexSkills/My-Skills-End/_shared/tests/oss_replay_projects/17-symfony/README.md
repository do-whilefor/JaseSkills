# symfony/demo OSS replay adapter

This adapter is for a real local checkout of `symfony/demo`. It intentionally does not bundle third-party source code. Set environment variable `OSS_REPLAY_17_PATH` to the local checkout and run `_shared/tests/oss_replay/oss_replay_runner.py`.

Promotion is blocked unless local checkout, commit hash, exact assertions and parser readiness are recorded.
