"""Shared test setup:  no test may open a network connection.

The key-check tests use fake openers.  If a code change ever sends a request through the real network,
the test fails here instead of calling the API with a real key from a developer's environment.
"""
import socket

import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("a test tried to open a network connection")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
