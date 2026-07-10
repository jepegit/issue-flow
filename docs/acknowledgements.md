# Acknowledgements

issue-flow builds on and takes inspiration from other people's open-source work.
Thanks to the authors and communities behind these projects:

| Project | How issue-flow uses it | License |
| --- | --- | --- |
| [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | Inspiration for the bundled `caveman` Agent Skill (terse, token-greedy response style). Our version is a trimmed adaptation — full intensity only, English only. | [MIT](https://github.com/JuliusBrussee/caveman/blob/main/LICENSE) |
| [mattpocock/skills](https://github.com/mattpocock/skills) | Matt Pocock's `grill-me` skill inspired the bundled `grill-me` Agent Skill (relentless planning interview). Our version is adapted to issue-flow's planning workflow, feeding conclusions into `issue<N>_plan.md`. | [MIT](https://github.com/mattpocock/skills/blob/main/LICENSE) |
| [safishamsi/graphify](https://github.com/safishamsi/graphify) (`graphifyy` on PyPI) | Powers the optional knowledge-graph integration (`issue-flow graphify`, `graphify-out/`). Installed separately and invoked as an external tool. | [MIT](https://github.com/safishamsi/graphify/blob/main/LICENSE) |
| [Typer](https://github.com/fastapi/typer) | The `issue-flow` command-line interface. | MIT |
| [Rich](https://github.com/Textualize/rich) | Formatted terminal output during `init` / `update`. | MIT |
| [Jinja2](https://github.com/pallets/jinja) | Renders the scaffolded skill, command, and rules templates. | BSD-3-Clause |
| [tomlkit](https://github.com/python-poetry/tomlkit) | Comment-preserving round-trips of `.issueflows/config.toml`. | MIT |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Loads `ISSUEFLOW_*` settings from a project `.env`. | BSD-3-Clause |
| [Zensical](https://github.com/zensical/zensical) | Builds this documentation site (from the Material for MkDocs team). | MIT |

Using or drawing on another project that should be listed here? Open a
[PR or issue](https://github.com/jepegit/issue-flow/issues) to add a row.
