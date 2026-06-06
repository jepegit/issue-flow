# Issue #63: Pick next issue

Source: https://github.com/jepegit/issue-flow/issues/63

## Original issue text

Create a slash command for picking a suitable next issue to work with.

The command operates within several phases

**Phase 1: What issue to work with.**

1. If issues exist in 02-partly-solved-issues, pick from them. If not, we assume issues are stored at github, and we have to pick a relevant issue. Relevance could be based on what milestone they are targetting. Or if they are working with similar topics as the most recent issues worked on. Ask the user if the selected issue is OK. If not OK ask user for input. It would be good if the agent could list some candidates.
2. If the selected issue seems to be too involved, consider breaking it up into sub-issues. Suggest sub-issues, and create them (also on github). Then start working on the first sub-issue. The other sub-issues should be put in 02-partly-solved-issues.
3. If the user types "fix", create a single new issue (also on github) and assume that the issue is a general issue for fixing smaller things (like typos, a small bug, or similar).

**Phase 2: Create branch**

1. make sure we are "git clean", i.e. no un-commited changes etc. Then create a branch for the issue (branching from main (or master if main does not exist)) always using naming convention that github uses (starts with a number). Perform the /issue-init step automatically (you already know the issue number).

**Phase 3: Standard issue flow**

1. Continue working on the issue as normal. After issue-init the user will typically continue with /issue-plan. To make it more obvious for the user, ask the user if the user wants to continue with issue-plan.  
