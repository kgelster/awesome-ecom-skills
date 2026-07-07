---
name: shopify-catalog-audit
description: >-
  Use when someone wants to find product-data problems across a Shopify
  catalog: "audit my catalog", "find PDP problems", "which products have
  missing photos / thin or missing descriptions / pricing anomalies", "$0
  or compare-at-inverted prices", "products missing type or vendor", "catalog
  quality sweep", "product data health check", "which listings are broken",
  "run a catalog audit before a big sale". Read-only: it locates and ranks
  problems, it does not change anything. Not for FIXING the problems it finds
  (use shopify-catalog-cleanup for debris/archiving, shopify-seo-metadata for
  missing SEO meta, shopify-alt-text for missing image alt text).
compatibility: >-
  Requires Shopify Admin API read access (custom-app token or Shopify CLI
  3.x). Minimum scope: read_products. GraphQL written against Admin API
  2025-07.
---

# Shopify Catalog Audit

Finding the problems, not fixing them. This is the **FIND** stage of catalog
work: it produces a ranked, justified list of product-data defects and hands
them off. The **FIX** stage lives in sibling skills: `shopify-catalog-cleanup`
(archiving/debris), `shopify-seo-metadata` (missing SEO meta), `shopify-alt-text`
(missing image alt). Don't mutate here.

The core principle: on a catalog too large to eyeball, **don't read every PDP.**
Build a cheap deterministic index over the whole catalog, let the model form
justified hypotheses about where problems cluster, deep-read only that slice,
then verify against the Admin API. The full method is in
[references/triage-method.md](references/triage-method.md); the GraphQL recipes
are in [references/queries.md](references/queries.md).

## Store access

Read-only audit. Grant the **minimum scope, `read_products`**, and nothing
else: this skill never needs a write scope, and a read-only token is the
cheapest guarantee it can't damage the catalog.

**Lane A: custom-app token (scriptable).** In Shopify admin: Settings → Apps
and sales channels → Develop apps → create an app → grant `read_products`, then
install and copy the Admin API access token. Export it; never write it to a
committed file:

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
$SHOPIFY_STORE --scopes read_products` then `shopify store execute` to run a
validated read. Good for token-less stores where the owner logs in
interactively.

**Toolkit preflight.** Lane B rides on the Shopify CLI: run `shopify version`
first and install it if missing. For the full Admin GraphQL schema and
validated execution, pair this skill with Shopify's official AI toolkit
plugin. In Claude Code, check `claude plugin list`; if it isn't there:

```bash
claude plugin marketplace add Shopify/Shopify-AI-Toolkit
claude plugin install shopify-plugin@shopify-ai-toolkit
```

Recommended, not required: Lane A needs only curl and a token. The toolkit
gives the agent the API; this skill gives it the audit playbook.

## Non-destructive doctrine

This is a **read-only skill**; the doctrine is trivially satisfied but still
governs how you verify.

- **Never mutate.** No `productUpdate`, no `productDelete`, no bulk write. If a
  finding needs fixing, name the sibling FIX skill and stop.
- **Verify existence and state via the Admin API, not the sitemap.** The
  sitemap (`/sitemap_products_1.xml`) lists **published** products only, and it
  silently misses drafts, archived items, and unpublished products, which are
  exactly where data debris hides. An audit that trusts the sitemap
  under-reports. Read product state back through `admin/api/.../graphql.json`.
- **Ground truth beats self-grading.** A finding is real when re-querying the
  Admin API confirms the defect on the live object, not when your index says so.

## The audit loop

Two layers: a cheap deterministic index over the whole catalog, then
hypothesis-driven triage on top of it. Never paste the whole catalog into the
model "to be thorough": that's the cost trap this method avoids.

**1. Build the cheap index.** Paginate `products` and pull only the fields that
reveal PDP quality (recipes in [references/queries.md](references/queries.md)).
Per product, compute deterministic flags in code (code answers what code can):

- **Images:** `mediaCount` / image count is 0 (missing photo) or 1 (thin, likely
  a placeholder for a product that should show several angles).
- **Description:** `descriptionHtml` empty, or stripped length below a small
  threshold (e.g. under ~20 chars = effectively empty). Flag "thin", don't
  judge quality yet.
- **Pricing anomalies:** any variant `price` of `0.00`; any variant where
  `compareAtPrice` is set but **≤** `price` (an inverted or fake "sale" that
  shows no discount or a negative one).
- **Taxonomy gaps:** empty `productType` or empty `vendor`: these break
  filtered collections, faceted search, and Google Shopping feeds.
- **Status context:** carry `status` (ACTIVE/DRAFT/ARCHIVED) and
  `publishedAt` so a flag can be weighed (a $0 draft is noise; a $0 active
  published product is a live defect).

Emit a compact per-product row (handle, id, status, the boolean flags). That
table, not the raw catalog, is the surface the model reasons over.

**2. Hypothesize on the index, justified.** The model reads the flag table and
ranks where the real problems cluster, **with a stated reason per hypothesis:
no reason, drop it.** Good hypotheses find *patterns*, not just rows: "every
product from vendor X imported last month has 0 images, likely a broken feed
import" beats "these 40 products lack images." Weight by live impact: an active,
published product with a $0 price is a revenue leak; the same flag on a draft is
noise.

**3. Deep-read only the targeted slice.** Pull full detail for just the products
the justified hypotheses point at (their PDPs, variant tables, media). This is
where the real tokens go. **Never widen back to the whole catalog "to be safe"**
: that defeats the method.

**4. Verify against ground truth.** Re-query each surviving finding through the
Admin API and confirm the defect on the live object. Not against the index, not
against the sitemap. The passing real-world read is the evidence.

## Discipline rails

- **Justify-or-drop.** A flag the model can't explain doesn't get deep-read.
- **Log coverage.** State what you indexed and what you did **not**. "Found 18
  problem products" must never read as "the catalog is clean": you indexed for
  images, description, pricing, and taxonomy, so you are blind to everything
  else (broken variants, mismatched options, bad metafields). Name the blind
  spot explicitly; triage is not assurance.
- **Re-aim, don't widen.** Thin results mean a better index (flag a different
  signal), not feeding more raw catalog to the model.
- **Rate limits are real.** The `products` connection is query-cost throttled;
  read the cost-and-concurrency notes in
  [references/queries.md](references/queries.md) before a full-catalog crawl.

## Handoff format

Output a ranked list, grouped by defect class, each row: handle, product id,
status, the specific flag(s), the justification, and the sibling FIX skill that
owns the remedy. Missing/thin images → `shopify-alt-text` also applies once
photos exist; missing SEO meta surfaced as a side effect → `shopify-seo-metadata`;
archivable debris and $0 drafts → `shopify-catalog-cleanup`.

## References

- [references/queries.md](references/queries.md): paginated `products` GraphQL
  recipes, the fields to pull for the index, query-cost / rate-limit notes, and
  a Plus-store concurrency note.
- [references/triage-method.md](references/triage-method.md): the
  hypothesis-driven triage method generalized for catalog work.

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions on a rolling quarterly schedule, so verify field names and
the version against
[shopify.dev](https://shopify.dev/docs/api/admin-graphql) before trusting a
version-specific claim. Read-only re-verification a stranger can run, confirming
the token reaches the store and the audit fields resolve on the live schema:

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ products(first:5){ edges{ node{ handle status productType vendor descriptionHtml mediaCount{count} variants(first:5){ edges{ node{ price compareAtPrice } } } } } } }"}'
```

Canonical docs: [Admin GraphQL](https://shopify.dev/docs/api/admin-graphql),
[the `products` query](https://shopify.dev/docs/api/admin-graphql/latest/queries/products).
This skill captures the audit method the docs don't; it is not a replacement for
the reference.
