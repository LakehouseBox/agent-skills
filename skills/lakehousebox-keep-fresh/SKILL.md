---
name: lakehousebox-keep-fresh
description: Keep a LakehouseBox table filling itself - a scheduled SQL sink that reads a URL (an API, a feed, open data) on a schedule and commits the rows, or an ingest sink that takes JSON rows posted by a device, webhook or job with a send-only key - with upserts by key, rejects and lag to watch. Builds on the lakehousebox skill.
---

# Keep a table filled

The `lakehousebox` skill has the ways in and the general rules. A **sink** is a table's single committer: LakehouseBox
turns what arrives into Iceberg commits on a rolling policy, so nothing of the person's has to keep running.

## First decision: who sends the data

| the data | use | read next |
|---|---|---|
| sits at an http(s) URL LakehouseBox can fetch (an API, a JSON or CSV feed, open data) | a **scheduled SQL** sink: one DuckDB SELECT run on a schedule | [scheduled-sql](references/scheduled-sql.md) |
| is sent by something: a device, a webhook, a job | an **ingest** sink: one HTTPS intake, JSON arrays, a send-only key | [ingest](references/ingest.md) |
| arrives as files a device drops | an upload-only key, then imports: the `lakehousebox-load-data` skill | |

## Scheduled SQL: LakehouseBox fetches

On for every organisation on the free plan (two sinks; `lhbox usage --full` shows the limit `sql_sinks`). A catalog made
with `lhbox new` gets it when a person claims it: until then `lhbox sink preview --sql @query.sql` runs the query once (nothing written)
and create answers `403 claim_required`.

```sh
lhbox sink preview --catalog analytics --sql @quakes.sql --limit 3        # runs once, writes nothing: rows and types
lhbox sink create --catalog analytics --name docs_quakes --table docs_example.quakes \
    --sql @quakes.sql --every 1h --offset 7m --create-table --paused
lhbox sink run docs_quakes --wait                                          # one run now, until committed
lhbox sink runs docs_quakes                                                # state, rows, requests, bytes, errors
lhbox sink resume docs_quakes                                              # then it runs on its schedule (UTC)
```

- The query is **one DuckDB SELECT over http(s) sources**, run on LakehouseBox's executor; preview it first, create it
  `--paused`, run it once, then resume.
- **Sources that need an API key** take a *connection*, so the key never sits in the SQL
  ([scheduled-sql](references/scheduled-sql.md), "connections").
- Five minutes is the shortest schedule.

## Ingest sink: something sends

```sh
lhbox sink create --catalog garden --table sensors.readings --name garden_readings --save ~/garden-sink.json
lhbox sink send rows.json --send-key-file ~/garden-sink.json     # a test send as the producer: a JSON array of rows
lhbox sink get garden_readings                                                    # lag, last roll, rejects
```

- **The table must exist first**, and a format-version 2 table must be unpartitioned (version 3 may be partitioned by
  time). One sink per table.
- **The send key** can only send to that sink: give it to the producer, never the catalog's key. `--save` writes it
  to a file and never prints it.
- **Rows are committed on a roll** (every 300 s by default, sooner on size or inactivity), so a send is not a row yet:
  `lhbox sink get <sink>` shows what is waiting and what was rejected, with the reason.
- **One row per key, not per send**: `--key COL` makes each roll replace rows that share the key (an upsert); `lhbox
  sink dedupe` cleans a table that collected duplicates before the key was set.

## Describe it

A table that fills itself is read by people who never saw it created:

```sh
lhbox table document garden.sensors.readings --doc "One row per reading, posted by the gateway every 60 s"
```

## References

- [scheduled-sql](references/scheduled-sql.md): the query, connections for API keys, the table, the schedule, every
  command, the errors, the account page.
- [ingest](references/ingest.md): the send key and route, the roll, keys and upserts, rejects, costs.
- [ingest-geometry](references/ingest-geometry.md): points and shapes into a geometry column.
- [ingest-index-rules](references/ingest-index-rules.md): files in the file bucket that become rows of a table.
- [ingest-devices](references/ingest-devices.md): devices that cannot set headers, the device route, the mapping and presets.
