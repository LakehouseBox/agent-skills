---
name: lakehousebox-hosted-agents
description: Create a LakehouseBox hosted agent - a prompt LakehouseBox runs next to the person's data, on demand or on a schedule, that reads their catalogs with SQL, keeps a few values between runs and emails a summary - test it before it sends anything, and read what each run did. A preview, enabled per organisation. Builds on the lakehousebox skill.
---

# Hosted agents: a prompt LakehouseBox runs next to the data

The `lakehousebox` skill has the ways in. A hosted agent runs **on LakehouseBox**, not on the person's machine: their
computer can be off. It acts through an identity of its own that reads exactly the catalogs its definition names.

**A preview, enabled per organisation.** Until it is enabled, creating or running one answers `403
feature_not_enabled`; the person asks at hello@lakehousebox.com. Say so before planning around it.

## The default path

```sh
lhbox agent create garden_morning --prompt @prompt.md --catalog garden \
    --schedule "0 8 * * *" --tz Europe/Madrid --state-key journal --notify-owner
lhbox agent run garden_morning --dry-run --wait        # a test run: what it would do, nothing sent
lhbox agent run garden_morning --wait                  # a real run
lhbox agent show garden_morning                        # definition, schedule, memory, last run
```

- **Write the prompt as a task for someone who has never seen the data**: which tables, what to compute, what is
  worth telling the person, what to do when there is nothing new. Read the catalog's AGENTS.md first and point the
  prompt at it.
- **Always a test run first** (`--dry-run`): it runs for real, but its email and memory writes are recorded in the run
  instead of performed, and its integrations offer only read-only tools. It does not count against the runs per day.
- **Give it the fewest catalogs** it needs; it can read nothing else.
- **`--state-key`** names a value it keeps between runs (a journal, the last value it reported), so it can say what
  changed rather than repeat itself.
- `lhbox agent update <name>` changes any part (a new version each time); `--pause` and `--resume` stop and restart
  the schedule; `lhbox agent delete <name> --yes` removes it, and its runs stay readable.

## What it can do in a run, and the limits

It reads its catalogs' tables and AGENTS.md, runs read-only SQL, keeps small values between runs, appends rows to
tables its definition names (`--write`), fetches from hosts it names (`--allow-host`), emails the owner and its
subscribers (once per run, five times a day) and uses the tools of connected MCP servers it is allowed. The defaults
per organisation: 4 runs a day, 5,000,000 tokens a month, the shortest schedule hourly; one run at most 400 s and 30
tool calls ([hosted-agents](references/hosted-agents.md), "Limits").

## References

- [hosted-agents](references/hosted-agents.md): creating one, what a run may do, models, schedules, test runs, run
  records, integrations (MCP servers), limits.
