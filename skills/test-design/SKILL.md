---
name: test-design
description: How tests are designed, written and verified in Cinematica (the movie recommender) - risk first, named test-design techniques, stand-ins instead of patch stacks, every bug pinned by a regression test proven on the old code, mutation testing to measure the tests, and a quality suite for the recommendations themselves. Use whenever writing, reviewing or extending tests in this repository, by a person or an AI assistant.
---

# Test design for Cinematica

These are the rules the test suite in `tests/` was built by, written
so that a person or an AI assistant follows the same method. `TESTING.md`
shows the result; this file is the process.

The human owns the risks, the decisions and the verification. An AI
assistant may draft cases and code at speed, but nothing it writes is
trusted until it passes the checks in step 6.

## 1. Start from risk, not from code

Before writing a test, write down what could go wrong for a real person and
rank it by harm. Money first (a wrong price, a lost or duplicate order),
then privacy (one user seeing another's data), then trust (a failure
presented as an answer), then everything else.

- Every risk in `TESTING.md` §1 names the test files that cover it.
- A test that guards no listed risk is either covering a risk that should
  be added to the table, or not worth keeping.

## 2. Test at the lowest level that can show the behaviour

| Level | Use it for | Stand-ins |
|---|---|---|
| `unit/` | a rule: parsing, similarity, recommending, posters | small hand-made data, a TMDB stand-in |
| `data/` | the shipped catalogue and every film in it | none: the real `movie_list.csv` |
| `quality/` | whether recommendations are good | none: the real catalogue |
| `app/` | the Streamlit page: what a user sees and clicks | Streamlit's `AppTest`, a TMDB stand-in |

Never test the similarity maths through the page, and never test "the
dropdown names each film once" with hand-made data alone.

## 3. Derive cases with a named technique

Cases come from a technique, not from inspiration. For every input, ask
which of these applies:

- **Equivalence classes**: group inputs that should behave the same; take
  one from each group, including the invalid groups. TMDB failures: bad
  key, unknown movie, rate limit, timeout, not JSON - one test each.
- **Boundary values**: bugs live at edges. For a limit L, test L-1, L and
  L+1. Top cast of 3: 2, 3 and 4 actors.
- **Decision tables**: when several conditions combine, write the table
  first (condition A × B → result) and make one test per row.
- **Properties (Hypothesis)**: for rules that must hold for *every* input,
  state the rule and let Hypothesis search for a counter-example ("the
  recommendations are always the true top-k").
- **Negative**: malformed TMDB data, a film credited twice.
- **Fault injection**: TMDB failing in each way it can.

Put the table or the boundary reasoning in the test file's docstring, so the
reader sees *why* each case exists.

## 4. Stand-ins, not patch stacks

- The engine lives in `recommender.py`, apart from the Streamlit page, so
  it can be tested without the UI.
- TMDB is replaced by a stand-in that returns real `requests.Response`
  objects; every test runs with the network blocked.
- Do not stack `patch("module.x.y")` calls: they tie a test to import
  paths, so a refactor breaks tests that aren't about it.
- Assert **outcomes** (the recommendations, the cards on the page, the
  request sent), not which internal functions were called.

## 5. The quality bar for test code

- The name is a sentence about behaviour:
  `test_a_new_price_must_be_above_cost`, not `test_price_2`.
- One behaviour per test; parametrize for more inputs.
- No `or` in an assertion unless the rule itself is "either/or". An `or` is
  usually a test that doesn't know what it expects.
- No tautologies (a dict holds what was put in it) and no
  "the mock returned what the mock was told to return".
- No sleeps. Concurrency tests use events, so they are deterministic.
- Test data must not be able to hide a bug. Not zero (`now - 0 == now + 0`),
  not values where two rules agree, not ties unless the tie is the point.
- Comments explain *why* a case exists, never *what* the line does.
- A known limitation is a strict `xfail` with a reason, so it fails loudly
  the day it is fixed.

## 6. Prove the tests, don't assume them

A test that has never failed has not proven anything. Every change to the
suite goes through these checks, whoever wrote it:

1. **Run it against the old code.** A regression test must fail on the
   pre-fix code and pass on the fix (`git stash` the fix, or run against
   `git archive HEAD~1`).
2. **Mutation testing** (`mutmut run`, configured in `setup.cfg`). For every
   surviving mutant, decide: is the test weak (fix the test), or is the
   mutant equivalent (it cannot change behaviour; write down why)?
3. **Read the failure message.** A useful test fails with a message that
   points at the bug.
4. **Reference check.** Every test name cited in `TESTING.md` must exist.

## 7. Quality: is the output any good?

- Unit tests prove the engine follows its rules. Whether its
  recommendations are *good* is measured in `tests/quality/` on the real
  catalogue: franchise checks and catalogue-wide genre agreement.
- The genre-agreement floor is set just under the measured value (92.0%),
  so it catches regressions without failing on noise.
- A known weakness is a strict `xfail` with its reason, never a deleted test.
- A perfect score is a reason to read the results by hand, not to celebrate.

## 8. Every bug leaves two things behind

1. A regression test, named for the behaviour, that failed on the old code.
2. A row in the defects table in `TESTING.md` §4: what the defect was, how
   it was found, and the test that pins it.
