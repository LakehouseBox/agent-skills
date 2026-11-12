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
| this machine, for the person's own agent | `lhbox login`: it acts as the person | [access](references/access.md), "Tokens for agents" |
| a program, a server, or an agent that should not act as the person | a token with exactly the grants it needs | [access](references/access.md) |
| a colleague | invite them to the organisation from the account page, then grant read or write on the catalog | [access](references/access.md) |
| anyone, with no account | publish the catalog | [public-catalogs](references/public-catalogs.md) |
| people of the organisation, as a page they open: a dashboard, a report, a map | publish an artifact: `lhbox artifact publish page.html --title "The garden" --catalog <catalog>`; the person shares it on the page | [artifacts](references/artifacts.md) |

## Agents and programs: the narrowest grant that works

```sh
lhbox login                                                              # this machine, as the person: they click Allow
lhbox token create --name nightly-load --grant sales:write --grant raw:read
lhbox token list
lhbox token revoke nightly-load
```

- **Read unless the job writes.** A reporting job gets `:read`; only a loader gets `:write`.
- **The key is shown once** by `token create`; the program reads it as `LHBOX_API_KEY`. Never paste it into a
  conversation or a file in a repository.
- **Revoking** stops the key at once; deleting a credentials file does not.

## Publish: anyone can read it

Only an **admin** can publish (or a member with write, when an admin lets members publish). A machine's `lhbox login`
key acts as the person who approved it; a token is a member's unless made an admin. When the key may not publish, ask
the person to publish from the account page; never ask them to make a token an admin.

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

- [access](references/access.md): roles, catalog grants, tokens for agents, revoking and rotating, deleting a
  catalog, the audit log.
- [access-organisation](references/access-organisation.md): invitations, domain claims, joining by domain.
- [access-credentials](references/access-credentials.md): the credentials an engine gets and how long each lives.
- [public-catalogs](references/public-catalogs.md): what publishing makes readable, the public page, reading with no
  account, attaching by name, allowances, risks.
- [artifacts](references/artifacts.md): writing a page that reads the catalogs live with each viewer's own
  permissions, publishing it and its next versions, what a viewer without access sees, limits.
