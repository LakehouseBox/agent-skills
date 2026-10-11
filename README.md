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
| `lakehousebox-load-data` | workflow | files into tables (CSV, Parquet, GeoParquet) in one commit, the file bucket, upload-only keys for devices |
| `lakehousebox-keep-fresh` | workflow | a table that fills itself: scheduled SQL from a URL, or an ingest sink a producer posts rows to |
| `lakehousebox-share` | workflow | access for colleagues and agents, publishing a catalog, AGENTS.md and table descriptions |
| `lakehousebox-hosted-agents` | workflow | a prompt LakehouseBox runs on a schedule next to the data (a preview) |
| `lakehousebox-portolan` | use-case | reading a Portolan geospatial catalog hosted on LakehouseBox (no account needed), or hosting one |

**Layers.** The base skill is what every LakehouseBox task needs. Workflow skills cover one capability of the
service; use-case skills cover an end-to-end job and build on the layers below. `catalog.json` has the graph.

Reading a public catalog needs neither an account nor the connector: the skills show the agent how to read it with
DuckDB. Everything else needs a LakehouseBox account.

## Install

| agent | install |
|---|---|
| Claude Code | `/plugin marketplace add lakehousebox/agent-skills`, then `/plugin install lakehousebox@lakehousebox` |
| Claude (claude.ai, Desktop) and Cowork | upload `lakehousebox.zip` and `lakehousebox-portolan.zip` from the [`dist` branch](https://github.com/lakehousebox/agent-skills/tree/dist) as custom skills; add `https://mcp.lakehousebox.com/mcp` as a custom connector |
| Codex | `codex plugin marketplace add lakehousebox/agent-skills`, then `codex plugin add lakehousebox@lakehousebox` |
| Gemini CLI | `gemini extensions install https://github.com/lakehousebox/agent-skills` |
| any agent that reads skills from a folder | copy `skills/<name>/` into that agent's skills directory |

Not yet listed in the Claude or OpenAI (ChatGPT, Codex) plugin directories.

## Where it connects

The connector, and the commands and DuckDB statements the skills give the agent, reach these services only:

| address | what goes there |
|---|---|
| `https://mcp.lakehousebox.com/mcp` | the connector: read-only tool calls (listing tables, read-only SQL, reading files) |
| `https://api.lakehousebox.com` | the `lhbox` CLI (sign-in approval, catalogs, tables, loading the person's files) and the description of a public catalog, read with no account |
| `https://catalog.lakehousebox.com` | the Iceberg catalog that DuckDB and other engines read and write tables through |
| `https://s3.lakehousebox.com` | the tables' and files' storage, read (and written, with an account) by DuckDB and the CLI |
| `https://lakehousebox.com/install.sh` | the CLI installer, downloaded once when the person installs it |
| `https://extensions.duckdb.org` | DuckDB's own extensions (iceberg, httpfs, spatial), downloaded the first time each is used |

The first four are LakehouseBox's services, run in Germany; the installer comes from LakehouseBox's website. Beyond these, a skill reaches only a source the person
names, such as the URL of a file to import. What LakehouseBox keeps, and for how long, is in its
[privacy policy](https://lakehousebox.com/legal/privacy/).

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
