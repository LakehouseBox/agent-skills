---
name: lakehousebox-home-assistant
description: Move a Home Assistant's history into LakehouseBox and keep it flowing in - the recorder's last 10 days of states and its hourly long-term statistics into Iceberg tables (no account needed to start, lhbox new), then the person claims the catalog and every state change is posted once a minute by rest_command and one automation. Use when someone wants to keep, move, back up or query Home Assistant history, energy or sensor data for longer than the recorder keeps it. Builds on the lakehousebox and lakehousebox-keep-fresh skills.
---

# Home Assistant history on LakehouseBox

The person wants their Home Assistant history kept for years and answers about it. The whole recipe, every command
and its recorded output, is in [the instructions](references/instructions.md); this page is the order and the
decisions.

## Before you start

- **Find Home Assistant.** You need its configuration folder (`configuration.yaml`, `home-assistant_v2.db`) and a way
  to restart it: a container (`docker restart homeassistant`), a Core install's service, or on Home Assistant OS the
  Terminal & SSH add-on (`ha core restart`, the folder is `/config`). If the person told you where, use that. If you
  cannot reach it, say so and do what you can from a copy of the database file.
- **Check the recorder.** `recorder: db_url:` pointing at MariaDB or PostgreSQL means the history move (step 2) is not
  covered; skip to the live feed after the claim.

## The order

1. **Access** (instructions §1). A saved key (`lhbox whoami`) or a person at the keyboard (`lhbox login`): use that.
   Otherwise `lhbox new`, no account: a catalog named `lakehouse` you can write now. Tell the person it accepted the
   Terms for them, and that it is deleted after 72 hours unless they keep it.
2. **Move the history** (§2): snapshot the database with SQLite's backup (never the live file), run the SQL, import
   `ha.states` and `ha.statistics`. Leave out `device_tracker` (locations) unless the person said yes. Answer one
   real question from the data before anything else: that is what the person came for.
3. **The claim** (§3) is the one thing only the person can do: `lhbox claim`, give them the link and the code and
   tell them to pick **read and write** (the page offers read first), then `lhbox claim --resume --wait`. If it comes
   back `downgraded`, ask again with `lhbox login --new --level write --catalog lakehouse:write --no-wait`. If they
   are not around, stop here and tell them exactly that, with the deadline.
4. **The live feed** (§4–§6), after the claim: the sink, the secret, the `rest_command` and automation **exactly as
   written** (the payload survives integrations whose attributes are not JSON), the "uploads stalled" sensor, one
   restart, rows arriving, then fill the gap between the snapshot and the restart.

## Rules that save a retry

- Back up `configuration.yaml`, `secrets.yaml` and `automations.yaml` before you edit them, and check the YAML with
  Home Assistant's own check before the restart when you can (`ha core check`, or
  `hass --script check_config -c <folder>`).
- The sink's address is a password: it goes in `secrets.yaml`, never in the conversation or `configuration.yaml`.
- One restart, after all the YAML is in place: a new `rest_command` needs it, and it is the minute that posts
  every entity at once.
- Name the catalog from `lhbox catalog list` after the claim: a claim can rename it (`lakehouse_2`).
- The first question: `lhbox query "<sql>"` (runs on LakehouseBox's side, nothing saved on disk). A DuckDB secret saved
  with `lhbox duckdb --persist` before the claim holds the old key.
- Queries, energy per day and what each domain holds: instructions §7 and "Energy". A live dashboard: the person
  connects LakehouseBox in Claude and ticks the catalog ("See it on a dashboard"). Daily summaries on a schedule or a
  morning email: the `lakehousebox-hosted-agents` skill.
