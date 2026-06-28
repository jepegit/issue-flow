# Issue #96: cli command for creating config.toml file

Source: https://github.com/jepegit/issue-flow/issues/96

## Original issue text

Add a cli command for handling the config.toml file, and in particular for creating a config.toml file.

It should create the file (if missing) in the appropriate folder (.issuflows usually) and populate with values for .env if it exists. If not, the default (as defined by issue-flow itself) should be added. Afterwards, a description of how to manually edit the config file later should be given.

I think it is best to give it its own "namespace", e.g. issue-flow config add
