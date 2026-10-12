# Run: reading.md, every block as written

Date (UTC): 2026-10-12 20:57. DuckDB 1.5.6, Python 3.14.7, no LakehouseBox account, no credentials.

## sh block

```sh
curl -s https://api.lakehousebox.com/v1/public/portolan/madrid \
  | jq '{bucket, files_url, agents: .agents_md.public_url, tables: [.tables[].table]}'
```

```
{
  "bucket": "portolan--madrid",
  "files_url": "https://s3.lakehousebox.com/portolan--madrid--blobs/public/",
  "agents": "https://s3.lakehousebox.com/portolan--madrid--blobs/AGENTS.md",
  "tables": [
    "catalog.datasets",
    "raster.mdo_orientacion",
    "raster.mdo_pendiente_porcentaje",
    "scratch.barrios_t",
    "v3.albergues_emergencia",
    "v3.ambitos_vigentes_2026",
    "v3.aparcamientos_disuasorios",
    "v3.aparcamientos_publicos",
    "v3.arbolado_alineacion_zonas_verdes",
    "v3.arbolado_singular",
    "v3.areas_acusticas_2018",
    "v3.barrios",
    "v3.bic_declarados",
    "v3.bosque_metropolitano_itinerarios",
    "v3.centros_sociosanitarios",
    "v3.centros_vigilantes_del_aire",
    "v3.colegios_plan",
    "v3.edificabilidad_parcelas_2026",
    "v3.edificios_alturas",
    "v3.edificios_protegidos",
    "v3.edificios_suspension_licencias",
    "v3.elementos_urbanos_singulares",
    "v3.establecimientos_comerciales_protegidos",
    "v3.etapas_desarrollos_sureste",
    "v3.expedientes_planeamiento_ad",
    "v3.infraestructura_ciclista",
    "v3.normas_zonales",
    "v3.parques_jardines_interes",
    "v3.parques_viveros",
    "v3.pgoum97_alineaciones",
    "v3.
```
0.7 s

## sh block

```sh
curl -s "https://s3.lakehousebox.com/portolan--madrid--blobs?list-type=2&prefix=public/&delimiter=/"
```

```
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Name>portolan--madrid--blobs</Name><Prefix>public/</Prefix><MaxKeys>1000</MaxKeys><Delimiter>/</Delimiter><IsTruncated>false</IsTruncated><Contents><Key>public/AGENTS.md</Key><ETag>&#34;442efe52c22d85db6939f08358d2cc64&#34;</ETag><Size>6144</Size><StorageClass>STANDARD</StorageClass><LastModified>2026-10-05T05:26:25Z</LastModified></Contents><Contents><Key>public/README.md</Key><ETag>&#34;06fa619bc5bdeb023e3d66a9b4381480&#34;</ETag><Size>755</Size><StorageClass>STANDARD</StorageClass><LastModified>2026-10-05T05:26:25Z</LastModified></Contents><Contents><Key>public/catalog.json</Key><ETag>&#34;79ab9d8635a34dbdffa02b02d14fcbaa&#34;</ETag><Size>1571</Size><StorageClass>STANDARD</StorageClass><LastModified>2026-10-05T05:26:25Z</LastModified></Contents><CommonPrefixes><Prefix>public/raster/</Prefix></CommonPrefixes><CommonPrefixes><Prefix>public/vector/</Prefix></CommonPrefixes><KeyCount>5</KeyCount></ListBucketResult>
```
0.2 s

## sql block

```sql
INSTALL iceberg; LOAD iceberg; INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial;
CREATE SECRET lhbox_public (TYPE S3, ENDPOINT 's3.lakehousebox.com', URL_STYLE 'path', USE_SSL true, KEY_ID '', SECRET '');
```

```
Success
True
```
0.17 s

## sql block

```sql
SELECT id, kind, "table", n_features, crs
FROM iceberg_scan('s3://portolan--madrid/catalog/datasets')
ORDER BY n_features DESC LIMIT 5;
```

```
id | kind | table | n_features | crs
arbolado_alineacion_zonas_verdes | vector | v3.arbolado_alineacion_zonas_verdes | 668357 | EPSG:25830
red_transporte_streets | vector | v3.red_transporte_streets | 545400 | EPSG:25830
edificios_alturas | vector | v3.edificios_alturas | 490740 | EPSG:25830
usos_suelo_parcelas | vector | v3.usos_suelo_parcelas | 39999 | EPSG:25830
pgoum97_alineaciones | vector | v3.pgoum97_alineaciones | 29069 | EPSG:25830
```
1.73 s

## sql block

```sql
DESCRIBE SELECT * FROM iceberg_scan('s3://portolan--madrid/v3/barrios');
```

```
column_name | column_type | null | key | default | extra
OGC_FID | BIGINT | YES | NULL | NULL | NULL
fid | INTEGER | YES | NULL | NULL | NULL
nomdis | VARCHAR | YES | NULL | NULL | NULL
cod_dis_tx | VARCHAR | YES | NULL | NULL | NULL
barrio_may | VARCHAR | YES | NULL | NULL | NULL
coddis | VARCHAR | YES | NULL | NULL | NULL
cod_bar | VARCHAR | YES | NULL | NULL | NULL
nombre | VARCHAR | YES | NULL | NULL | NULL
… 21 rows
```
0.96 s

## sql block

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT b.nombre AS barrio, b.nomdis AS distrito
FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, p
WHERE b.geom && p.g AND ST_Contains(b.geom, p.g);
```

```
barrio | distrito
Sol | Centro
```
1.03 s

## sql block

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT count(*) AS trees
FROM iceberg_scan('s3://portolan--madrid/v3/arbolado_alineacion_zonas_verdes') t, p
WHERE t.geom && ST_Buffer(p.g, 100) AND ST_DWithin(t.geom, p.g, 100);
```

```
trees
31
```
1.68 s

## sql block

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT NOMBRE, DISTRITO, round(ST_Distance(a.geom, p.g)) AS metres
FROM iceberg_scan('s3://portolan--madrid/v3/albergues_emergencia') a, p
WHERE a.geom && ST_Buffer(p.g, 3000)
ORDER BY metres LIMIT 3;
```

```
NOMBRE | DISTRITO | metres
OAC LÍNEA MADRID | CENTRO | 780.0
Centro Deportivo Municipal La Cebada (antigua La Latina) | CENTRO | 841.0
ESCUELA DE MÚSICA MARÍA DOLORES PRADERA | CENTRO | 885.0
```
1.33 s

## sql block

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

```
barrio | n_viviendas_turisticas | unidades_vut
Embajadores | 69 | 80.0
Pueblo Nuevo | 43 | 59.0
Universidad | 40 | 56.0
Palacio | 36 | 42.0
Ventas | 35 | 44.0
```
2.05 s

## sql block

```sql
WITH p AS (SELECT ST_Transform(ST_Point(-3.7038, 40.4168), 'EPSG:4326', 'EPSG:25830', always_xy := true) AS g)
SELECT b.nombre, ST_AsText(ST_Transform(ST_Centroid(b.geom), 'EPSG:25830', 'EPSG:4326', always_xy := true)) AS centroid
FROM iceberg_scan('s3://portolan--madrid/v3/barrios') b, p
WHERE b.geom && p.g AND ST_Contains(b.geom, p.g);
```

```
nombre | centroid
Sol | POINT (-3.704555188649378 40.41731053427639)
```
0.59 s

## sql block

```sql
SELECT count(*) AS trees FROM iceberg_scan('s3://portolan--madrid/v3/arbolado_alineacion_zonas_verdes');
```

```
trees
668357
```
0.58 s

## Measured: the spatial filter with and without `&&` (fresh session each, HTTP requests counted)

| filter | rows | requests | MB read | seconds |
|---|---|---|---|---|
| ST_DWithin alone | 31 | 48 | 4.6 | 2.13 |
| && box, then ST_DWithin | 31 | 9 | 0.5 | 1.71 |

## Negative controls, with the positive one (every secret against every way of naming a table)

- keyless secret (positive), s3:// root: 134 rows
- keyless secret (positive), https:// root: 134 rows
- no secret, s3:// root: ERROR: Failed to read iceberg table. No version was provided and no version-hint could be found, globbing the filesystem to locate the latest version is disabled by default as this is considered unsafe and could result in reading uncommitted data.
- no secret, https:// root: ERROR: HTTP Error: HTTP GET error reading 'https://portolan--madrid.s3.amazonaws.com/v3/barrios/metadata/snap-2642679886515750171-1-005b6d5d-40a3-4a35-ab47-7925fefb8b27.avro' in region '' (HTTP 404 Not Found) NoSuchBucket: The specified bucket doe
- a made-up key pair, s3:// root: ERROR: Failed to read iceberg table. No version was provided and no version-hint could be found, globbing the filesystem to locate the latest version is disabled by default as this is considered unsafe and could result in reading uncommitted data.
- a made-up key pair, https:// root: ERROR: HTTP Error: HTTP GET error reading 'https://s3.lakehousebox.com/portolan--madrid/v3/barrios/metadata/snap-2642679886515750171-1-005b6d5d-40a3-4a35-ab47-7925fefb8b27.avro' in region '' (HTTP 403 Forbidden) InvalidAccessKeyId: The access key 

0 block(s) failed.
