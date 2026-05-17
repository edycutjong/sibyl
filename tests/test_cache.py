from unittest.mock import MagicMock

import pytest

from sibyl import cache as cache_module
from sibyl.cache import _get_cache, cache_key, get_cached, set_cached


@pytest.fixture(autouse=True)
def reset_cache():
    # Reset the global _cache before and after each test
    cache_module._cache = None
    yield
    cache_module._cache = None


def test_cache_key():
    # Test string input
    key1 = cache_key("test", "data")
    assert key1.startswith("test:")
    assert len(key1) == 5 + 16

    # Test dict input (should sort keys)
    dict1 = {"b": 2, "a": 1}
    dict2 = {"a": 1, "b": 2}
    assert cache_key("dict", dict1) == cache_key("dict", dict2)


def test_get_cache_initialization(mocker):
    mock_settings = MagicMock()
    mock_settings.cache_dir = "/tmp/test_cache"
    mocker.patch("sibyl.cache.get_settings", return_value=mock_settings)
    mock_diskcache = mocker.patch("sibyl.cache.diskcache.Cache")

    c = _get_cache()
    mock_diskcache.assert_called_once_with("/tmp/test_cache")

    # Should not re-initialize
    c2 = _get_cache()
    assert mock_diskcache.call_count == 1
    assert c == c2


def test_set_and_get_cached(mocker):
    mock_cache_instance = MagicMock()
    mock_cache_instance.get.return_value = "cached_value"
    mocker.patch("sibyl.cache._get_cache", return_value=mock_cache_instance)

    set_cached("mykey", "myval", 100)
    mock_cache_instance.set.assert_called_once_with("mykey", "myval", expire=100)

    val = get_cached("mykey")
    assert val == "cached_value"
    mock_cache_instance.get.assert_called_once_with("mykey")


def test_get_cached_exception(mocker):
    mock_cache_instance = MagicMock()
    mock_cache_instance.get.side_effect = Exception("DB error")
    mocker.patch("sibyl.cache._get_cache", return_value=mock_cache_instance)

    val = get_cached("mykey")
    assert val is None


def test_set_cached_exception(mocker, caplog):
    mock_cache_instance = MagicMock()
    mock_cache_instance.set.side_effect = Exception("DB error")
    mocker.patch("sibyl.cache._get_cache", return_value=mock_cache_instance)

    # Should not raise
    set_cached("mykey", "myval")

    assert "Cache write failed: DB error" in caplog.text
