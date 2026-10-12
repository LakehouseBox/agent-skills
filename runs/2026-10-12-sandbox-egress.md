# 2026-10-12: can a chat or cloud sandbox compute against LakehouseBox?

The routing in `skills/lakehousebox/SKILL.md` ("a shell that reaches s3.lakehousebox.com") and the MCP server's
`local_compute` rest on these runs. The probe reads the public catalog `commons/pubdata`, no account, no key.

**Positive control, the founder's laptop (macOS arm64, DuckDB 1.5.6):** every host answered; `reference.countries`
249 rows in 0.9 s; `places.places` `count(*), count(DISTINCT country_code)` = 7,257,624 and 50 in 4.3 s.

**A Claude cloud sandbox (Linux x86_64, Python 3.13.16, `CCR_*` environment), default network setting:**

```
api public catalog JSON            FAIL curl: (56) CONNECT tunnel failed, response 403
s3 table metadata                  FAIL curl: (56) CONNECT tunnel failed, response 403
install.sh (lhbox CLI)             FAIL curl: (56) CONNECT tunnel failed, response 403
pypi (pip install duckdb)          FAIL curl: (6) Could not resolve host: pypi.org
extensions.duckdb.org              FAIL curl: (56) CONNECT tunnel failed, response 403
control: example.com               FAIL curl: (56) CONNECT tunnel failed, response 403
```

The proxy's own note: `connect_rejected (the egress proxy denied the CONNECT (organization policy) ...)`.

**Same sandbox after the person allowed lakehousebox.com, its subdomains and extensions.duckdb.org:**

```
api public catalog JSON            200 1.088369s
s3 table metadata                  200 0.679227s
install.sh (lhbox CLI)             200 0.522070s
pypi (pip install duckdb)          FAIL curl: (6) Could not resolve host: pypi.org
extensions.duckdb.org              301 0.270166s
control: example.com               FAIL curl: (56) CONNECT tunnel failed, response 403
```

Why pip failed: `pypi.org` is in the sandbox's `NO_PROXY`, so pip connects directly, but only the proxy resolves names
(`CLAUDE_CODE_PROXY_RESOLVES_HOSTS=true`): `[Errno -2] Name or service not known`. With the bypass turned off,
`NO_PROXY= no_proxy= pip install 'duckdb>=1.5.5'` answered `Successfully installed duckdb-1.5.6`.

Not yet run there: a DuckDB query end to end; claude.ai and ChatGPT chat with the connector (next).

## The same request in claude.ai and ChatGPT, after #1283 went live (2026-10-12, 20:30-21:15 UTC)

One request in a fresh chat each time, with the LakehouseBox connector: "from the public catalog commons/pubdata, the
places table, give me the complete list of every restaurant in Spain (name, locality, coordinates) as a CSV file. I
need all of them, not a sample." The table holds 60,412 such rows, 30 times the 2,000-row cap of server-side `query`.
Claude: Opus 5.5 on claude.ai, code execution on. ChatGPT: free plan, the connector added as a custom MCP server.

| client | sandbox network | what the agent did |
|---|---|---|
| ChatGPT, before #1283 | none (its code tool) | counted 60,412 on the server, said the cap blocks a full export, offered `lhbox duckdb` and a COPY |
| claude.ai | package managers + `*.lakehousebox.com`, `lakehousebox.com`, `extensions.duckdb.org` | installed DuckDB in the sandbox and wrote all 60,412 rows to a CSV (the server's count) in about 4 minutes, after two detours below |
| claude.ai | package managers only (the default) | saw the block, refused to retype ~70 pages by hand, wrote a DuckDB script for the person, and said: allow lakehousebox.com and its subdomains in the sandbox's network settings and ask again |
| claude.ai | outbound network off | the same, plus: link the chat to your computer through the desktop app, or ask an admin to allow the hosts |
| ChatGPT, after #1283 | none | as before: the count, the cap, an export script to run elsewhere (it never hit a truncated answer, so `local_compute` never showed) |

The two detours in the allowed-network run, both ours to fix (the PR after #1283):

1. The keyless read failed: `Authentication Failure ... Credentials are provided, but they did not work`. The sandbox
   sets `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` to placeholders and DuckDB signs with them. Reproduced on a laptop
   with DuckDB 1.5.6 against production: with the two variables set, `iceberg_scan('s3://commons--pubdata/reference/countries')`
   fails; with `KEY_ID '', SECRET ''` added to the keyless secret it answers 249; without the variables, 249 either way.
2. The connector's ATTACH recipe was refused before it ran: `Permission for this action was denied by the Claude Code
   auto mode classifier. Reason: [Credential Exploration]`. The recipe holds the public catalog's shared reader key in
   clear. The agent finished by reading the table's Parquet files over plain HTTPS.
