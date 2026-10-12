# 2026-10-12: an agent with no account, on production

What `skills/lakehousebox/SKILL.md` ("With a shell and no account yet") and `lakehousebox-load-data/SKILL.md` say about
`lhbox new` and `lhbox claim` comes from this run: lhbox 0.6.33 against https://api.lakehousebox.com, DuckDB 1.5.6, the
person's side a QA account (deleted after). The full record, commands and answers, is
`research/results/t70_agent_signup_prod_run.txt` in the private repository; the parts the skill relies on:

- `lhbox new` answered "Created catalog lakehouse for this agent, with no account" in 1.29 s, with the 72-hour deadline,
  "at most 1 GB, nothing public, data only" and the Terms line.
- `lhbox table import cities.csv --catalog lakehouse --namespace demo --name cities` wrote 3 rows in one commit (4.34 s
  wall); `lhbox query` read them back (193 ms).
- `lhbox claim` printed the link and the code, valid 24 h, and "Then run: lhbox claim --resume --wait".
- After the person approved (into their organisation, write), `lhbox claim --resume --wait` printed "Connected to
  lakehouse (read and write)"; the earlier key answered 401; `lhbox status` said "This key belongs to an account:
  nothing expires"; a second import with the new key worked.
