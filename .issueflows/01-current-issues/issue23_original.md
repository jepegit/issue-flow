# Issue #23: conversion for teams using multiple coding environments

Source: https://github.com/jepegit/issue-flow/issues/23

## Original issue text

For teams, typically not everyone uses the same IDE or coding tools ("developer solution"). Using Git hooks, it should be possible to convert between the different formats or layouts (Cursor vs. Claude code, for example) conveniently and automatically. 

Plan:

1. Evaluate if there exists a common standard (search the web) that works for all solutions.
2. If not, suggest a common standard (the issuflow format)
3. Make sure that the codebase is refactored so that it can easily switch between solutions
4. Create a function and/or a CLI option for converting between solutions.
5. create a method that helps users to add git hooks    - triggered during pulling (convert to the developers' format)
    - triggered during push (or commit?) (Convert to the format decided by the team (where the `issueflow` format is one of the options)).
