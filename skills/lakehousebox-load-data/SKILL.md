---
name: lakehousebox-load-data
description: Load data into LakehouseBox tables - CSV, Parquet, GeoParquet or anything DuckDB reads - as one commit per load, append the next batch of files, describe what was loaded, and keep files that are not tables (photos, rasters, archives) in the catalog's file bucket, including from devices that only drop files. Builds on the lakehousebox skill.
---

# Load data into LakehouseBox

The `lakehousebox` skill has the ways in and the general rules; this one is the path from files to tables. It
needs an account and a write credential on the catalog (`lhbox login`, the person ticks write).

## First decision: what the person has

| the person has | do | read next |
|---|---|---|
| CSV, Parquet or GeoParquet files on this machine or at an https URL | `lhbox table import <catalog>.<ns>.<table> <file>` | [import](references/import.md) |
| anything else DuckDB reads (JSON, a database attached next to the catalog) | one `CREATE TABLE … AS SELECT` in `lhbox duckdb` | [import](references/import.md), last section |
| files that are not tables: photos, PDFs, rasters, archives | the catalog's file bucket | [files](references/files.md) |
| a device, relay or partner that only drops files | an upload-only key for one folder | [uploaders](references/uploaders.md) |
| rows that keep arriving (a feed, a webhook, a sensor) | the `lakehousebox-keep-fresh` skill | |

## Import files: the default path

```sh
lhbox table import analytics.sensors.readings 'data/2026/*.parquet'                  # every file, ONE commit
lhbox table import analytics.sensors.readings 'data/2026-10/*.parquet' --mode append  # the next batch, one commit
lhbox table get analytics.sensors.readings                                             # schema, snapshots, rows
```

- **Quote globs**, so `lhbox` expands them and makes one commit; one statement per file is one commit per file.
- **DuckDB 1.5.5 or newer** must be on the machine that holds the files; `lhbox doctor` says which one it found.
- **Creating or appending.** `--mode create` (the default) stops with `table_exists` (exit 2) when the table is there:
  use `--mode append`. Append matches columns by name; a column the files have and the table lacks stops it
  (`columns_not_in_table`) before anything is written.
- **`import_outcome_unknown` (exit 5)**: run `lhbox table get` before anything else. Re-running an append blindly
  writes every row twice.
- **CSV** is detected by its extension. **GeoParquet**: add `--format-version 3` so geometry becomes a typed column
  with its coordinate system, rows in spatial order.
- **Required columns or identifier fields**: create the table first (`lhbox table create … --format-version 3
  --column id:long:required:identifier --column geom:geometry`, see the base skill), then import with `--mode append`.

## Describe what you loaded

The next agent, or the person's colleague, reads the table without the context you have now:

```sh
lhbox table document analytics.sensors.readings --doc "One row per reading, every 5 minutes, from …"
lhbox catalog agents-md analytics --set AGENTS.md          # the catalog's notes: units, joins, caveats
```

## A load went wrong

Every commit is a snapshot: `lhbox table get` lists them, and an older one can be read or made current again
([time-travel](references/time-travel.md); the rollback is a PyIceberg or Spark call today). Snapshots are kept for a
limited time, so roll back soon. To redo a table, `DROP TABLE` then import again (no `CREATE OR REPLACE`).

## Files that are not tables

The file bucket `<handle>--<catalog>--blobs` takes data files, photos, documents and archives; any other type is
refused with `415 UnsupportedFileType` ([files](references/files.md)). A device that must only write gets an
upload-only key for one folder, which can neither read nor list:

```sh
lhbox catalog uploader create garden --name camera-north --prefix photos/north/ --save ~/camera-north.json
lhbox catalog uploader revoke garden --uploader camera-north
```

## References

- [import](references/import.md): importing in detail: formats, create or append, format version, sort
  order and file size, GeoParquet, the account page's Import dialog, your own SQL.
- [files](references/files.md): what the file bucket takes, the error for the rest, what a public folder serves.
- [uploaders](references/uploaders.md): upload-only keys, folder design, expiring files, the FTP/SFTP drop box.
- [time-travel](references/time-travel.md): snapshots, how long they are kept, reading an older version, rolling back.
