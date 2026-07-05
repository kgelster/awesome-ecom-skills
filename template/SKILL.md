---
name: shopify-yourskill
description: >-
  Use when [the specific situations, symptoms, and phrases someone would type or
  think when they hit this problem]. Pack real trigger words and store-owner
  symptoms. Describe ONLY when to use it, never summarize the workflow inside.
  Keep the whole frontmatter under 1024 characters. End by naming what this
  skill is NOT for, pointing at the sibling skill that covers it.
compatibility: >-
  Requires Shopify Admin API access (custom-app token or Shopify CLI 3.x).
  GraphQL written against Admin API 2025-07.
---

# Shopify Yourskill

One or two sentences: what this skill covers and the core principle. Cross-
reference sibling skills by name when a task belongs to one of them, rather than
repeating their content.

## Guidelines for a good ecom skill

Delete this section in your real skill; it's guidance for authoring.

- **Name:** `shopify-<area>` (or `ecom-<area>` for platform-neutral skills),
  lowercase and hyphens only. The directory name MUST equal the frontmatter
  `name`.
- **Description:** starts with "Use when…", lists concrete triggers and
  keywords, ends with a "not for X, use Y" pointer. No workflow summary — an
  agent follows the description to decide whether to load the body.
- **Original prose only.** Do not paste from shopify.dev, the Matrixify docs, or
  any other source — write the lesson in your own words and link the canonical
  doc. Ship the institutional knowledge agency work teaches that the docs don't.
- **Body 100–200 lines; heavy detail in `references/*.md`.** No `scripts/`
  directory — this collection is markdown-only (see recipes doctrine below).
- Every SKILL.md ends with a **Provenance and maintenance** section.

## Store access

Every skill that touches the Admin API opens with this stanza (paste it, adjust
the scopes line to this skill's minimum). Two lanes; pick one.

**Lane A — custom-app token (scriptable).** In Shopify admin: Settings → Apps
and sales channels → Develop apps → create an app → grant the minimum scopes
this skill needs, then install and copy the Admin API access token. Export it;
never write it to a committed file:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="<your Admin API access token>"   # keep it in the env, not on disk
```

Call the GraphQL endpoint (this skill's minimum scopes: `read_products`,
`write_products` — edit per skill):

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name } }"}'
```

**Lane B — Shopify CLI OAuth (no stored token).** `shopify store auth --store
$SHOPIFY_STORE --scopes read_products,write_products` then `shopify store
execute` to run a validated operation. Good for token-less stores where the
owner logs in interactively.

For the full Admin GraphQL schema and per-object reference, use Shopify's
official AI toolkit plugin — that plugin gives your agent the API; this skill
gives it the playbook.

## Recipes, not scripts

This collection ships **recipes, not programs.** The GraphQL/curl blocks here
are copy-and-adapt starting points: your agent writes throwaway code per
engagement against the current schema, runs it, and discards it. That keeps the
skill honest across Shopify's schema changes and avoids shipping a binary that
silently rots. Two rules make recipes safe:

1. **Preview before you mutate.** Every mutation recipe is preceded by a
   read-only count/preview query. Run the count, sanity-check the number against
   what you expect, and only then mutate. A count far above expectation means
   stop and re-scope, not proceed.
2. **Safe-mode defaults, stated in prose.** Fill missing only, never overwrite;
   MERGE not REPLACE; hide/archive before delete. State the destructive path
   exists and how to opt into it deliberately — never make it the default.

## Non-destructive doctrine

- Read before you write. A read-only query is always cheap; an unscoped mutation
  is not reversible.
- Back up first where a bulk export is the backup (Matrixify export, or a
  `bulkOperationRunQuery` dump) before a large write.
- **Verify against ground truth via the Admin API, not the storefront.** The
  storefront is CDN-cached and lies about freshness; read the object back
  through `admin/api/.../graphql.json` to confirm a write landed.
- Never print or commit an Admin API access token. Read it from the env.

## [Your sections]

Quick-reference tables, the specific traps agency work taught, worked examples
with real numbers but anonymized brands. One excellent example beats five
generic ones.

## References

- [references/topic.md](references/topic.md) — heavy detail loaded on demand.

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions on a rolling quarterly schedule, so verify against
[shopify.dev](https://shopify.dev/docs/api/admin-graphql) before trusting a
version-specific claim. Read-only re-verification a stranger can run:

```bash
# confirm your token reaches the store and the API version resolves
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name currencyCode } }"}'
```

Canonical docs: [Admin GraphQL](https://shopify.dev/docs/api/admin-graphql).
These skills capture operational lessons the docs don't; they are not a
replacement for the reference.
