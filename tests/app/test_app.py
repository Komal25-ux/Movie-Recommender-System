"""The Streamlit page, driven like a user would: pick a film, press
Recommend, read the cards. Runs app.py for real through Streamlit's AppTest,
with TMDB replaced (see the `tmdb` fixture)."""
import json
import re
from pathlib import Path

import pytest
import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from recommender import PLACEHOLDER_POSTER, POSTER_BASE_URL

APP = str(Path(__file__).resolve().parents[2] / "app.py")
KEY = "test-key-0123456789abcdef"


@pytest.fixture(autouse=True)
def fresh_caches(monkeypatch):
    """Posters are cached across runs; each test starts clean and keyless."""
    st.cache_data.clear()
    monkeypatch.delenv("TMDB_API_KEY", raising=False)


@pytest.fixture
def tmdb(monkeypatch):
    """TMDB stand-in: every movie has a poster named after its id."""
    calls = []

    def get(url, params=None, timeout=None):
        calls.append({"url": url, "params": params})
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps({"poster_path": f"/{url.rsplit('/', 1)[1]}.jpg"}).encode()
        return response

    monkeypatch.setattr(requests, "get", get)
    return calls


def open_app():
    return AppTest.from_file(APP, default_timeout=60).run()


def recommend_for(app, label):
    box = app.selectbox[0]
    box.set_value(list(box.options).index(label))
    app.button[0].click().run()
    assert not app.exception, app.exception
    return app


def cards(app):
    grid = next(m.value for m in app.markdown if m.value.startswith('<div class="movie-grid">'))
    return re.findall(r'<img src="([^"]*)" alt="([^"]*)">', grid)


def test_the_page_loads_with_every_film_in_the_dropdown():
    app = open_app()

    assert not app.exception
    options = list(app.selectbox[0].options)
    assert len(options) == len(set(options)) == 4803


def test_recommending_shows_five_cards_for_the_chosen_film():
    app = recommend_for(open_app(), "The Dark Knight")

    titles = [alt for _, alt in cards(app)]
    assert len(titles) == 5
    assert "Batman Begins" in titles
    assert any("Matches based on <span>The Dark Knight</span>" in m.value for m in app.markdown)


@pytest.mark.parametrize("label", ["Signed, Sealed, Delivered", "Shanghai Calling", "My Date with Drew"])
def test_the_films_that_crashed_the_original_app_now_get_recommendations(label):
    assert len(cards(recommend_for(open_app(), label))) == 5


def test_a_horror_film_shows_horror_not_the_neighbouring_rows_comedies():
    titles = [alt for _, alt in cards(recommend_for(open_app(), "Devil"))]

    assert "House on Haunted Hill" in titles
    assert "Paul Blart: Mall Cop" not in titles   # what the original app showed


def test_titles_with_ampersands_and_apostrophes_are_escaped_in_the_html():
    app = recommend_for(open_app(), "Batman Forever")

    alts = [alt for _, alt in cards(app)]
    assert "Batman &amp; Robin" in alts
    grid = next(m.value for m in app.markdown if m.value.startswith('<div class="movie-grid">'))
    assert "Batman & Robin" not in grid


def test_without_a_key_posters_are_placeholders_and_tmdb_is_never_called(tmdb):
    app = recommend_for(open_app(), "Avatar")

    assert {src for src, _ in cards(app)} == {PLACEHOLDER_POSTER}
    assert tmdb == []


def test_with_a_key_posters_come_from_tmdb_and_the_key_never_reaches_the_page(tmdb, monkeypatch):
    monkeypatch.setenv("TMDB_API_KEY", KEY)

    app = recommend_for(open_app(), "Avatar")

    assert all(src.startswith(POSTER_BASE_URL) for src, _ in cards(app))
    assert len(tmdb) == 5 and all(call["params"]["api_key"] == KEY for call in tmdb)
    assert not any(KEY in m.value for m in app.markdown)


def test_a_key_in_streamlit_secrets_is_used_too(tmdb):
    app = open_app()
    app.secrets["TMDB_API_KEY"] = KEY

    recommend_for(app, "Avatar")

    assert tmdb and tmdb[0]["params"]["api_key"] == KEY


def test_the_same_poster_is_fetched_once_however_often_it_is_shown(tmdb, monkeypatch):
    monkeypatch.setenv("TMDB_API_KEY", KEY)
    app = recommend_for(open_app(), "Avatar")

    app.button[0].click().run()

    assert len(tmdb) == 5   # the second press is served from the cache
