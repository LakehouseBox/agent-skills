# 2026-10-20: `lhbox file cp|sync` and the aws-style spellings against lakehousebox.com

The aws-style `lhbox file` lines in `skills/lakehousebox-load-data/SKILL.md` rest on this run (the put/get/ls/rm
record is `2026-10-20-lhbox-file.md`). It used lhbox 0.6.63 from the branch `cli/file-aws-style` and a throwaway QA
account (`qa_account.sh al-lake1 create filescp`, deleted after) with a catalog `garden`. Output piped, so JSON; the
lines below are the JSON cut down with `jq`. The times are UTC.

**Up, down, and the same bytes back (01:34:37Z):**

```
$ lhbox file cp ./site/data/trees.csv lhbox://garden/public/
"uploaded": [{"key": "public/trees.csv", "size": 20, "etag": "e80a100b3871ae2f7e3022981be48a8a", "method": "put", ...}]
$ lhbox file cp ./site/data/dem.tif lhbox://garden/rasters/ --metadata source=qa,run=cp
"uploaded": [{"key": "rasters/dem.tif", "size": 70000000, "etag": "213dc14666910d22f01a63689c424dfe-2",
              "method": "multipart", "parts": 2, ...}], "seconds": 2.25, "headers": ["metadata"]
$ lhbox file cp lhbox://garden/rasters/dem.tif ./down/
{"key": "rasters/dem.tif", "path": "./down/dem.tif", "bytes": 70000000, "sha256": "dfd8818d…bfc0"}
$ shasum -a 256 site/data/dem.tif down/dem.tif            both dfd8818d…bfc0
```

**sync twice, with and without a filter (01:35:04Z):**

```
$ lhbox file sync ./site lhbox://garden/site/ --exclude "*.tif"
{"uploaded":["site/catalog.json","site/data/notes.csv","site/data/trees.csv","site/sub/empty.geojson"],"skipped":[],"count":4}
$ lhbox file sync ./site lhbox://garden/site/ --exclude "*.tif"          # again
{"uploaded":[],"skipped":[... 4 x "unchanged (same size and ETag)"],"count":0}
$ lhbox file sync ./site lhbox://garden/site/                            # no filter: only dem.tif is new
{"uploaded":["site/data/dem.tif"],"skipped":[4 keys],"count":1,"bytes":70000000,"seconds":2.24}
$ lhbox file sync ./site lhbox://garden/site/                            # again
{"uploaded":[],"skipped":5,"count":0,"seconds":0.11}
$ lhbox file sync lhbox://garden/site/ ./mirror
{"downloaded":[5 keys],"skipped":0,"count":5,"bytes":70000090,"seconds":2.81}
$ lhbox file sync lhbox://garden/site/ ./mirror                          # again
{"downloaded":[],"skipped":5,"count":0,"seconds":0.11}
$ diff -r site mirror && echo identical
identical
$ lhbox file cp lhbox://garden/site/ ./csvonly --recursive --exclude "*" --include "*.csv"
{"downloaded":["…/csvonly/data/notes.csv","…/csvonly/data/trees.csv"],"count":2}
```

**The SKILL.md block as written (01:36:30Z):**

```
$ lhbox file cp ./tiles.pmtiles lhbox://garden/public/ --cache-control "public, max-age=86400"
{"uploaded":[{"key":"public/tiles.pmtiles","size":300000,"method":"put","content_type":"application/vnd.pmtiles"}],"headers":["cache_control"]}
$ lhbox file cp ./stac lhbox://garden/public/stac/ --recursive --exclude "*.tmp"
{"uploaded":["public/stac/catalog.json","public/stac/items/a.json"],"count":2}        (items/b.tmp left out)
$ lhbox file ls lhbox://garden/public/
{"prefixes":["public/stac/"],"objects":[{"key":"public/tiles.pmtiles","size":300000},{"key":"public/trees.csv","size":20}]}
$ lhbox file cp lhbox://garden/public/tiles.pmtiles .
{"key":"public/tiles.pmtiles","path":"./tiles.pmtiles","bytes":300000,"sha256":"a63e33e6…fea1"}   (shasum: the same)
$ lhbox file sync lhbox://garden/public/stac/ ./stac
{"downloaded":["./stac/catalog.json","./stac/items/a.json"],"skipped":0}
$ lhbox file sync lhbox://garden/public/stac/ ./stac                     # again
{"downloaded":[],"skipped":2}
$ lhbox file put ../tiles.pmtiles old/ --catalog garden --metadata a=1,b=2 --dryrun
{"uploaded":[{"key":"old/tiles.pmtiles","size":300000,"content_type":"application/vnd.pmtiles","method":"put"}],"dry_run":true}
$ lhbox file get public/stac/catalog.json cat.json --catalog garden
{"key":"public/stac/catalog.json","path":"cat.json","bytes":28,"sha256":"880d95a4…4046"}
$ lhbox file rm lhbox://garden/public/tiles.pmtiles                     # stdin /dev/null, no --yes
{"catalog":"garden","deleted":["public/tiles.pmtiles"],"count":1}       exit 0, nothing on stderr
```

**Refusals (exit 6, one envelope each):**
- `lhbox file cp ./site/catalog.json s3://<the catalog's bucket>/`: "… is an S3 URL. lhbox addresses a catalog's files
  as lhbox://<catalog>/<key> (the catalog's name or id, e.g. lhbox://garden/public/tiles.pmtiles); the bucket behind it
  is the platform's, not a name to use here."
- `lhbox file cp ./site/catalog.json ./elsewhere.json`: "Neither side is a catalog address: …".
- `--acl public-read`: "--acl is an aws s3 flag that lhbox file does not take: a catalog's files have no per-file ACL
  …(lhbox catalog publish)." `sync --delete`: "… lhbox file sync never deletes: remove what is no longer wanted with
  lhbox file rm KEY (or --recursive PREFIX; --dryrun lists first)." `--content-encoding gzip`: "… upload data.csv.gz as
  it is (typed application/gzip) and readers decompress it."
