# Issue #47: how to handle dirty issueflows directories

Source: https://github.com/jepegit/issue-flow/issues/47

## Original issue text

We need a strategy for how to clean up dirty issueflow directories. This could be either done by python functions, or agents. We will need a detailed definiton of what dirty means.

Tasks

0. Define in detail what dirty means - i.e. what in the folders will make the issue flow run into inconsistencies and troubles (one example could be several issues in the current issue folder)
1. Create python functions and make them available through cli that can help users to clean up their issueflows directories. Possible actions could be (feel free to suggest other actions)
      - check if folders are dirty
      - keep only one issue in the current issues folder (01) and move others to 02
2. create skills allowing agents to perform similar operations
