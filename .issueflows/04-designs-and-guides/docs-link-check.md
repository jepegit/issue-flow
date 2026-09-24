# Docs link check

**Issues:** [#342](https://github.com/jepegit/issue-flow/issues/342),
[#344](https://github.com/jepegit/issue-flow/issues/344),
[#353](https://github.com/jepegit/issue-flow/issues/353) (epic #341).
**Status:** decided 2026-09-24.

## Context

The published docs had broken links:

- Read the Docs pages linked without `/en/latest/`, which returns 404.
- Links pointed into `.issueflows/` and `src/`, which are outside the published site.
- External URLs had rotted, including `iflow-graphify.net` in templates shipped to every project.

Nothing caught them before they reached the site or scaffolded projects.

## Decisions

### Versioned URLs

- Links to doc **pages** always use `https://issue-flow.readthedocs.io/en/latest/<page>/`.
- Only the bare root (`https://issue-flow.readthedocs.io/`) and `/llms.txt` may omit the prefix; both return 200.
- `site_url` in `zensical.toml` is the versioned base.
- `tests/test_doc_links.py` (essential) scans the README, `docs/` and `src/issue_flow/templates/` for unversioned page links and for `iflow-graphify.net`.

### Where docs may link

- Link to repo files outside `docs/` (design notes, source) with GitHub blob URLs (`https://github.com/jepegit/issue-flow/blob/main/…`). Never use relative `../` paths.
- Don't claim a design note exists "in scaffolded projects". `issue-flow init` seeds only `this-project.md`, `essential-tests.md` and `test-registry.md` (plus `python-quality-tools.md` at skill level `advanced`).

### CI check

The `docs-links` job in `.github/workflows/ci.yml` works in three steps:

1. `scripts/check_doc_links.sh --stage-only` builds the site with `uv run --group docs zensical build` and copies `site/` to `_linkcheck/en/latest/`. The copy is needed because `site_url` puts `/en/latest/` into root-relative links. Checking `site/` directly gives false 404s.
2. **Internal links** are checked with `lycheeverse/lychee-action@v2` using `--offline --root-dir _linkcheck --index-files index.html`. This step is **blocking**.
3. **External links** get the same check without `--offline`, with retries, accepting 429. This step is **non-blocking** (`fail: false`). Results go to the job summary, so a flaky third-party site never blocks a PR.

To run it locally: `scripts/check_doc_links.sh` (needs lychee on PATH).

## Alternatives considered

- **Check `site/` without staging.** Every root-relative link 404s because of the `/en/latest/` prefix.
- **Drop `/en/latest/` from `site_url`.** The built links would then not match how Read the Docs serves the site.
- **Make external links blocking.** Rejected as too flaky for PR gating. Review the job summary instead. The first run found 6 real dead links, fixed in #353.
- **A pytest-based link checker.** It would duplicate lychee and need network access in the test suite.

## Follow-ups

Check the external-link summary now and then, and file issues for real rot.
