# Run: a fresh agent with and without the skills, no account

**2026-10-10.** Claude Code 2.1.296, `claude -p`, default model, from an empty directory (no CLAUDE.md), with
`--strict-mcp-config` (no MCP server: the LakehouseBox connector could not help), `--max-turns 40`, permissions
bypassed inside that directory. `PATH` held a Python with DuckDB 1.5.6 first, then Homebrew, whose `duckdb` binary is
0.6.1. The only difference between the two runs: `--plugin-dir agent-skills` (the two skills of catalog 0.1.0).

The question, as the person asked it:

> I don't have a LakehouseBox account. Using the public Portolan catalog portolan/madrid on LakehouseBox, tell me which barrio Puerta del Sol (longitude -3.7038, latitude 40.4168) is in, and how many tourist flats (viviendas turísticas) that barrio has. Show the SQL you ran.

The right answer, computed beforehand (`runs/portolan_reader.py`'s session, the same SQL as reading.md): the barrio
**Sol**, with **8** tourist-flat records covering **14** units.

| | with the skills | without |
|---|---|---|
| answer | Sol; 8 records, 14 units | Sol; 8 records, 14 units |
| turns | 7 | 15 |
| time | 33 s | 109 s |
| cost (USD, as reported) | 0.27 | 0.61 |

What differed, from the two answers below:
- **Without the skills** the agent found the public JSON through the web (llms.txt, the public-catalogs page), found
  that the `duckdb` binary was 0.6.1, built a virtual environment with DuckDB 1.5.6 under `/tmp`, wrote the spatial
  join without an `&&` filter, and failed to read the catalog's curated questions.
- **With the skills** it went straight to the reader templates, used `&&` before `ST_Contains`, and cited the
  source, the licence and the snapshot date from the AGENTS.md.

Both reached the right answer: the public JSON, its recipes and the AGENTS.md already carry most of what an agent
needs. The skills made it cost less than half as much and take a third of the time.

## The answer with the skills

Puerta del Sol (lon −3.7038, lat 40.4168) is in the **barrio Sol**, in the **Centro** distrito. The catalog has **8 tourist flat records** in Sol, which add up to **14 tourist flat units** (`UNIDADES_VUT`).

I ran this with no account, in DuckDB 1.5.6 against the public `portolan/madrid` catalog. The tables use the EPSG:25830 coordinate system, so the queries convert your point into it first.

**Setup (once per session):**
```sql
INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;
CREATE SECRET lhbox_public (TYPE S3, ENDPOINT 's3.lakehousebox.com', URL_STYLE 'path', USE_SSL true);
```

**1. Which barrio holds the point:**
```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT b.nombre AS barrio, b.nomdis AS distrito
FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, p
WHERE b.geom && p.g AND ST_Contains(b.geom, p.g);
-- → Sol | Centro
```

**2. Tourist flats inside that barrio:**
```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g),
b AS (SELECT b.nombre, b.geom FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, p
      WHERE b.geom && p.g AND ST_Contains(b.geom, p.g))
SELECT b.nombre AS barrio, count(v.OBJECTID) AS n_viviendas_turisticas, sum(v.UNIDADES_VUT) AS unidades_vut
FROM b JOIN iceberg_scan('s3://portolan--madrid/v3/viviendas_turisticas') v
  ON v.geometry && b.geom AND ST_Contains(b.geom, v.geometry)
GROUP BY b.nombre;
-- → Sol | 8 | 14.0
```

In the flats table the geometry column is named `geometry`, not `geom` as in `barrios`.

**About the numbers:**
- This table holds the city's tourist flat records, which carry licence file and decree numbers. It is not a count of every listing on Airbnb or similar sites, so the real number in Sol is probably higher.
- The data is a snapshot of the city's layers as refreshed on 2026-09-21, copied into LakehouseBox on 2026-09-28. It is not updated automatically.

Source: Ayuntamiento de Madrid (SIGMA), CC-BY-4.0.

## The answer without them

Puerta del Sol (-3.7038, 40.4168) is in the barrio of **Sol** (barrio code 16), in the Centro district. The catalog has **8 tourist-flat registrations** there, covering **14 flats** in total (the table's `UNIDADES_VUT` column counts the flats in each registration).

### How I got in without an account
The catalog is public. LakehouseBox's metadata endpoint (`https://api.lakehousebox.com/v1/public/portolan/madrid`) lists the tables and gives a recipe that reads them directly from the storage, with no login or key. The installed DuckDB was 0.6.1, which is too old for these tables, so I put DuckDB 1.5.6 in a throwaway virtual environment under `/tmp`. The tables store geometry in EPSG:25830 (metric UTM coordinates), so the query converts your longitude/latitude to that system first.

### SQL I ran
```sql
INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;
-- keyless secret: unsigned requests against the public catalog
CREATE SECRET lhbox_public (TYPE S3, ENDPOINT 's3.lakehousebox.com', URL_STYLE 'path', USE_SSL true);

-- 1) Which barrio contains Puerta del Sol?
WITH sol AS (
  SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS pt
)
SELECT b.cod_disbar, b.nombre AS barrio, b.nomdis AS distrito
FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, sol
WHERE ST_Contains(b.geom, sol.pt);
-- → 16 | Sol | Centro

-- 2) Tourist flats inside that barrio (point-in-polygon)
WITH sol AS (
  SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS pt
),
barrio AS (
  SELECT b.nombre, b.geom
  FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, sol
  WHERE ST_Contains(b.geom, sol.pt)
)
SELECT barrio.nombre AS barrio,
       count(*)            AS registros_vut,
       sum(v.UNIDADES_VUT) AS unidades_vut
FROM iceberg_scan('s3://portolan--madrid/v3/viviendas_turisticas') v
JOIN barrio ON ST_Contains(barrio.geom, v.geometry)
GROUP BY barrio.nombre;
-- → Sol | 8 | 14.0
```

### Checks and caveats
- **The table is far from a full count.** `v3.viviendas_turisticas` has only 1,025 registrations (1,483 flats) for the whole city, so it is not a census of every tourist flat in Madrid. It is likely a subset with municipal licences only. Read the 14 as "what this dataset records", not the real number in Sol.
- **Sol is small, so the low number is plausible.** I counted the other barrios in Centro the same way: Embajadores 69 registrations, Universidad 40, Palacio 36, Cortes 15, Justicia 8, Sol 8.
- **I didn't use the catalog's own tourist-flats query.** The catalog includes a ready-made per-barrio query for this question, but my lookup for it returned nothing, so I couldn't compare against it.
- **Source:** Ayuntamiento de Madrid (SIGMA), CC-BY-4.0. LakehouseBox copied it on 2026-09-28 from a snapshot dated 2026-09-21, and the copy doesn't update automatically.

Sources:
- [LakehouseBox llms.txt](https://lakehousebox.com/llms.txt)
- [LakehouseBox public catalogs docs](https://lakehousebox.com/docs/public-catalogs/)
- [LakehouseBox MCP connector on Glama](https://glama.ai/mcp/connectors/com.lakehousebox/lakehousebox)
- [Portolan reference catalog (source.coop)](https://source.coop/portolan/portolan-pipeline/portolan-reference/main)

