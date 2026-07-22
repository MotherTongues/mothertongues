# MotherTongues Revival Plan

Status: draft, based on a full-codebase health review on 2026-07-21. Both `mothertongues` (Python) and `mothertongues-UI` (Nx/Angular submodule) have had no substantive commits since June 2024. This plan sequences the work needed to bring both back to a maintainable, currently-supported state.

**Suggested execution order:** 5 (done) → 2 (done) → 1 (done) → 6 (python half) → 3 → 4 → 6 (UI half). Dependabot is cheap and immediately surfaces the true dependency gap; PR #33 is easiest to land *before* the pyproject/tooling churn of step 1 touches the same files it touches; the Python code-smell cleanup pairs naturally with step 1 since you're already in `pyproject.toml`/CI; the UI code-smell cleanup pairs naturally with step 3/4 since you're already touching those components. The list below stays in the order requested, with cross-references to this sequencing.

---

## 1. Bump Python floor and migrate Poetry → uv

**Why:** `pyproject.toml` still declares `python = "^3.8"` (EOL Oct 2024). `poetry.lock` pins `numpy` 1.24.4, which fails to build on Python 3.12 (issue #35) — a known, unresolved pain point. Dev tools (`black ^22.12`, `pre-commit ^2.20`, `mypy ^1.4.1`) are all multiple majors behind. Issue #38 ("switch to hatch") already flags dissatisfaction with Poetry; this plan uses **uv** instead, which is faster, PEP 621-native, and increasingly the de facto standard — closing #38 with a different (better-suited) resolution.

**Steps:**
- Raise the floor to a currently-supported Python (3.10 or 3.11 minimum — check what NLTK/rank-bm25/pydantic 2.x actually require before picking the floor).
- Convert `[tool.poetry]` sections to a standard PEP 621 `[project]` table; move `[tool.poetry.dependencies]`/`dev`/`docs` groups to `[project.dependencies]` and `[dependency-groups]` (uv's native grouping).
- Replace `poetry.lock` with `uv.lock`; drop the `poetry-core` build backend if switching to `hatchling` or `setuptools` (uv doesn't require Poetry's backend).
- Update all three CI workflows (`.github/workflows/tests.yml`, `docs.yml`, `release-tests.yml`) — replace `abatilo/actions-poetry` + `poetry install`/`poetry run` with `astral-sh/setup-uv` + `uv sync`/`uv run`. `release-tests.yml`'s OS/Python matrix is a good opportunity to also resolve issue #41 ("add matrix tests for publishing that test all python versions we support") if it isn't already fully satisfied.
- Update `.pre-commit-config.yaml`'s local isort/black/mypy hooks to current versions once they're driven by `uv`.
- Re-pin `numpy` without the `<3.12`/`>=3.12` split now that the floor excludes the broken combination — this should let issue #35 close outright.
- Update README's "Local Install" section (currently says "Python 3.8+... poetry") and the badge/instructions to match.
- Bump `LICENSE` copyright line (currently frozen at "2016-2023") while touching packaging metadata.
- Nice-to-have while in here: issue #39 asks for semantic versioning + a `mothertongues --version` CLI command — small enough to fold into this pass since you're already touching `pyproject.toml` version handling.

**Verify:** `uv run pytest mothertongues/tests/` green on the new floor; `uv build` produces an installable wheel; CI matrix passes on all supported OS/Python combos.

---

## 2. Review and land PR #33 ("Improve tabular parsers to allow for column headers in manifest")

**Why:** Mergeable, well-tested (adds `test_basic_tabular_parsers_use_header` plus header fixture files for csv/tsv/psv/xlsx), from a trusted contributor (David Huggins-Daines), and closes real gaps — it also happens to resolve issue #37 ("CSV parser should support 'A','B' as well as '0','1'"). It's been sitting since March 2024. Land it before the Python tooling migration (step 1) touches the same parser files, to avoid a painful rebase.

**Review checklist (from reading the diff):**
- The author's own PR description flags an unresolved design question: the new `use_header` flag overlaps with the existing `skip_header` flag ("perhaps we should only keep one of them, and just call it `header`?"). Decide before merge — either consolidate now or file a fast-follow issue; don't let it merge silently ambiguous.
- `BaseTabularParser.parse_fn` (`mothertongues/parsers/__init__.py`) falls back from a named-column lookup to `col2int(y, base0=True)` when the key isn't found in `self.fieldnames`. Confirm this fallback is intentional and not silently masking a typo'd column name in someone's manifest (e.g. `"Speaker"` vs. actual header `"speaker"`) — consider whether a typo should raise instead of silently reinterpreting the name as a spreadsheet column letter.
- `xlsx_parser.py`'s new `self.fieldnames = {c.value: c.column for (c,) in work_sheet.iter_cols(...)}` will silently drop earlier columns on duplicate header names (dict comprehension overwrite). Worth a test case or at least a documented caveat.
- `test_cli.py` diff adds a misplaced `from unittest import main` (not at top of file) and a `if __name__ == '__main__': main()` block that isn't needed given the existing `mothertongues/tests/run.py` test runner — ask the author to drop it, or drop it yourself on merge, to keep the test-running story singular.
- PR is ~2 years stale relative to `main`; do a final rebase and full CI run before merging even though GitHub reports it as mergeable.

---

## 3. Upgrade Angular (and Nx / Capacitor / Ionic)

**Why:** Root `mothertongues-UI/package.json` pins Angular `^17` (Nov 2023) and Nx `~18.2.4` — both several majors behind current, per the dependency audit. Capacitor `^6` is 2 majors behind. Node 16 (stated as the minimum in docs) has been EOL since Sept 2023.

**Steps:**
- Check current stable major versions for Angular, Nx, Ionic, and Capacitor at execution time (don't hardcode a target here — the gap will have grown further by the time this is actioned).
- Upgrade **one major version at a time** using `ng update` / `nx migrate`, running the full test + build suite between each hop — don't attempt to jump Angular 17 → latest in one step.
- Bump the Node engine requirement in docs/CI to a currently-supported LTS.
- Angular Material's MDC migration was left half-done (see step 6 — several `TODO(mdc-migration)` comments in both apps' stylesheets); finishing that migration should happen as part of this upgrade, not deferred further, since later Angular Material majors assume it's complete.
- Re-run both e2e suites (`mtd-mobile-ui-e2e`, `mtd-web-ui-e2e`) after the upgrade — but note (see step 6) they currently contain only unedited Cypress scaffolding, so "passing e2e" isn't a meaningful signal until those are actually written.
- Update `mothertongues-UI`'s own submodule pointer in the parent repo once the upgrade is committed and tagged.

**Verify:** `nx run-many -t build` succeeds for all four app/lib targets; `nx run-many -t test` green; manually smoke-test both `mtd-web-ui` and `mtd-mobile-ui` in a browser.

---

## 4. Extract the duplicated service layer into a shared library

**Why:** `packages/mtd-mobile-ui/src/app/data.service.ts` and `packages/mtd-web-ui/src/app/core/data.service.ts` are near-identical (96 vs. 101 lines, differing only in null-safety/type-alias cosmetics) — same story for `settings.service.ts` in both apps. Bug fixes currently have to be applied twice by hand, and nothing enforces that they are. This is real structural risk, independent of the Angular version.

**Steps:**
- Create a new Nx library (e.g. `packages/data-access`, alongside the existing `packages/search` and `packages/schemas` libraries) using the Angular-agnostic parts of both services as the starting point.
- Diff the two existing services line-by-line first to identify any behavioral divergence that isn't just incidental (i.e., check whether the differences are bugs in one app or intentional platform-specific behavior) before collapsing them.
- Migrate both apps to depend on the shared lib; delete the two duplicated files.
- Do this **after** the Angular upgrade (step 3) so you're not maintaining two copies through a major-version migration, and **before** or alongside the code-smell fixes in step 6 that touch these same services (e.g., the mobile `search.page.ts` duplicate-results TODO, the hardcoded `defaultLanguage` in `app.module.ts`).

**Verify:** both apps build and pass their existing unit tests against the shared lib; manually confirm search/settings behavior is unchanged in both apps.

---

## 5. Add Dependabot

**Why:** Neither repo (main or UI submodule) has any automated dependency or security scanning — the one existing security fix in the log (h11 bump, July 2025) was a manual, reactive PR. Given the multi-year dependency drift found across both repos, this is the highest-leverage, lowest-effort change and should land first so it starts surfacing update PRs while the rest of this plan is underway.

**Steps:**
- Add `.github/dependabot.yml` to the main `mothertongues` repo covering the `pip`/`uv` ecosystem (root) and `github-actions` ecosystem (workflow action versions).
- Add a separate `.github/dependabot.yml` to the `mothertongues-UI` repo (it's a distinct GitHub repo via the submodule) covering the `npm` ecosystem, scoped appropriately given the Nx monorepo's single root `package.json`.
- Set a sane cadence (weekly, grouped minor/patch updates) to avoid PR flood, and group major-version bumps separately so they don't get auto-merged.
- Consider enabling GitHub's Dependabot security alerts / CodeQL scanning at the same time — neither is currently configured.

**Verify:** confirm Dependabot opens its first batch of PRs within a few days on both repos.

---

## 6. Resolve lingering code smells

Split by codebase; each item below was found during the review and is small enough to knock out individually rather than needing its own phase.

### Python (`mothertongues/`)
- `mothertongues/processors/index_builder.py` — `InvertedIndex.__init__` has a mutable default argument (`keys_to_index: List[str] = [...]`); switch to `None` + assign inside `__init__`.
- `mothertongues/config/models.py` — two validators are stubs that just `return v` with no actual logic: `ResourceManifest.check_paths_are_pingable` (for `audio_path`/`img_path`) and `DataSource.check_data_is_parsable`. The `check_paths_are_pingable` one is directly related to issue #34 ("`audio_path` and friends are not paths") — these fields are typed `HttpUrl` but are almost always relative deployment paths in practice, causing unfriendly validation errors. Resolve by either implementing real validation or changing the type to something that reflects real usage (e.g. a relative-path-friendly type), and delete the dead stub either way.
- `mothertongues/config/models.py:303-315` — two `@root_validator` methods are commented out entirely with `# TODO: implement` / `# TODO: test`. Either implement them or delete the dead code; commented-out code shouldn't linger indefinitely.
- `mothertongues/config/models.py:175` — `# TODO: test, and consider adding the other 4 unicode blocks` in the combining-character removal regex; either add the coverage or drop the comment if it's not going to happen.
- `mothertongues/cli.py:244` — `# TODO: get more reasonable example data` for `new-project`'s sample data generation.
- `mothertongues/cli.py:254-255` — a workaround comment ("This adds a path that gets incorrectly resolved otherwise") papering over what sounds like a real path-resolution bug in `new-project`; worth root-causing rather than leaving the workaround.
- `mothertongues/parsers/__init__.py:91` — TODO about suppressing `IndexError` warnings behind a verbosity flag; decide and implement, since right now every malformed row logs unconditionally.
- Fold in issue #22 (unfriendly Pydantic `ValidationError` stack traces for `LanguageConfiguration`) and issue #27 (numbers should be cast to strings before validation fails) — both are the same root complaint as the stub validators above: Pydantic errors are currently surfaced raw to end users who are not Python developers. Worth a single pass at wrapping/catching `ValidationError` at the CLI boundary with human-readable messages.
- README's Contributing link points to a root-level `Contributing.md` that doesn't exist; the real file is `docs/developer/Contributing.md` — fix the link.
- Consider issue #43 (indexing on nested/optional fields currently requires duplicating the field at the top level) if there's appetite — it's a real design limitation, not just a smell, so may warrant its own follow-up rather than a quick fix.

**Deferred from the uv migration (2026-07-21):** while bumping the dependency floor, four packages were pinned back to their pre-migration versions rather than fixed in-place, to keep that migration scoped to just the Python/uv change. Each needs a real fix here:
- `jsf` pinned `<0.9.0` — 0.9+ fixes an upstream bug ([ghandic/jsf#80](https://github.com/ghandic/jsf/issues/80)) that `test_config_does_not_raise_unexpected_errors` was unknowingly relying on: the bug prevented the fuzzer from ever generating a `transducers` config, which was masking a real bug in `MTDictionary.transduce()` (`mothertongues/dictionary.py`) — a transducer whose `input_field` doesn't match an actual entry field raises a bare `KeyError` instead of the library's own `ConfigurationError`. Fix: wrap the `datum[transducer.input_field]` lookup in `transduce()` and raise `ConfigurationError` with a helpful message. Also, `test_no_file_config`'s assertion (`len(dictionary) + len(duplicates) == 2000`) is separately fragile — it assumes no generated entry is ever invalid/missing a required field, which newer `faker` versions violate more often; the fix needs to either sum `duplicates` + `missing_data` (not just `duplicates`, and NOT deduplicated via `set()` — `self.duplicates` intentionally isn't deduplicated, unlike `self.missing_data`, so a `set()` union of the two undercounts) or make `_generate_fake_data` guarantee schema-valid, non-falsy entries so only genuine duplicates get removed.
- `typer` pinned `<0.10.0` (with its `[all]` extra re-added, since modern typer no longer needs/has that extra — `rich` is now a core dependency, so it's also declared explicitly since our own code imports it directly) — 0.10+ changes Click's error-output rendering: error text moves from `result.stdout` to `result.output`, gets wrapped in a bordered panel, and parameter names are lowercased (`'language_config_path'` not `'LANGUAGE_CONFIG_PATH'`). Fix: update the 4 affected assertions in `test_cli.py` (`test_export_missingConfigFileArg`, `test_export_configFileDoesNotExist`, `test_export_missingOutputDirArg`, `test_export_outputDirDoesNotExist`) to check `result.output` and the new lowercase text, then bump `typer` back to current.
- `black` pinned `<23.0` and `mypy` pinned `<1.5.0` — bumping either surfaces pre-existing issues that predate the migration: black 24.x wants to reformat `mothertongues/tests/test_cli.py` (parenthesization style changed since 22.x — this is the file PR #33 touched; the reformat also fixes the isort import-order nit flagged during that PR's review, i.e. `from unittest import main` sorting with stdlib imports instead of after the third-party import), and mypy 1.5+ additionally catches `mothertongues/dictionary.py:224` (`parse()`'s return type) and `:370` (`create_inverted_index`'s argument type) — both pre-existing type mismatches, mypy 1.4.1 just doesn't infer them. Fix: run `black`/`isort` on `test_cli.py`, resolve the two mypy errors in `dictionary.py`, then bump both tools back to current and drop the version ceilings.

### UI (`mothertongues-UI/`)
- `packages/mtd-web-ui/src/app/pages/browse/browse.component.ts:164` — author-flagged `O(N²)` algorithm marked for rewrite.
- `packages/mtd-web-ui/src/app/pages/browse/browse.component.ts:142` — unexplained hardcoded pixel-offset hack ("Really unsure where those extra 6 pixels come from").
- `packages/mtd-web-ui/src/app/app.module.ts:72` — `defaultLanguage: 'en'` hardcoded instead of read from config; ties into the shared-service extraction in step 4.
- `packages/mtd-web-ui/src/app/core/route.animations.ts:68` — module-level variable used as a workaround, flagged by the author as needing a better approach.
- `packages/mtd-mobile-ui/src/app/search/search.page.ts:33` — author-flagged possible duplicate results when joining search results; this is a user-facing correctness bug, prioritize over the purely cosmetic items in this list.
- `packages/mtd-web-ui/src/app/pages/settings/settings-container.component.html:18` — `ngFor` used as a hack to work around missing `ngLet`; revisit once Angular's control-flow syntax (`@if`/`@for`/`@let`) is available post-upgrade (step 3), which directly obsoletes this workaround.
- Three stylesheets (`app.component.scss`, `word-modal.component.scss`, `nature-theme.scss`) have `TODO(mdc-migration)` markers from an incomplete Angular Material Design Components migration — fold into step 3's Angular upgrade as noted there.
- `packages/search/src/lib/factories.ts:89` — `// TODO: This isn't really right, not sure how we should tokenize though` — an admitted correctness gap in the *shared* search library used by both apps; prioritize this one since it affects both frontends.
- Both `mtd-mobile-ui-e2e` and `mtd-web-ui-e2e` contain only default Cypress scaffolding (a `cy.login(...)` call and greeting-text assertion that don't match the real apps) despite being wired into Nx. Either write real e2e coverage or remove the packages — "configured but empty" e2e is worse than no e2e because it's misleading.
- `liblevenshtein` (used by the search library) hasn't been published to npm since June 2022; evaluate whether it's still the right dependency or whether the weighted-Levenshtein implementation already in `packages/search/src/lib/weighted.levenstein.ts` makes it redundant.
- No `CHANGELOG.md` or `CONTRIBUTING.md` exists in the UI repo at all (the main repo at least has `docs/developer/Contributing.md`); add both now that active development is resuming.

**Deferred from the Angular/Nx migration (2026-07-22):** `packages/mtd-mobile-ui/src/app/app.component.spec.ts`'s `should have urls` test asserts on the `ng-reflect-router-link` DOM attribute, which is Ivy's dev-mode binding-debug reflection, not application behavior. As of the Angular 20 hop it's no longer being emitted for these bindings and the assertion fails (`getAttribute('ng-reflect-router-link')` returns `null`). Left failing rather than fixed in-place, to keep the version-bump migration scoped to just the version bump. Fix by asserting on something real instead (e.g. querying the rendered `routerLink`/`href` via `RouterTestingHarness`, or checking `ion-item[routerLink]` behavior) rather than relying on the removed debug attribute; `mtd-web-ui`'s equivalent tests don't have this problem since they don't probe `ng-reflect-*`.
- Also from this migration: `mtd-web-ui`'s production build (`nx build mtd-web-ui --configuration=production`) exceeds its 1MB initial bundle budget (now 1.98MB, up from 1.86MB pre-upgrade). Not caused by the migration and not currently enforced by CI (only `search` and `mtd-mobile-ui` are built in CI), but worth either raising the budget to reflect reality or trimming the bundle.
- `mtd-web-ui`'s `eslint.config.mjs` configures `@angular-eslint/component-selector`/`directive-selector` with `prefix: 'mothertongues'`, but every real component uses `mtd-*` selectors (e.g. `mtd-home`, `mtd-browse`) — this is pre-existing (not caused by the Nx/Angular upgrade), just newly visible now that `eslint.config.mjs` actually loads (it was previously broken entirely by a dead `plugin:@ngrx/recommended` reference to an uninstalled package, removed during this migration). Fix by changing the prefix to `'mtd'` to match reality, or renaming every selector — a deliberate choice, not a mechanical one.
- The Nx 21→23 hop (2026-07-22) disabled several `@angular-eslint`/`@typescript-eslint` rules workspace-wide (`prefer-on-push-component-change-detection`, `prefer-standalone`, `prefer-inject`, `no-empty-function`, `no-inferrable-types`, template `click-events-have-key-events`/`interactive-supports-focus`) that the angular-eslint v22 recommended preset newly enables by default; none were explicitly configured before, and fixing them means real refactoring (converting ~15+ components to standalone/OnPush, constructor DI to `inject()`, adding keyboard handlers for click-only interactions) rather than a version-bump mechanical change. Re-enable each and fix the underlying code as a deliberate follow-up, not all at once.
- Angular 22's tooling now declares a hard Node engine floor (`^22.22.3 || ^24.15.0 || >=26.0.0`); CI and docs were bumped to Node 22 as part of this migration (2026-07-22), but local dev machines still on Node 18/20 should upgrade — `npm install` only warns today, it doesn't block, so this can silently bite someone later.
- `@nxext/ionic-angular`'s release history has a permanent gap at the Nx-22-compatible line (21.0.0 → 23.0.0 directly, nothing in between), which is why the Nx 22 and 23 majors were combined into a single hop instead of stopping at 22 as originally planned. Not actionable — just documented here so future migrations aren't surprised by the same gap recurring.
