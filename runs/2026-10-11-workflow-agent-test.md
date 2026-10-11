# Run: a fresh agent asks how to load and refresh data (the workflow skills)

**2026-10-11.** Claude Code 2.1.296, `claude -p` from an empty directory with `--plugin-dir agent-skills` (catalog
0.3.0: the base skill, the four workflow skills and Portolan) and `--strict-mcp-config` (no MCP server). No account;
the agent was told to run nothing, so this checks routing and the commands it gives, not a load.

> I export a CSV of sales every month. How do I get them into LakehouseBox as one table and add each new month, and
> how would a weather API feed keep another table filled every hour? Answer with the exact commands; do not run
> anything.

7 turns, 23 s, 0.17 USD as reported. It used
`lakehousebox-load-data` (`table import`, quoted glob, `--mode append`, `table_exists`, `columns_not_in_table`,
`import_outcome_unknown` with `lhbox table get` first, `table document`) and `lakehousebox-keep-fresh` (the per-organisation
switch and `403 not_enabled`, `sink preview`, a paused `sink create`, `sink run --wait`, `sink runs`, `sink resume`).
One loose phrase: it said a bad month "can be rolled back from `lhbox table get`'s snapshot list"; the list is there, the
rollback itself is a PyIceberg or Spark call (the skill says so).

## The answer

LakehouseBox has two separate tools for this. You load the sales CSVs yourself with `lhbox table import`. The weather table is a **scheduled SQL sink**, which LakehouseBox runs on a timer so nothing on your side has to stay running. I ran nothing. Swap in your own names: in the examples the catalog is `analytics`, sales goes to `analytics.sales.monthly` and weather to `analytics.weather.hourly`.

## Before you start

```sh
lhbox login        # tick "write" for the catalog
lhbox doctor       # checks DuckDB 1.5.5 or newer is on this machine
```

## 1. Monthly sales CSVs → one table

**First time** (creates the table from every CSV you already have, in a single commit):

```sh
lhbox table import analytics.sales.monthly 'exports/sales-*.csv'
lhbox table get analytics.sales.monthly        # check the schema, snapshots and row count
```

**Every month after that**, add the new file to the same table:

```sh
lhbox table import analytics.sales.monthly exports/sales-2026-10.csv --mode append
lhbox table get analytics.sales.monthly
```

Things to know:
- **Put quotes around the `*` pattern** so that `lhbox` reads all the files into one commit.
- **Use `--mode append` from the second month on.** Without it you get `table_exists` and exit code 2.
- **Append matches columns by name.** If a new export has a column the table doesn't have, it stops with `columns_not_in_table` before writing anything. Keep the export format the same.
- **If you get `import_outcome_unknown` (exit 5), run `lhbox table get` before anything else.** Running the append again without checking can add every row twice.
- **Every load is a snapshot.** A bad month can be rolled back from `lhbox table get`'s snapshot list, but only for a limited time.

Add a description for whoever reads the table later:

```sh
lhbox table document analytics.sales.monthly --doc "One row per sale, from the monthly CSV export, appended each month"
```

## 2. Weather API → a table filled every hour

Scheduled SQL sinks are switched on per organisation. Until yours is enabled, these commands answer `403 not_enabled`. To get it enabled, email hello@lakehousebox.com with your organisation's handle. `lhbox usage --full` shows your `sql_sinks` limit.

**`weather.sql`** must be one DuckDB SELECT over an http(s) source. This example uses Open-Meteo, which needs no API key:

```sql
SELECT
  current.time::TIMESTAMP     AS observed_at,
  current.temperature_2m      AS temperature_c,
  current.relative_humidity_2m AS humidity_pct,
  current.wind_speed_10m      AS wind_kmh,
  40.42 AS lat, -3.70 AS lon
FROM read_json('https://api.open-meteo.com/v1/forecast?latitude=40.42&longitude=-3.70&current=temperature_2m,relative_humidity_2m,wind_speed_10m')
```

Then:

```sh
lhbox sink preview --catalog analytics --sql @weather.sql --limit 3      # runs once, writes nothing; shows the rows and types
lhbox sink create --catalog analytics --name weather_hourly --table weather.hourly \
    --sql @weather.sql --every 1h --offset 5m --create-table --paused
lhbox sink run weather_hourly --wait                                     # one real run, waits until it's committed
lhbox sink runs weather_hourly                                           # state, rows, requests, errors per run
lhbox sink resume weather_hourly                                         # from now on it runs hourly (times are UTC)
lhbox table document analytics.weather.hourly --doc "Current weather for Madrid, fetched hourly from Open-Meteo"
```

Things to know:
- **Run the preview before creating the sink.** I wrote the SQL above from the API's documented response shape and haven't run it. The preview will show whether the columns come out right.
- **If your weather API needs a key, don't put it in the SQL.** LakehouseBox stores it as a *connection*. I couldn't open the skill's reference page that gives the exact connection commands, so I haven't listed them rather than guess. Ask me again, or check `lhbox sink --help`, if you need that.
- The shortest schedule is 5 minutes, so hourly is fine. `--offset 5m` makes it run at 5 past each hour.
- If you ever push weather rows yourself rather than having LakehouseBox fetch them, that's a different setup: an **ingest sink** with a send-only key. Ingest sinks also have `--key` for one row per key (an upsert).
