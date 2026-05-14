# Issue #49: add graphify

Source: https://github.com/jepegit/issue-flow/issues/49

## Original issue text



Graphify is a python library (package name is graphifyy). It has several cli commands (see https://graphify.net/graphify-cli-commands.html)
The code lives on https://github.com/safishamsi/graphify

Tasks:

Figure out how graphify can be implemented in issue-flow. 

Implement graphify as a issue-flow feature (i.e. that we for example can run `issue-flow init --with graphify` (or `issue-flow update --with graphify`)), and that it then has graphify enabled. It could be that the markdown files (jina-templates, skills, rules) also needs to be updated. And graphify should also run when doing issue-flow init or update.

We should also add another cli command for issue-flow. It could be called 'build'. And that runs a graphify rebuilding of the graph.



