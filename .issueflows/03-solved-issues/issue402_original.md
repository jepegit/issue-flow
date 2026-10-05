# Issue #402: create a mode that drives hands off

Source: https://github.com/jepegit/issue-flow/issues/402

## Original issue text

Create a issue-flow command that modifies skills so that a full feature can be implemented without intervention from user. It should be have like a drive flow - but without stopping for big issues. 

Example

> issue-flow mode "hands-off"

Issue-flow re-writes the skills

In agent harness (if issue exist): iflow drive 120

agent notifies that we are in hands-off mode
agent takes over and runs all steps and cycles. 

In agent harness (if issue does not exits): iflow drive <short description>
agent notifies that we are in hands-off mode
agent asks in grill-me mode about details of the feature

when all is explained, agent takes over and runs all steps and cycles.
