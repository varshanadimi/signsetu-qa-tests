# conftest.py — Pytest configuration for SignSetu QA Test Suite

import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "bug: marks tests as vulnerability/bug detection tests"
    )
    config.addinivalue_line(
        "markers", "edge: marks tests as edge case tests"
    )
    config.addinivalue_line(
        "markers", "lifecycle: marks tests as core lifecycle tests"
    )
