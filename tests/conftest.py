import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring external services"
    )
    config.addinivalue_line(
        "markers", "live: mark test as requiring live network calls"
    )
