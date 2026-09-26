# Issue #388: more knobs for automatically accepting and for continuing

Source: https://github.com/jepegit/issue-flow/issues/388

## Original issue text

I always answer yes to the agent for the first A1 step in the cleanup. Make it a knob.
Actually I always answer yet to the agent for the second step as well. Make it a knob. When running the cli command for updating issue-flow and it encounters that the second knob is on, issue a short warning.

Regarding knobs for automatically continue to next step, I have lost overview of what we have (I remember we have one for automatically planning). We should have knobs for all the steps. Remark that if we have a knob for automatically going to cleanup, we need the agent to be allowed to merge pull requests, or at least monitor if they are merged.
