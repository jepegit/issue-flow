# Issue #213: option for using essential tests

Source: https://github.com/jepegit/issue-flow/issues/213

## Original issue text

In a large codebase, there might be a huge amount of tests (especially now as agents make writing tests "free"). A paradigm for handling large test suites is to label tests as "essential" and run only those in CI. The full tests suite can be set to run on a schedule (daily/weekly) and as a part of the release process. I use this paradigm.

One way issue-flow can help here is to evaluate which tests should be labelled "essential" for a given issue we are working on. The action must be configurable (not everyone would like this feature). When to run the "essential" review, is maybe also something that should be configurable. We might also allow iflow-doctor to do a full sweep and review, so that the work in the issue does not take too long (reviewing all tests each time we run an issue-flow would be very demanding on the tokens and time). 

To be able to use this paradigm, the repo should have two GitHub workflow files (minimum), one running only essential tests (e.g. "ci.yml") and one running the full test suite (e.g. "ci-scheduled.yml"). Maybe issue-flow can help creating these.

One idea; maybe we should add a document in .issueflows (04-design-and-guides?) that keeps some kind of track of tests and their status? For example with information like if the test should always be essential, what code the test tests (maybe with some help by graphify), issue it was created for testing, recommendations for turning it off or not afterwards, and maybe more. During a regular flow, it gets updated with the new tests made. And the doctor can go through and review/update when needed (we dont want the "essential" suite to be too large, and there might be tests made that were not a part of a issue flow).

Feel free to suggest improvements to this issue/plan.

## Comments (curated summary)

- **Clarifications / constraints**: Assume pytest for now. `test_runner` may be configurable later, but v1 only accepts `"pytest"`; anything else → unsupported + invite contribution.

_Note: interpretive summary of comment thread, not verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-24._
