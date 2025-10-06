# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- `radssh.plugins` — a minimal, side-effect-free plugin registry module used by the application and tests. This replaces several test-time import shims and makes plugin management explicit.

- `tests/conftest.py` — pytest fixtures including `cluster_factory` that construct `Cluster` instances with `start_threads=False` to avoid starting background threads during unit tests.

### Changed

- Tests updated to use the `radssh.plugins` registry instead of injecting `sys.modules['radssh.plugins']`.

- `Cluster` gained a `start_threads` parameter (default True) to opt out of background thread startup for tests and tooling.

### Notes

- The `radssh.plugins` module intentionally exposes a minimal registry API (`register`, `get`, `iter_plugins`, `get_plugins`, `clear`) and is safe to import during test collection.
