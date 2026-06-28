# Issue #24: utilize the tools folder and status files better

Source: https://github.com/jepegit/issue-flow/issues/24

## Original issue text

Currently, it seems like the agents never chose to add tools into 00-tools. We should add some text in the slash commands ala "check if suitable tool exist in 00-tools" and "have you developed something that can be a tool? add it into 00-tools and make it easy for agents to understand if they should use it".


It also does not create the _status.md file until after we have issued `/issue-close`. This is not what we want. We want the agents to keep updating the file during working on the issue (so that it can use it when iterating also before we close the issue).
