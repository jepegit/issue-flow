# Issue #168: fix GitHub Linguist skew

Source: https://github.com/jepegit/issue-flow/issues/168

## Original issue text

In my opinion, the repositories under "issue-flow" should have a .gitattributes to prevent skewing the GitHub Linguist.


Example `.gitattributes` file:


```
# GitHub Linguist: keep language stats focused on library source.
# Without this, graphify-out/graph.html might dominates as HTML.

graphify-out/** linguist-generated
docs/** linguist-documentation
tests/** linguist-documentation
.issueflows/** linguist-documentation
dev/** linguist-documentation
scripts/** linguist-documentation

# Cross-platform line endings for shell helpers
.aliases     text eol=lf
*.sh         text eol=lf
*.lock       text eol=lf
```
