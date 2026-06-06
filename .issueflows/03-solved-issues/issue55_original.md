# Issue #55: agent tab improvement

Source: https://github.com/jepegit/issue-flow/issues/55

## Original issue text

Update issue-init.md step 2:

```
2. Fetch issue data using GitHub CLI (explicit repo if needed). Include comments so they can be triaged into the original file:
   - `gh issue view <N> --repo owner/repo --json title,body,url,number,comments`
   - `comments` returns an array where each entry has at least `author.login`, `body`, and `createdAt`.
   - Confirm resolved `owner/repo` to the user.
   - Change the chat/agent tab title to reflect the issue topic on the form "Issue <issue number> <short description of issue>", for example "Issue 74 cell info".

```

Here, the last bullet point is the new edit.
