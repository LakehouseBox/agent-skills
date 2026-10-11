---
name: lakehousebox-share
description: Share LakehouseBox data - give a colleague or another agent read or write on one catalog, make a read-only key for a reporting job, revoke access, publish a catalog so anyone can read it with no account, and write the AGENTS.md and table descriptions that tell readers what the data means. Builds on the lakehousebox skill.
---

# Share LakehouseBox data

The `lakehousebox` skill has the ways in and the general rules. Access is given **per catalog**, read or write, and
can always be taken back. Who may do what depends on the person's role: an admin grants on every catalog; a member only
where they hold write, never above their own level ([access](references/access.md)).

## First decision: who should read it

| who | do | read next |
|---|---|---|
| this machine, for an agent | `lhbox login` with the catalogs and levels it needs | [access](references/access.md), "Tokens for agents" |
| a program or an agent on a machine where nobody runs `lhbox login` | a token with exactly the grants it needs | [access](references/access.md) |
| a colleague | invite them to the organisation from the account page, then grant read or write on the catalog | [access](references/access.md) |
| anyone, with no account | publish the catalog | [public-catalogs](references/public-catalogs.md) |

## Agents and programs: the narrowest grant that works

```sh
lhbox login --catalog sales:read --catalog raw:write --name etl-box      # this machine; the person approves once
lhbox token create --name nightly-load --grant sales:write --grant raw:read
lhbox token list
lhbox token revoke nightly-load
```

- **Read unless the job writes.** A reporting job gets `:read`; only a loader gets `:write`.
- **The key is shown once** by `token create`; the program reads it as `LHBOX_API_KEY`. Never paste it into a
  conversation or a file in a repository.
- **Revoking** stops the key at once; deleting a credentials file does not.

## Publish: anyone can read it

Only an **admin** can publish. A machine's `lhbox login` key is a member's, so ask the person to publish from the
account page or to run this signed in as an admin; never ask them to make the machine's key an admin.

```sh
lhbox catalog publish <name> --confirm                     # every table, read-only, for anyone
lhbox catalog publish <name> --confirm --files public/     # also one folder of the file bucket
lhbox catalog unpublish <name>                             # private again: tables, folder and AGENTS.md
```

Say these to the person before they publish ([public-catalogs](references/public-catalogs.md), "Risks"):

- everything in the catalog is readable and copyable by anyone, **including its history**: a row deleted today may
  still be in an older snapshot;
- anything later written into the published folder is public too;
- public bytes count in their own allowance (5 GB; 50 GB once LakehouseBox reviews the dataset).

Readers then find it at `https://lakehousebox.com/app/<handle>/<catalog>`, attach it with `lhbox duckdb --catalog
<handle>/<catalog>`, or query it through MCP by its alias `<handle>_<catalog>`.

## Tell readers what the data means

People and agents who read shared data lack the context its writers have:

```sh
lhbox catalog agents-md <catalog> --set AGENTS.md          # what the tables mean, how they join, units, caveats
lhbox table document <catalog>.<ns>.<table> --doc "One row per …"
```

The AGENTS.md of a public catalog is public too: nothing in it the owner would not publish.

## References

- [access](references/access.md): roles, catalog grants, tokens for agents, the credentials an engine gets, revoking
  and rotating, deleting a catalog, the audit log.
- [public-catalogs](references/public-catalogs.md): what publishing makes readable, the public page, reading with no
  account, attaching by name, allowances, risks.
