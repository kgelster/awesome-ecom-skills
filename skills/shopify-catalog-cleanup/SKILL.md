---
name: shopify-catalog-cleanup
description: >-
  Use when fixing the debris an audit found in a Shopify catalog: bulk-archive
  dead/discontinued/zero-inventory products, clean up catalog debris, kill ghost
  review stars (empty star ratings a theme still renders after a review app was
  uninstalled), remove orphaned metafields left by an uninstalled app, strip HTML
  artifacts from product descriptions (double-nested bold, fully-bold paragraphs,
  empty tags), or fix messed-up / mangled product descriptions in bulk. Mutating
  cleanup work: archive vs delete, metafieldsDelete, description rewrites. Not for
  FINDING what's wrong (use shopify-catalog-audit) or filling missing metadata
  like SEO titles and alt text (use shopify-seo-metadata).
compatibility: >-
  Requires Shopify Admin API access (custom-app token or Shopify CLI 3.x).
  GraphQL written against Admin API 2025-07. Minimum scopes: read_products,
  write_products (products carry metafield read/write).
---

# Shopify Catalog Cleanup

Fixing the debris an audit found. This is the mutating counterpart to
`shopify-catalog-audit` (which finds problems) and `shopify-seo-metadata` (which
fills missing metadata). Everything here writes to the catalog, so the whole
skill is built around one rule: **preview the count, then mutate.**

## Store access

**Lane A: custom-app token (scriptable).** In Shopify admin: Settings → Apps
and sales channels → Develop apps → create an app → grant `read_products` and
`write_products`, install, copy the Admin API access token. Export it; never
write it to a committed file:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="<your Admin API access token>"   # env, not disk
```

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name } }"}'
```

**Lane B: Shopify CLI OAuth (no stored token).** `shopify store auth --store
$SHOPIFY_STORE --scopes read_products,write_products` then `shopify store
execute`. Good for token-less stores where the owner logs in interactively.

**Toolkit preflight.** Lane B rides on the Shopify CLI: run `shopify version`
first and install it if missing. For the full Admin GraphQL schema and
validated execution, pair this skill with Shopify's official AI toolkit
plugin. In Claude Code, check `claude plugin list`; if it isn't there:

```bash
claude plugin marketplace add Shopify/Shopify-AI-Toolkit
claude plugin install shopify-plugin@shopify-ai-toolkit
```

Recommended, not required: Lane A needs only curl and a token. The toolkit
gives your agent the API; this skill gives it the playbook.

## The one rule: preview count, then mutate

Every recipe in [references/recipes.md](references/recipes.md) pairs a read-only
count/preview query with the mutation it feeds. The discipline is not optional:

1. **Run the count first.** `products(query:"…")` with a filter returns
   `count` and a page of titles. Read them.
2. **Sanity-check the number against expectation.** If you expected ~40 dead
   products and the count says 900, **stop and re-scope**: your filter is
   wrong, not the store. A count far above expectation is a bug in your query.
3. **Only then mutate,** and prefer the reversible path (below).

## Non-destructive doctrine

- **Archive, never delete.** Archiving a product (`status: ARCHIVED`) hides it
  from the storefront and channels but keeps the record, its handle, its history,
  and its URL-redirect potential. It is fully reversible: flip status back to
  `ACTIVE` or `DRAFT`. Deletion is not reversible: the product, its variants,
  and its metafields are gone. Default to archive; only delete when the owner
  explicitly asks and understands it is permanent.
- **Tag what you touch.** When you bulk-archive, add a dated tag
  (`archived-2026-07-05`) in the same mutation. That tag is your undo list: to
  reverse, query `tag:archived-2026-07-05` and set status back. Without it you
  cannot cleanly separate your batch from products that were already archived.
- **Read before you write.** A read query is cheap; an unscoped mutation is not
  reversible. Verify a write landed by re-reading the object through the Admin
  API, not the storefront (the storefront is CDN-cached and lies about
  freshness).
- Never print or commit the Admin API access token.

## Recipes, not scripts

The GraphQL blocks in the reference are copy-and-adapt starting points: your
agent writes throwaway code per engagement against the current schema, runs it,
discards it. Bulk mutations should batch and respect throttling: read the
`throttleStatus` in the `extensions` block and back off when
`currentlyAvailable` drops, rather than hammering a fixed rate.

## Three fix classes

### 1. Bulk-archiving dead products

Design the criteria before you touch anything. Common "dead" signals, combined
with AND (a product is rarely dead on one signal alone):

- Zero total inventory across all variants, and
- Zero sales in a trailing window (e.g. 12 months), and
- Created/updated long enough ago to not be a new launch, and
- Not in a collection you care about, or already tagged discontinued.

Turn that into a `products(query: …)` search filter, run the **count** query,
read the sample titles, confirm the number is in the ballpark you expected, then
run `productUpdate` to set `status: ARCHIVED` and append the dated tag. The
unarchive path is the same query on your tag, flipping status back. Recipes:
[references/recipes.md](references/recipes.md).

### 2. Orphaned metafield debris (the ghost-star class)

Classic symptom: a store uninstalled a product-review app (Shopify's own Product
Reviews is the usual culprit), but the theme still renders **empty star ratings**
on every product. The app left its metafields behind: the `spr.reviews` field the
Product Reviews app wrote, plus a `reviews` namespace holding `reviews.rating` and
`reviews.rating_count`. The theme's star snippet reads them, finds `0`, and paints
five empty stars.

Fix safely:

1. **Confirm the app is truly gone.** Check Settings → Apps; the namespace must
   belong to an app that is uninstalled, not merely paused. Deleting metafields
   an installed app owns will just have the app rewrite them.
2. **Inventory the orphaned namespaces.** Query the product metafield
   definitions and a sample of products for every suspect namespace (`spr` and
   `reviews` for the Product Reviews app) so you know exactly which
   `namespace.key` pairs you are removing and how many products carry them.
3. **Delete via `metafieldsDelete`**, keyed by owner GID + namespace + key,
   covering both `spr.reviews` and the `reviews.rating` / `reviews.rating_count`
   fields. Preview the affected-count first, same as archiving; batch the
   identifiers to stay under rate/cost limits.
4. **Re-read** a few products to confirm the fields are gone, then reload the
   storefront product: the empty stars should be gone (the theme snippet may
   also need its now-dead reference removed; flag that to whoever owns the theme).

**Matrixify warning:** a blank cell in a Matrixify update **deletes** that
metafield, it does not skip it. That is a footgun for accidental deletion and a
tool for deliberate bulk removal: either way, know which you are doing. For
spreadsheet-driven bulk work and that trap, see `shopify-matrixify`.

### 3. HTML artifacts in descriptions

Editors, app injections, and copy-paste leave residue in `descriptionHtml`:
double-nested `<strong><strong>…`, whole paragraphs wrapped in bold, empty
`<p></p>` / `<span></span>` tags, stray inline styles. Detect cheaply with an
index scan (pull `descriptionHtml` for the scope, regex for the artifact
patterns) rather than eyeballing products one by one. Fix by rewriting
`descriptionHtml` per product via `productUpdate`: a targeted string transform,
not a from-scratch rewrite that would lose real formatting.

**Post-edit scan doctrine.** After ANY bulk content edit, sweep the affected
scope again for residue: double-bold, orphaned tags, half-applied
transforms, **before** you declare done. A bulk regex fix routinely leaves a
new artifact on the 3% of products whose markup didn't match your assumption.
The passing re-scan is the evidence; "the transform ran" is not.

## References

- [references/recipes.md](references/recipes.md): count-before-mutate archive
  query + mutation, metafield-namespace inventory + `metafieldsDelete`,
  description-artifact scan + safe rewrite.

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions on a rolling quarterly schedule, so verify against
[shopify.dev](https://shopify.dev/docs/api/admin-graphql) before trusting a
version-specific claim. Read-only re-verification a stranger can run (a
metafield-namespace inventory and an archived-product count, both non-mutating):

```bash
# how many products are already archived, and a metafield namespace sample
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ productsCount(query:\"status:archived\") { count } products(first:5) { nodes { title metafields(first:20) { nodes { namespace key } } } } }"}'
```

Canonical docs: [productUpdate](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productupdate),
[metafieldsDelete](https://shopify.dev/docs/api/admin-graphql/latest/mutations/metafieldsdelete).
These skills capture operational lessons the docs don't; they are not a
replacement for the reference.
