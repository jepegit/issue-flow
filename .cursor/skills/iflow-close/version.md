# Close step 2 — version bump

**Contents:** Publish-on-success label · Resolve the release strategy first · Bump levels · Choosing the level · Strategy: static version (uv) · Strategy: git-tag derived · Constraints

Read this to **bump the project version** before landing work (step 2 of `/iflow-close`) — either at a specific level, or with the default rule below when none is given. What "bump" means depends on the **release strategy**, so resolve that first.

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow agent version-plan [--bump <level>] --json`. It detects the
> strategy from `pyproject.toml`, reads the latest tag, does the PEP 440
> next-version arithmetic, and returns the exact commands — read-only, it
> only reports. The `this-project.md` release section
> still wins over its detection: when the payload says
> `brief_release_section: "filled"`, read the section and follow it. If the
> CLI is missing or errors, fall back to the manual steps below.


## Publish-on-success label

When the focus issue carries the **`publish`** label (exact, or `publish:<level>` / `publish:<version>`), treat it as a bump request unless the `ops` token is present (ops wins, no publish). Prefer `issue-flow agent publish-intent --issue <N> --json`:

- Bare `publish` → **patch**. `publish:minor` → that level. `publish:0.6.0` (or `v0.6.0`) → explicit target version.
- Exit code **2**, `logical: false`, or `conflict: true` → **stop and ask** (even under `yolo`): show `suggestion` and `notes`.
- An explicit bump token on the command line **wins** over the label; announce which one you used.
- Record `Publish label: <raw>` and the planned version in `issue<N>_status.md`.
- After the merge, the GitHub release is created on the default branch by `merge.md` (yolo) or `/iflow-cleanup`.


## Resolve the release strategy first

In order — stop at the first that answers:

1. **`.issueflows/04-designs-and-guides/this-project.md`** — if its **"Release & version bump"** section is filled in, follow it verbatim. It is the project's own documentation and beats every default below.
2. **Detect from `pyproject.toml`:**
   - `dynamic = ["version"]` under `[project]`, together with a tag-driven backend (`[tool.setuptools_scm]`, `hatch-vcs` in the build requires, `versioningit`, or similar) → **git-tag derived** strategy.
   - a static `version = "..."` under `[project]` → **static version (uv)** strategy.
3. **Neither** (no `pyproject.toml`, or no version at all) → **skip** the bump, explain why, and continue the rest of the flow (for example `/iflow-close`) without failing.

**Record what you learn (self-healing).** When the strategy came from detection or from the user explaining it — i.e. *not* from `this-project.md` — add or fill in the **"Release & version bump"** section of `.issueflows/04-designs-and-guides/this-project.md` with a short description of the strategy and the exact commands, so no future session has to rediscover it. The brief is user-owned and `issue-flow update` leaves it alone, so the note is durable.

## Bump levels (both strategies)

Every level below is allowed; the same table drives both strategies (examples from `0.4.1a4`):

| Level | Effect |
|---|---|
| `major` | `1.0.0` |
| `minor` | `0.5.0` |
| `patch` | `0.4.2` |
| `stable` | `0.4.1` — drop the pre-release/dev segment |
| `alpha` | `0.4.1a5` — next alpha pre-release |
| `beta` | `0.4.1b1` — promote/advance to beta |
| `rc` | `0.4.1rc1` — promote/advance to release candidate |
| `post` | `0.4.1a4.post1` — post-release |
| `dev` | dev release — **must** be paired with another component |

## Choosing the level

1. **The user named a level** (`patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`, `dev`) → use exactly that.
2. **The user asked to bump/release but gave no level** → apply the **pre-release-aware default**, based on the *current* version (static field, or latest tag):
   - current is an **alpha** (`aN`) → next alpha
   - current is a **beta** (`bN`) → next beta
   - current is a **release candidate** (`rcN`) → next rc
   - current is a **dev** release (`.devN`) → advance dev paired with the component being advanced (default `patch`)
   - current is a **stable** release (no pre-release segment) → `patch`
3. **Free-text intent** (e.g. "bugfix release", "promote to beta") → map to the matching level (bugfix → `patch`, "to beta" → `beta`); if genuinely ambiguous, ask once rather than guessing **major**.

## Strategy: static version (uv)

For a **Python + uv** project whose `pyproject.toml` has a `[project]` `version` field.

1. Run from the **project root** (the directory that contains `pyproject.toml`).
2. Use **only** `uv` with `--bump <level>`:

```bash
uv version --bump patch     # 0.4.1a4 -> 0.4.2
uv version --bump alpha     # 0.4.1a4 -> 0.4.1a5
uv version --bump minor --bump alpha   # combine: 0.4.1a4 -> 0.5.0a1
```

Tip: preview without writing using `uv version --dry-run --bump <level> --short`.

3. Afterwards: confirm the new version in `pyproject.toml` (or the `uv` output). When committing later, stage **`pyproject.toml`**; if **`uv.lock`** changed as well, stage it too.

## Strategy: git-tag derived

For projects whose built version comes from the **latest git tag** (setuptools-scm, hatch-vcs, versioningit, …). Here bumping means **planning a tag**, and the tag is created **after the PR merges**.

1. **Leave the version out of `pyproject.toml`** — the backend derives it.
2. **Find the current version**: latest tag via `git describe --tags --abbrev=0` (or `git tag --sort=-v:refname` and take the first). Keep the project's existing tag style (e.g. a leading `v`).
3. **Compute the planned next version** from the level table above (e.g. latest `v1.0.4a2` + `alpha` → planned `v1.0.4a3`).
4. **Create the tag only after the merge.** In a squash-merge world the squash commit replaces the issue-branch commit on the default branch, so a pre-merge tag would point at an orphan. So:
   - report the **planned tag** in the close output and record it in the issue's status file,
   - let `HISTORY.md` promotion use the planned version,
   - create the tag **after the merge**, standing on the updated default branch (this is offered by `/iflow-cleanup`, or happens right after the post-merge pull in a `yolo` close):

```bash
git tag v1.0.4a3
git push origin v1.0.4a3
# or, to also cut a GitHub release:
gh release create v1.0.4a3 --generate-notes
```

## Constraints

- Use the strategy's own tool; switch to `pip` or hand-edited versions only when that tool fails and the user agrees.
- Never silently jump release channels: without a named level, stay on the current pre-release channel (no alpha → stable, no major/minor bump).
- Tag-derived projects: never tag an issue-branch commit; the tag is created on the merged default branch only.
