"""Shared test setup.

Layout (see TESTING.md):
  unit/      the engine's rules: data parsing, similarity, recommending, posters
  data/      the shipped catalogue (movie_list.csv) and the whole-catalogue sweep
  quality/   whether the recommendations are any good: franchises and genres
  app/       the Streamlit page itself, driven by Streamlit's AppTest
"""
import os
import socket
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import HealthCheck, settings as hypothesis_settings

from recommender import build_movies, build_similarity

ROOT = Path(__file__).resolve().parent.parent

# CI runs property tests with a fixed seed so a failure always reproduces.
hypothesis_settings.register_profile("ci", derandomize=True, deadline=None, max_examples=200)
hypothesis_settings.register_profile("dev", deadline=None, suppress_health_check=[HealthCheck.too_slow])
hypothesis_settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """A test that reaches for the real TMDB API fails loudly."""
    def refuse(self, *args, **kwargs):
        raise RuntimeError(f"Network access attempted during a test: {args}")
    monkeypatch.setattr(socket.socket, "connect", refuse)


# The real catalogue and its similarity matrix take a few seconds to build,
# so each is built once per test run and shared (tests only read them).

@pytest.fixture(scope="session")
def catalogue() -> pd.DataFrame:
    return pd.read_csv(ROOT / "movie_list.csv", dtype={"year": "Int64"})


@pytest.fixture(scope="session")
def similarity(catalogue):
    return build_similarity(catalogue["tags"])


@pytest.fixture(scope="session")
def built_from_csvs() -> pd.DataFrame:
    """The catalogue rebuilt from the raw TMDB CSVs, with genres kept."""
    return build_movies(pd.read_csv(ROOT / "tmdb_5000_movies.csv"), pd.read_csv(ROOT / "tmdb_5000_credits.csv"))


@pytest.fixture(scope="session")
def position_of(catalogue):
    """Row position of a movie, by title (titles used in tests are unique)."""
    def find(title: str) -> int:
        matches = catalogue.index[catalogue["title"] == title]
        assert len(matches) == 1, f"{title!r} matches {len(matches)} movies"
        return int(matches[0])
    return find
