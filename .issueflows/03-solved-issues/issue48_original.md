# Issue #48: Create options for issue flow modes

Source: https://github.com/jepegit/issue-flow/issues/48

## Original issue text

When installing or updating issue-flow, we should allow the user to select different modes.

One mode is the standard mode, assuming we would like to create pull requests and cleans up stuff, fixes history file, etc

Another mode could be a simple mode where only the markdown files are updated and moved to their correct position.

Task:

1. create the structure that allows having several modes. The user can then run `issue-flow init --mode simple` if he or she wants the simple mode.
2. make sure that `issue-flow update` respects the mode set. To change mode, the user must use issue-flow init.

Consider the need for adding additional structure to the code-base, for example having configuration files where we (the developers) can specify what each mode should contain (and add more modes later on).
