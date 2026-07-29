# Issue #216: possible bug in gitutils

Source: https://github.com/jepegit/issue-flow/issues/216

## Original issue text

An agent got this error message:

```bash
cd /c/scripting/cellpy-workspace/cellpy && git fetch --prune && git switch master && git pull --ff-only && git switch -c 676-native-header-docs && git status -sb && issue-flow agent capture 676 -C /c/scripting/cellpy-workspace/cellpy --repo jepegit/cellpy && issue-flow agent sweep --except 676 -C /c/scripting/cellpy-workspace/cellpy
Your branch is up to date with 'origin/master'.
Switched to branch 'master'
Already up to date.
Switched to a new branch '676-native-header-docs'
## 676-native-header-docs
Exception in thread Thread-1 (_readerthread):
Traceback (most recent call last):
  File "C:\Users\jepe\AppData\Local\miniconda3\Lib\threading.py", line 1044, in _bootstrap_inner
    self.run()
    ~~~~~~~~^^
  File "C:\Users\jepe\AppData\Local\miniconda3\Lib\threading.py", line 995, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\jepe\AppData\Local\miniconda3\Lib\subprocess.py", line 1615, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Users\jepe\AppData\Local\miniconda3\Lib\encodings\cp1252.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 1912: character maps to <undefined>
┌───────────────────── Traceback (most recent call last) ──────────────────────┐
│ C:\scripting\issue-flow\src\issue_flow\cli.py:801 in agent_capture           │
│                                                                              │
│   798 │   from issue_flow.agent import run_capture                           │
│   799 │                                                                      │
│   800 │   raise typer.Exit(                                                  │
│ > 801 │   │   code=run_capture(project_dir, _console, number, repo, force,   │
│       json_output)                                                           │
│   802 │   )                                                                  │
│   803                                                                        │
│   804                                                                        │
│                                                                              │
│ C:\scripting\issue-flow\src\issue_flow\agent.py:1892 in run_capture          │
│                                                                              │
│   1889 │   │   if owner_repo is not None:                                    │
│   1890 │   │   │   resolved_repo = f"{owner_repo[0]}/{owner_repo[1]}"        │
│   1891 │                                                                     │
│ > 1892 │   data = gitutils.gh_issue_view(number, project_root,               │
│        resolved_repo)                                                        │
│   1893 │   if data is None:                                                  │
│   1894 │   │   msg = (                                                       │
│   1895 │   │   │   f"could not fetch issue #{number}"                        │
│                                                                              │
│ C:\scripting\issue-flow\src\issue_flow\gitutils.py:246 in gh_issue_view      │
│                                                                              │
│   243 │   ]                                                                  │
│   244 │   if repo:                                                           │
│   245 │   │   argv += ["--repo", repo]                                       │
│ > 246 │   out = _stdout(argv, cwd)                                           │
│   247 │   if out is None:                                                    │
│   248 │   │   return None                                                    │
│   249 │   try:                                                               │
│                                                                              │
│ C:\scripting\issue-flow\src\issue_flow\gitutils.py:81 in _stdout             │
│                                                                              │
│    78 │   result = _run(argv, cwd)                                           │
│    79 │   if result is None or result.returncode != 0:                       │
│    80 │   │   return None                                                    │
│ >  81 │   return result.stdout.strip()                                       │
│    82                                                                        │
│    83                                                                        │
│    84 def current_branch(cwd: Path) -> str | None:                           │
└──────────────────────────────────────────────────────────────────────────────┘
AttributeError: 'NoneType' object has no attribute 'strip'

```

Is this a bug in issue-flow or is it something with the python setup at that machine? If a bug, we should fix it.

## Comments (curated summary)

- **Additional tasks**:
  - Also teach agents (skills/docs) that `gh repo view` takes the repo as a **positional** arg (`gh repo view owner/repo`), not `--repo` — agents hit `unknown flag: --repo` on that command.
- **Clarifications / constraints**:
  - Second report is agent CLI misuse, not a `gitutils` failure — still in scope as guidance so agents stop repeating it.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-25._
