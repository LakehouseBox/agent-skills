# Run: a fresh agent moves a Home Assistant's history, with no account, and switches on the live feed

**2026-10-12**, against production (`api.lakehousebox.com`). Claude Code 2.1.296, `claude -p` from an empty directory
with `--plugin-dir agent-skills` and `--strict-mcp-config` (no MCP server), its own `lhbox` credentials file, no
LakehouseBox account. Home Assistant 2026.2.3 (Python 3.13) ran on the same machine with the default SQLite recorder and
stand-in devices: template sensors for solar, house and car-charger power, the integration helper's kWh meters (so
real long-term statistics), inside and outside temperature, a light and a blind toggled by an automation. The prompt,
the founder's sentence plus where Home Assistant was:

> Check out the LakehouseBox skill for Home Assistant, and get me started moving my Home Assistant history data to
> LakehouseBox.
>
> (Home Assistant runs on this machine. Its configuration folder is <folder> and <script> restarts it. I'm not around
> for the next while, so do as much as you can on your own and tell me exactly what you need from me at the end.)

## Baseline, before the skill existed

11 turns, 57 s, 0.15 USD. With only the base and load-data skills the agent improvised: it chose `lhbox login` although
nobody was there to approve it, exported the recorder to Parquet on its own (a safe copy, then states and statistics),
loaded nothing, and ended asking for a sign-in.

## With the skill: §1–§3 (no account, the history, the claim)

17 turns, 88 s, 0.29 USD. The agent loaded `lakehousebox-home-assistant` first, ran `lhbox new` (catalog `lakehouse`,
no account), snapshotted the database with SQLite's backup, ran the instructions' SQL and imported
`lakehouse.ha.states` (310 rows, 40 entities) and `lakehouse.ha.statistics` (14 hourly rows), left `device_tracker`
out and said so, read both tables back, and stopped at `lhbox claim` with the link, the code and the deletion time.
An earlier attempt the same morning stopped at `anonymous_not_enabled` before agent signup was switched on.

What it changed in the instructions: the first question now uses `lhbox query` (the agent had saved a DuckDB secret with
`--persist` to ask it, and that secret went stale at the claim); the statistics' `name` is empty for most entities, so
entities are named by `statistic_id`; DuckDB's Python module needs `pytz`.

## The claim, and the live feed (§3–§6)

The founder claimed the catalog into their organisation and left the page's default, read: `lhbox claim --resume --wait`
answered `"downgraded": true` and `lhbox sink create` was refused (`required: write`). The account page cannot raise a
claim's key (it is a connection, not an organisation token, so Grant access does not list it). The agent asked again
with `lhbox login --new --level write --catalog lakehouse:write --no-wait`; the founder approved with write. Then, 10
turns, 454 s, 0.56 USD: `lhbox sink create … --device --save ha-sink.json`, the address in `secrets.yaml`, the
`rest_command`, the automation (into the existing `automations.yaml`), the `input_datetime` and the uploads-stalled
sensor, `check_config`, one restart, and `lhbox sink get`: 81 rows in 6 batches, 0 rejected, committed. The gap fill
found 0 rows, correctly: the test Home Assistant had been stopped by the operator between the snapshot and the restart.

What it changed: the claim step says "pick read and write" and gives the way back when it comes out read.

## The dashboard

The founder connected LakehouseBox in Claude (claude.ai) and asked for "a dashboard of my home: solar, house and car
energy per day, and inside vs outside temperature, from the lakehouse catalog". The first answer found only
`madrid_data`: the connector reached only the catalog ticked when it was approved. Once the founder's connection
reached `lakehouse` (how it was changed is not recorded here), Claude
built a live "Home energy & temperature" dashboard (energy per day, inside vs outside temperature, tables by day), whose
queries run on the connector with the viewer's own access. Screenshot: the guide's `img/dashboard.webp`.
