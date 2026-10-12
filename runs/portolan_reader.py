#!/usr/bin/env python3
"""Re-run lakehousebox-portolan/references/reading.md against the live service, with no account.

    python3 agent-skills/runs/portolan_reader.py > agent-skills/runs/<date>-portolan-reader.md

Runs every ```sh block with bash and every ```sql block, in order, in ONE DuckDB session (the reference says its
blocks run that way), printing each block, its answer and its time. Then the measurements the text quotes but no
block shows: the spatial filter with and without `&&`, in fresh sessions, counting HTTP requests; and two negative
controls (no secret, a made-up key) with the positive one beside them. Needs python3 with duckdb>=1.5.6 and jq."""
import re
import subprocess
import sys
import time
from pathlib import Path

import duckdb

REF = Path(__file__).resolve().parent.parent / "skills/lakehousebox-portolan/references/reading.md"
SECRET = "CREATE SECRET lhbox_public (TYPE S3, ENDPOINT 's3.lakehousebox.com', URL_STYLE 'path', USE_SSL true, KEY_ID '', SECRET '')"


def show(rows, cols, limit=8):
    out = [" | ".join(cols)]
    for r in rows[:limit]:
        out.append(" | ".join("NULL" if v is None else str(v)[:60] for v in r))
    if len(rows) > limit:
        out.append(f"… {len(rows)} rows")
    return "\n".join(out)


def main():
    text = REF.read_text(encoding="utf-8")
    print(f"# Run: {REF.name}, every block as written\n")
    print(f"Date (UTC): {time.strftime('%Y-%m-%d %H:%M', time.gmtime())}. DuckDB {duckdb.__version__}, "
          f"Python {sys.version.split()[0]}, no LakehouseBox account, no credentials.\n")
    con = duckdb.connect()
    failed = 0
    for lang, block in re.findall(r"```(sh|sql)\n(.*?)```", text, re.S):
        print(f"## {lang} block\n\n```{lang}\n{block.strip()}\n```\n")
        t = time.time()
        try:
            if lang == "sh":
                out = subprocess.run(["bash", "-c", block], capture_output=True, text=True, timeout=120)
                body = (out.stdout.strip()[:1200] or "(no output)") + (f"\nexit {out.returncode}" if out.returncode else "")
                failed += out.returncode != 0
            else:
                rel = None
                # a piece that is only comments is no statement; a statement after a comment line runs as written
                for stmt in [s for s in block.split(";") if re.sub(r"--[^\n]*", "", s).strip()]:
                    rel = con.sql(stmt)
                body = show(rel.fetchall(), rel.columns) if rel is not None else "(no result)"
        except Exception as e:  # noqa: BLE001 - every failure is reported, the run goes on
            body, failed = f"ERROR: {str(e)[:400]}", failed + 1
        print(f"```\n{body}\n```\n{round(time.time() - t, 2)} s\n")

    print("## Measured: the spatial filter with and without `&&` (fresh session each, HTTP requests counted)\n")
    point = "ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true)"
    table = "iceberg_scan('s3://portolan--madrid/v3/arbolado_alineacion_zonas_verdes')"
    cases = {
        "ST_DWithin alone": f"SELECT count(*) FROM {table} t WHERE ST_DWithin(t.geom, {point}, 100)",
        "&& box, then ST_DWithin": f"SELECT count(*) FROM {table} t WHERE t.geom && ST_Buffer({point}, 100) "
                                   f"AND ST_DWithin(t.geom, {point}, 100)",
    }
    print("| filter | rows | requests | MB read | seconds |\n|---|---|---|---|---|")
    for label, sql in cases.items():
        c = duckdb.connect()
        c.sql(f"LOAD iceberg; LOAD httpfs; LOAD spatial; {SECRET}")
        c.sql("CALL enable_logging('HTTP')")
        t = time.time()
        n = c.sql(sql).fetchone()[0]
        dt = round(time.time() - t, 2)
        reqs, mb = c.sql("SELECT count(*), round(sum(TRY_CAST(response.headers['Content-Length'] AS BIGINT))/1e6, 1) "
                         "FROM duckdb_logs_parsed('HTTP') WHERE request.type = 'GET'").fetchone()
        print(f"| {label} | {n} | {reqs} | {mb} | {dt} |")

    print("\n## Negative controls, with the positive one (every secret against every way of naming a table)\n")
    bad = ("CREATE SECRET bad (TYPE S3, KEY_ID 'made-up-key-id', SECRET 'made-up-secret', "
           "ENDPOINT 's3.lakehousebox.com', URL_STYLE 'path', USE_SSL true)")
    probes = {"s3:// root": "s3://portolan--madrid/v3/barrios",
              "https:// root": "https://s3.lakehousebox.com/portolan--madrid/v3/barrios"}
    for slabel, secret in [("keyless secret (positive)", SECRET), ("no secret", None), ("a made-up key pair", bad)]:
        for plabel, path in probes.items():
            c = duckdb.connect()
            c.sql("LOAD iceberg; LOAD httpfs;")
            if secret:
                c.sql(secret)
            try:
                n = c.sql(f"SELECT count(*) FROM iceberg_scan('{path}')").fetchone()[0]
                body = f"{n} rows"
            except Exception as e:  # noqa: BLE001
                body = "ERROR: " + " ".join(str(e).split())[:240]
            print(f"- {slabel}, {plabel}: {body}")
    print(f"\n{failed} block(s) failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
