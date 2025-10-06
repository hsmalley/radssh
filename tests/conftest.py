"""Pytest fixtures for the radssh test suite.

Provides a `cluster_factory` fixture that returns a callable to construct
`radssh.ssh.Cluster` instances with `start_threads=False` by default so tests
can create clusters without spawning background threads.
"""

from __future__ import annotations

import pytest
import radssh.plugins as _plugins


@pytest.fixture
def cluster_factory():
    """Return a factory that constructs Cluster instances with no background threads.

    Usage in tests:
        cluster = cluster_factory(hosts=[...])
    """

    def _factory(*, hosts=None, **kwargs):
        # Import inside factory to keep module import light-weight for collection
        from radssh.ssh import Cluster

        if hosts is None:
            hosts = []
        # Ensure tests opt out of thread startup unless explicitly requested
        kwargs.setdefault("start_threads", False)
        return Cluster(hosts=hosts, **kwargs)

    return _factory


@pytest.fixture(autouse=True)
def clear_plugins_between_tests():
    """Automatically clear the plugin registry before and after each test.

    This avoids accidental state leakage between tests and removes the need
    for individual tests to remember to call `plugins.clear()`.
    """
    _plugins.clear()
    yield
    _plugins.clear()
