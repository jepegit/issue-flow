# Issue #174: skill for reviewing and labelling issues

Source: https://github.com/jepegit/issue-flow/issues/174

## Original issue text

We should help `issue-flow` users to assess how issues should be labelled. Currently, we only support "yolo" labels (if I remember correctly), but we anticipate we will allow for more labels in the future.

### Tasks

- Create/update the machinery for creating and editing issues, allowing for reviewing GitHub issues and adding labels.
- Create a skill for updating labels on all issues. The skill should be written so that it is extendable; the sub-skill supported so far will be examining issues and labeling suitable issues with the YOLO label (the actual YOLO label text is already configurable).
- Pick a good name for the skill (e.g. iflow-review). If the user does not supply a word in addition that defines what type of issue review the user wants, list the options and ask the user to pick (so far the only supported will be the yolo review).
