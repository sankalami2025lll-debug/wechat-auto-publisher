import pytest


@pytest.fixture
def sample_config() -> dict:
    return {
        "app_name": "wechat-auto-publisher",
        "version": "0.1.0",
    }
