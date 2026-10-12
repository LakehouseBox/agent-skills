# Reading a Portolan catalog hosted on LakehouseBox

No account and no credentials. Every SQL block below ran as written, in this order, in one DuckDB 1.5.6 session
with no account against the public catalog `portolan/madrid` on 2026-10-10; the times and answers quoted are from
that run (`runs/2026-10-10-portolan-reader.md` in the skills repository). On 2026-10-12 the secret gained `KEY_ID '', SECRET ''` (without them DuckDB signs with AWS variables some sandboxes set) and every block ran again as written, none failing (`runs/2026-10-12-portolan-reader.md`). Substitute your catalog's bucket, tables,
columns and coordinate system.

## Contents

- 1. Find the catalog and its files
- 2. From a collection to its table
- 3. DuckDB
- 4. Query templates
- 5. When something fails
- 6. What it needs from the network

## 1. Find the catalog and its files

By its LakehouseBox name, `<handle>/<catalog>`:

```sh
curl -s https://api.lakehousebox.com/v1/public/portolan/madrid \
  | jq '{bucket, files_url, agents: .agents_md.public_url, tables: [.tables[].table]}'
```

The full answer for `portolan/madrid` is 128 kB (51 tables with every column), so select fields as above. The fields:
`bucket` (the table bucket), `tables[]` (`table`, `root_url`, `columns`), `files_url` (the published folder of the
file bucket, where `catalog.json` is), `agents_md` (the catalog's AGENTS.md), and `recipes` (a ready-made DuckDB
script that creates one view per table). The same catalog has a page for people at
`https://lakehousebox.com/app/<handle>/<catalog>`.

The STAC root is `<files_url>catalog.json`, and every Portolan catalog and collection links its `AGENTS.md` (rel
`agents`) and `README.md` (rel `describedby`). The folder can be listed, S3-style:

```sh
curl -s "https://s3.lakehousebox.com/portolan--madrid--blobs?list-type=2&prefix=public/&delimiter=/"
```

Read the AGENTS.md files before writing SQL. Madrid's says, among other things, that the coordinate system is
EPSG:25830 (metres), that the geometry column is `geom` in 31 tables and `geometry` in 12, and that
`catalog.datasets` is an index with one row per dataset and curated questions whose SQL runs as is.

## 2. From a collection to its table

A vector collection hosted with its Iceberg table carries the STAC Iceberg extension. From
`vector/viviendas_turisticas/collection.json`:

```json
"iceberg:rest_prefix": "portolan--madrid",
"iceberg:table_id": "v3.viviendas_turisticas",
"iceberg:metadata_location": "https://s3.lakehousebox.com/portolan--madrid/v3/viviendas_turisticas/metadata/v7.metadata.json",
"iceberg:format_version": 3
```

The table's root is `s3://<iceberg:rest_prefix>/<namespace>/<table>`: here
`s3://portolan--madrid/v3/viviendas_turisticas`. Read the root. `metadata_location` is one fixed version: in this
run, `catalog.json`'s link to the index table named `v6.metadata.json` while the table was at `v8`. The old version
still read, but it is not the current data.

## 3. DuckDB

DuckDB 1.5.6 or newer (`pip install 'duckdb>=1.5.6'`; an old `duckdb` binary may sit earlier on `PATH`, so check
`duckdb --version`). Once per session:

```sql
INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;
CREATE SECRET lhbox_public (TYPE S3, ENDPOINT 's3.lakehousebox.com', URL_STYLE 'path', USE_SSL true, KEY_ID '', SECRET '');
```

The secret has no key: requests go unsigned. Do not add a made-up key pair, which the store refuses. The secret is
needed even when you pass a full `https://` metadata URL, because the metadata names its data files as `s3://` paths.

## 4. Query templates

### What the catalog holds

When the catalog has an index table, start there (madrid's is `catalog.datasets`, 51 rows; 1.7 s as the session's
first read):

```sql
SELECT id, kind, "table", n_features, crs
FROM iceberg_scan('s3://portolan--madrid/catalog/datasets')
ORDER BY n_features DESC LIMIT 5;
```

Otherwise list the tables from the public JSON (section 1) and `DESCRIBE` the ones you need:

```sql
DESCRIBE SELECT * FROM iceberg_scan('s3://portolan--madrid/v3/barrios');
```

`barrios` has `geom GEOMETRY('EPSG:25830')` and the bounding-box columns `xmin`, `ymin`, `xmax`, `ymax`.

### Which polygon holds a point

The person gives longitude and latitude; the table is in EPSG:25830. Convert the point once (`always_xy := true`
keeps longitude first):

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT b.nombre AS barrio, b.nomdis AS distrito
FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, p
WHERE b.geom && p.g AND ST_Contains(b.geom, p.g);
```

Puerta del Sol is in the barrio Sol, about 1 s.

### Everything within a distance

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT count(*) AS trees
FROM iceberg_scan('s3://portolan--madrid/v3/arbolado_alineacion_zonas_verdes') t, p
WHERE t.geom && ST_Buffer(p.g, 100) AND ST_DWithin(t.geom, p.g, 100);
```

31 trees within 100 m, out of 668,357. The `&&` test is what lets DuckDB skip row groups. Measured in fresh sessions,
counting HTTP requests:

| filter | requests | bytes read | time |
|---|---|---|---|
| `ST_DWithin` alone | 48 | 4.6 MB | 2.1 s |
| `&&` box, then `ST_DWithin` | 9 | 0.5 MB | 1.7 s |

The gap grows with the table. Always put the `&&` box first, then the exact test (`ST_DWithin`, `ST_Contains`,
`ST_Intersects`).

### The nearest few

Bound the search with a box larger than the answer is likely to be, then order by distance:

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT NOMBRE, DISTRITO, round(ST_Distance(a.geom, p.g)) AS metres
FROM iceberg_scan('s3://portolan--madrid/v3/albergues_emergencia') a, p
WHERE a.geom && ST_Buffer(p.g, 3000)
ORDER BY metres LIMIT 3;
```

Three emergency shelters, the nearest at 780 m, about 1.3 s. If fewer rows come back than you asked for, widen the
box.

### Count points per polygon

Madrid's curated question 3, tourist flats per barrio, as published in `catalog.datasets.questions`. The flats table
names its geometry column `geometry`, so the query renames it:

```sql
SELECT
  b.nombre AS barrio,
  COUNT(v.OBJECTID) AS n_viviendas_turisticas,
  SUM(v.UNIDADES_VUT) AS unidades_vut
FROM iceberg_scan('https://s3.lakehousebox.com/portolan--madrid/v3/barrios') b
LEFT JOIN (SELECT * EXCLUDE (geometry), geometry AS geom FROM iceberg_scan('https://s3.lakehousebox.com/portolan--madrid/v3/viviendas_turisticas')) v
  ON ST_Contains(b.geom, v.geom)
GROUP BY b.nombre
ORDER BY n_viviendas_turisticas DESC
LIMIT 5;
```

132 rows without the `LIMIT` (Embajadores first, with 69), 2 to 3 s. The `https://` form of the table root works too.

### Results in longitude and latitude

Transform on the way out, for a map or for the person:

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT b.nombre, ST_AsText(ST_Transform(ST_Centroid(b.geom), 'EPSG:25830', 'EPSG:4326', always_xy := true)) AS centroid
FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, p
WHERE b.geom && p.g AND ST_Contains(b.geom, p.g);
```

### Large tables

Aggregate and filter in SQL; do not pull raw rows from a table of hundreds of thousands of features into the
conversation. A plain count comes from the table's metadata without reading a data file:

```sql
SELECT count(*) AS trees FROM iceberg_scan('s3://portolan--madrid/v3/arbolado_alineacion_zonas_verdes');
```

## 5. When something fails

- **`No version was provided and no version-hint could be found … SET unsafe_enable_version_guessing = true`** on an
  `s3://` table root: the session has no keyless secret, or its secret carries a key pair. Create the secret of
  section 3. Do not turn version guessing on: the table has a version hint, DuckDB could not read it.
- **`NoSuchBucket` at `<bucket>.s3.amazonaws.com`** on an `https://` path: no secret in this session, so DuckDB
  looked for the data files at Amazon.
- **`InvalidAccessKeyId`**: the secret has a key pair in it; drop it and create the keyless one.
- **`failed to cast column "geometry" from type GEOMETRY(…) to BLOB`**: a table registered over existing GeoParquet
  files without rewriting them, whose schema says binary. Run `SET enable_geoparquet_conversion = false;` and read
  again (measured on a test catalog, 2026-09-29).
- **PyIceberg 0.12** cannot load a geometry column with a non-default coordinate system (EPSG:2913,
  EPSG:25830): read those tables with DuckDB.
- **A distance looks wrong by a factor of about 3.28**: the coordinate system is in feet (TriMet's EPSG:2913 is), not
  metres. Read the units in the AGENTS.md or the CRS definition.

## 6. What it needs from the network

Outbound HTTPS to `api.lakehousebox.com` (the catalog's JSON) and `s3.lakehousebox.com` (every table and file), and
to `extensions.duckdb.org` the first time each DuckDB extension is installed. A sandbox that blocks these cannot read
the catalog: say so to the person rather than answering without the data.
