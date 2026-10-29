# How Cinematica is tested

107 automated tests run in about 15 seconds on every push. Mutation testing
measures whether those tests would catch bugs, and a quality suite checks
whether the recommendations are any good. The method is the same one used
for Sakhi, written down in
[skills/test-design/SKILL.md](skills/test-design/SKILL.md).

```bash
pip install -r requirements-dev.txt
pytest                         # everything
pytest tests/unit              # one level
HYPOTHESIS_PROFILE=ci pytest   # property tests with CI's fixed seed
mutmut run && mutmut results   # mutation testing (setup.cfg)
```

## 1. What could go wrong, and where it is covered

| # | Risk | What a failure looks like | Covered in |
|---|---|---|---|
| 1 | A movie gets another film's recommendations | Choosing a horror film shows five comedies | `data/test_catalogue.py`, `quality/`, `app/test_app.py` |
| 2 | The app crashes for some films | A red Python traceback instead of results | `data/test_catalogue.py` (every film), `app/test_app.py` |
| 3 | The catalogue is built wrongly | Two films sharing a title swap casts; films silently dropped | `unit/test_pipeline.py`, `data/test_catalogue.py` |
| 4 | The engine breaks its own rules | A film recommends itself; a weak match ranks above a strong one | `unit/test_recommend.py`, `unit/test_similarity.py` |
| 5 | TMDB misbehaves | A slow or failing API hangs or breaks the page | `unit/test_posters.py`, `app/test_app.py` |
| 6 | The API key leaks | The key appears in the source or the page | `app/test_app.py` |
| 7 | The recommendations are simply poor | Sequels don't bring up their series | `quality/test_recommendation_quality.py` |

## 2. Levels

| Level | Tests | What it covers |
|---|---:|---|
| `unit/` | 74 | Parsing TMDB's data, building the catalogue, similarity, recommending, dropdown labels, posters |
| `data/` | 7 | The shipped `movie_list.csv`, and a sweep recommending for all 4,803 films |
| `quality/` | 15 | Franchise checks and catalogue-wide genre agreement |
| `app/` | 11 | The Streamlit page itself, driven through Streamlit's `AppTest` like a user |

To make this testable, the logic moved out of the Streamlit page and the
notebook into `recommender.py`; `app.py` is now only the page. TMDB is
replaced in tests by a stand-in that returns real `requests.Response`
objects, and every test runs with the network blocked.

## 3. Techniques

| Technique | Where |
|---|---|
| **Boundary values** | Top cast: 0, 1, 2, 3 (the limit), 4 and 25 actors; result count `k` = 0, 1, 4, 5; ties among 6 vs 200 films |
| **Equivalence classes** | TMDB failures: bad key, unknown movie, rate limit, server error, timeout, offline, not JSON, unexpected JSON; poster paths: null, missing, empty, relative, not a string |
| **Decision rules** | `recommend()`: best first · never itself · ties keep catalogue order · zero similarity is no recommendation · at most k |
| **Property-based (Hypothesis)** | "Similarity is symmetric and between 0 and 1", "a film with a real word is fully similar to itself", "recommendations are always the true top-k" |
| **Negative** | Malformed TMDB JSON fails the build; a film credited twice is a build error |
| **Regression** | Every defect below; the app-level ones were run against the original code, where they failed |
| **Golden file** | The shipped catalogue must equal what `build_model.py` produces from the CSVs |
| **Known limitation** | A strict `xfail` for *The Hangover Part II* (see section 6) |

## 4. Defects found

| # | Defect | Found by | Pinned by |
|---|---|---|---|
| 1 | **2,148 of 4,806 films (45%) got another film's recommendations.** `dropna()` left gaps in the row labels and `recommend()` used a label as a row number. "Devil" (horror) showed *Paul Blart: Mall Cop* and four other comedies | Inspecting the saved data | `data/test_catalogue.py::test_rows_are_numbered_zero_to_n_minus_one`, `app/test_app.py::test_a_horror_film_shows_horror_not_the_neighbouring_rows_comedies` |
| 2 | The last 3 films in the list crashed the app with an `IndexError` traceback | Same | `app/test_app.py::test_the_films_that_crashed_the_original_app_now_get_recommendations` |
| 3 | Movies and credits were joined on title: the 3 shared titles became 12 rows, 6 of them with the other film's cast and director | Reading the notebook | `unit/test_pipeline.py::test_two_films_with_the_same_title_each_keep_their_own_cast` |
| 4 | "Batman" and "The Host" recommended themselves | Inspecting results | `unit/test_recommend.py::test_the_chosen_movie_is_never_recommended_even_when_another_ties_with_it`, `data/test_catalogue.py::test_every_movie_gets_five_recommendations_and_never_itself` |
| 5 | The dropdown listed "Batman" 4 times with no way to tell them apart | Running the app | `unit/test_display_titles.py`, `data/test_catalogue.py::test_every_dropdown_entry_names_exactly_one_film` |
| 6 | Films with no overview were silently dropped from the catalogue | Reading the notebook | `unit/test_pipeline.py::test_a_film_without_an_overview_is_kept_rather_than_dropped` |
| 7 | The TMDB API key was written in the public source code | Reading the code | `app/test_app.py::test_with_a_key_posters_come_from_tmdb_and_the_key_never_reaches_the_page` |
| 8 | Poster requests had no timeout, so a slow TMDB could hang the page | Reading the code | `unit/test_posters.py::test_the_request_carries_the_key_as_a_parameter_and_a_timeout` |
| 9 | Titles were only partly HTML-escaped | Reading the code | `app/test_app.py::test_titles_with_ampersands_and_apostrophes_are_escaped_in_the_html` |
| 10 | `build_similarity` crashed on a catalogue with no usable words (introduced during this work) | A property test | `unit/test_similarity.py::test_a_catalogue_with_no_usable_words_has_no_similarities_instead_of_crashing` |
| 11 | The README claimed Porter stemming that the code never did, a "5000×5000" matrix, and placeholder links | Review | Corrected in the README |

The catalogue also moved from a pickle to `movie_list.csv`. A pickle written
by one pandas version may not load in another, and loading pickles is a
security risk. `test_the_shipped_file_is_exactly_what_build_model_produces`
keeps the file and the code in step.

## 5. Mutation testing

[mutmut](https://github.com/boxed/mutmut) plants small bugs in
`recommender.py` and runs the unit tests against each one (`setup.cfg`).

| Run | Killed | Survived |
|---|---:|---:|
| First | 164 / 176 | 12 |
| Final | **173 / 176** | 3 |

The survivors showed three weaknesses in the tests:

- **Nothing checked the catalogue's columns.** A renamed column passed.
- **Nothing checked that years are whole numbers.** A decimal year still
  equals 1989 in Python, but users would have seen "Batman (1989.0)".
- **Six tied films were too few.** NumPy's default sort only reorders ties
  on longer arrays, so it took 200 tied films to show the difference.

The last 3 are **equivalent mutants**: joining with no `on=` still joins on
`movie_id`, the only shared column (two mutants), and NumPy accepts
"STABLE" as well as "stable".

## 6. Recommendation quality

Unit tests prove the engine follows its rules; the quality suite checks its
output on the real catalogue.

- **Franchises:** 12 sequels must bring up their series (Dark Knight →
  Batman films, Iron Man 2 → Iron Man, all the Harry Potters...). All pass.
- **Genre agreement:** across all 4,803 films, the share of
  recommendations that share a genre with the chosen film. **The fixed engine
  scores 92.0%; the original app scored 76.9%**, because of defect 1. The
  test fails below 90%.
- **Known limitation:** *The Hangover Part II* recommends wedding films (its
  plot is a wedding in Thailand), not *The Hangover*. Word counts weigh the
  plot more than the shared cast. This is recorded as a strict `xfail`.

## 7. Not covered

- The look of the page: CSS and layout are checked by eye, not by tests.
- The real TMDB API: always replaced in tests.
- Performance: the similarity matrix takes a few seconds at startup, and
  that is not measured.
- The notebook: it remains as exploration; `recommender.py` is the tested
  source of truth.
