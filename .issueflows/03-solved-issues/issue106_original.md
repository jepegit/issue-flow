# Issue #106: chose flow details from issue labels

Source: https://github.com/jepegit/issue-flow/issues/106

## Original issue text

It is a bit tedious to always write slash commands. This issue tries to help a bit on that.

What if we can create flows that rely on issue labels? For example, we can say that if it has a label "yolo", then it can run the flow in yolo mode?
So, lets say the issue is a rather easy and small code change. It has the label "yolo". When we pick that issue, we run through it in yolo mode.

We can later expand on this. For now, let's wire it up. We need a config variable that controls if we allow this. It should default to allowing. We should also allow the label for yolo to be customizable. This should also be in config (and defaults to yolo). 

Since we are picking yolo as our first case, we should also use this opportunity to make sure that yolo flow "closes-the-loop" without any required input from the user. As far as I know, when running "/iflow-close" with yolo on it does not merge the pull request. But it should. It should also not stop and ask if it should update HISTORY.md. It should decide itself. And, it should, after switching to main (or master), do a pull.
