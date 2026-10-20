# 2026-10-20: `lhbox file put|get|ls|rm` against lakehousebox.com

The `lhbox file` lines in `skills/lakehousebox-load-data/SKILL.md` rest on this run. It used lhbox 0.6.62 from the
branch of #1662 and a throwaway QA account (`qa_account.sh al-lake1 create filesput`, deleted after) with a catalog
`filesqa` that published its `public/` folder. The times are UTC.

**A small file with the owner's headers (00:29:22Z):**

```
$ lhbox --json file put pub/small.csv public/ --catalog filesqa --cache-control "public, max-age=120" \
    --content-disposition 'attachment; filename="small.csv"' --meta source=qa
"uploaded": [{"key": "public/small.csv", "size": 12, "etag": "c3c6bc2ae8ece4bd2510dca21225c041", "method": "put",
              "parts": 1, "content_type": "text/csv"}], "count": 1, "bytes": 12, "seconds": 0.55
```

The ETag is the file's md5 (`md5 -q` gave the same). Read through the CDN with `curl -sD -`, twice:

```
HTTP/2 200  content-type: text/csv; charset=utf-8  cache-control: public, max-age=120, s-maxage=604800
x-amz-meta-source: qa  content-disposition: attachment; filename="small.csv"  cdn-cache: MISS   (then HIT)
```

There was no `content-encoding`. At the S3 endpoint the file answered `cache-control: public, max-age=120` with the same
disposition and metadata.

**150 MiB sent in parts, then downloaded (00:29:46Z, 00:29:55Z):**

```
$ lhbox --json file put big.tif rasters/big.tif --catalog filesqa --cache-control "public, max-age=3600"
{"key": "rasters/big.tif", "size": 157286400, "etag": "763ec863252e895549b946d35fa129ac-3", "method": "multipart",
 "parts": 3, "part_size": 67108864}   "seconds": 4.15
$ lhbox --json file get rasters/big.tif -o big.down.tif --catalog filesqa       (2.75 s)
"bytes": 157286400, "sha256": "b7b4e89e0742c59563809f571e00bb5e79cfe78272845e77d682eb859a6c0e94"
$ shasum -a 256 big.tif big.down.tif      both b7b4e89e…0c94
```

`--skip-unchanged` on both files skipped both. The ETag of the file sent in parts matched the one the CLI computes
from the file.

**A 12 MiB file in parts (`--part-size 5`) into `public/`** with `--cache-control "max-age=60" --content-language en
--meta run=qa` answered through the CDN:

```
cache-control: max-age=60, s-maxage=604800   content-language: en   x-amz-meta-run: qa   content-length: 12582912
```

**Refusals and the rest:**
- `lhbox --json file put page.html` exited 1 with one envelope: `storage_refused`, `415 UnsupportedFileType`.
- `file get public/small.csv -o -` printed the CSV.
- `file rm public/mid.parquet --yes` answered `{"deleted": ["public/mid.parquet"], "count": 1}`.
- `file ls` without `--recursive` listed the folders `_lhbox/`, `public/` and `rasters/`.
