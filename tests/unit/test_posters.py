"""poster_url(): a poster from TMDB, or a placeholder - never an exception.

Each case below is something TMDB or the network can actually do."""
import json

import numpy as np
import pytest
import requests

from recommender import PLACEHOLDER_POSTER, POSTER_BASE_URL, POSTER_TIMEOUT_SECONDS, poster_url


class TMDB:
    """Stands in for requests.get: answers with a real requests.Response (or
    raises), and records every call."""

    def __init__(self, status=200, body=None, raises=None):
        self.status, self.body, self.raises = status, body, raises
        self.calls = []

    def __call__(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if self.raises:
            raise self.raises
        response = requests.Response()
        response.status_code = self.status
        response._content = (self.body if isinstance(self.body, bytes) else json.dumps(self.body).encode())
        return response


def test_a_poster_path_becomes_a_full_image_url():
    tmdb = TMDB(body={"poster_path": "/kqjL17yufvn9OVLyXYpvtyrFfak.jpg"})

    assert poster_url(19995, "key", get=tmdb) == POSTER_BASE_URL + "/kqjL17yufvn9OVLyXYpvtyrFfak.jpg"


def test_the_request_carries_the_key_as_a_parameter_and_a_timeout():
    tmdb = TMDB(body={"poster_path": "/p.jpg"})

    poster_url(np.int64(19995), "secret-key", get=tmdb)   # ids come from pandas as numpy ints

    [call] = tmdb.calls
    assert call["url"] == "https://api.themoviedb.org/3/movie/19995"
    assert call["params"] == {"api_key": "secret-key", "language": "en-US"}
    assert "secret-key" not in call["url"]
    assert call["timeout"] == POSTER_TIMEOUT_SECONDS   # without one, a slow TMDB hangs the page


@pytest.mark.parametrize("key", ["", None])
def test_without_a_key_tmdb_is_not_even_asked(key):
    tmdb = TMDB(body={"poster_path": "/p.jpg"})

    assert poster_url(1, key, get=tmdb) == PLACEHOLDER_POSTER
    assert tmdb.calls == []


@pytest.mark.parametrize("tmdb", [
    TMDB(status=401, body={"status_message": "Invalid API key"}),
    TMDB(status=404, body={"status_message": "Not found"}),
    TMDB(status=429, body={"status_message": "Rate limited"}),
    TMDB(status=500, body={}),
    TMDB(raises=requests.Timeout("read timed out")),
    TMDB(raises=requests.ConnectionError("no route to host")),
    TMDB(body=b"<html>not json</html>"),
    TMDB(body=["a list, not an object"]),
], ids=["bad key", "unknown movie", "rate limited", "server error", "timeout", "offline", "not json", "unexpected json"])
def test_any_failure_gives_the_placeholder(tmdb):
    assert poster_url(1, "key", get=tmdb) == PLACEHOLDER_POSTER


@pytest.mark.parametrize("body", [
    {"poster_path": None},              # TMDB's answer for a film with no poster
    {},
    {"poster_path": ""},
    {"poster_path": "relative.jpg"},    # not a TMDB path
    {"poster_path": 12345},
], ids=["null", "missing", "empty", "no leading slash", "not a string"])
def test_a_missing_or_odd_poster_path_gives_the_placeholder(body):
    assert poster_url(1, "key", get=TMDB(body=body)) == PLACEHOLDER_POSTER


def test_by_default_the_real_requests_library_is_used_at_call_time(monkeypatch):
    tmdb = TMDB(body={"poster_path": "/p.jpg"})
    monkeypatch.setattr(requests, "get", tmdb)

    assert poster_url(1, "key") == POSTER_BASE_URL + "/p.jpg"
    assert len(tmdb.calls) == 1
