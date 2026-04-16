# Issue #10: enhance issue-close with ability to bump version number

Source: https://github.com/jepegit/issue-flow/issues/10

## Original issue text

It would be cool if we could add ability for issue-close to also bump the version number. 

Add a skill for bumping version number:

The command should be like this for bumping the semantic versioning version number (this example is for bumping from e.g. 1.2.0 to 1.2.1)

`uv version --bump patch`

Add the ability for issue-close to bump version number if the user asks for it while issuing "/issue-close". The bump should be done before creating the final pull request (to make sure that the new version number is a part of the code when pulling)

Example:

`/issue-close bump`:  bumps patch

`/issue-close patch`:  bumps patch

`/issue-close bump minor`:  bumps minor

`/issue-close <some txt describing that the user would like bumping the version number>`:  bumps according to the description


