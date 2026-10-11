# LakehouseBox for agents

The [LakehouseBox](https://lakehousebox.com) MCP connector and [Agent Skills](https://agentskills.io) in one plugin.
LakehouseBox keeps analytical data as Apache Iceberg tables, operated in Germany; the agent brings the compute.

- **The connector** (`https://mcp.lakehousebox.com/mcp`, read-only): find the tables you can read and how fresh they
  are, run read-only SQL on LakehouseBox's side, read files such as photos. It needs a LakehouseBox account (free); you
  approve it once in the browser.
- **The skills** teach the agent the service. A skill is a folder with a `SKILL.md` the agent loads when the task
  matches, plus references it opens only when needed.

| skill | layer | use it for |
|---|---|---|
| `lakehousebox` | base | connecting through the `lhbox` CLI, the connector or plain DuckDB; the rules that save a retry; reading anyone's public catalog with no account |
| `lakehousebox-portolan` | use-case | reading a Portolan geospatial catalog hosted on LakehouseBox (no account needed), or hosting one |

**Layers.** The base skill is what every LakehouseBox task needs. Workflow skills cover one capability of the
service; use-case skills cover an end-to-end job and build on the layers below. `catalog.json` has the graph.

Reading a public catalog needs neither an account nor the connector: the skills show the agent how to read it with
DuckDB. Everything else needs a LakehouseBox account.

## Install

| agent | install |
|---|---|
| Claude Code | `/plugin marketplace add lakehousebox/agent-skills`, then `/plugin install lakehousebox@lakehousebox` |
| Claude (claude.ai, Desktop) and Cowork | upload `dist/lakehousebox.zip` and `dist/lakehousebox-portolan.zip` as custom skills; add `https://mcp.lakehousebox.com/mcp` as a custom connector |
| Codex | `codex plugin marketplace add lakehousebox/agent-skills`, then `codex plugin add lakehousebox@lakehousebox` |
| Gemini CLI | `gemini extensions install https://github.com/lakehousebox/agent-skills` |
| any agent that reads skills from a folder | copy `skills/<name>/` into that agent's skills directory |

Not yet listed in the Claude or OpenAI (ChatGPT, Codex) plugin directories.

## Use

Ask for the task; the agent loads the skill when it matches. For example:

> What is in the public catalog portolan/madrid on LakehouseBox, and how many trees are within 100 m of Puerta del
> Sol?

> Load these CSV files into LakehouseBox and tell me how to add next month's.

## How the skills are kept true

The references under `skills/*/references/` are copies of the Markdown version of LakehouseBox's docs pages (each
names its live URL in its first lines), regenerated whenever a page changes. Everything else was written from
recorded runs against the live service: `runs/` holds them, with the script that repeats them. This repository is
published from LakehouseBox's own; issues are welcome here.

## License

[MIT](LICENSE).
