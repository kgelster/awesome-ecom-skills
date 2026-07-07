---
name: shopify-redirect-mapping
description: >-
  Use when you need to map a pile of old URLs to live pages and turn them into
  301 redirects on a Shopify store: fix 404s, bulk redirects after a
  migration/replatform/catalog restructure, turn a Google Search Console 404
  export into live redirects, or WordPress→Shopify URL transforms
  (/YYYY/MM/slug/ → /products/slug). Trigger phrases: "map old URLs", "fix our
  404s", "redirect the dead links", "we relaunched and lost our rankings".
  Recovers SEO equity and rescues users after a URL structure changes. Not for
  creating a single one-off redirect (do it in admin).
compatibility: >-
  Requires Shopify Admin API (custom-app token or Shopify CLI 3.x), GraphQL
  written against Admin API 2025-07, scopes read_products/read_content/
  read_online_store_navigation/write_online_store_navigation. Or apply in bulk
  via the Matrixify Redirects sheet.
---

# Shopify Redirect Mapping

Turn a list of 404ing URLs into live 301 redirects on a Shopify store using
type-aware fuzzy matching with a manual review queue for the leftovers. The job
is reclaiming search equity and rescuing lost visitors, not building a perfect
1:1 map. For bulk apply through a spreadsheet instead of the API, hand the final
map to the sibling `shopify-matrixify` skill's Redirects sheet.

## The one rule that matters: recall over precision

A wrong-but-related redirect beats a 404. A visitor who lands on a close product
or the right category still converts; a visitor who hits a dead page leaves.
Google keeps some of the old page's equity when the 301 points somewhere
topical; it keeps none when the URL 404s. So tune for coverage, not for a
flawless match, and let a human review pass catch the misfires.

**Worked case (an automotive-lifestyle brand, anonymized).** A first pass used a
single conservative 0.92 similarity threshold across all URL types. Out of 1,010
dead URLs it produced 6 redirects: effectively nothing, and the merchant called
it useless. Re-running with per-type thresholds plus cross-type fallbacks
yielded 725 live redirects (~72% coverage) from the same export. The lesson is
blunt: do not ship a conservative first pass. Precision-first thresholds look
safe and deliver nothing.

## Per-type thresholds (defaults, not suggestions)

Different URL types tolerate different looseness. Classify each dead path by its
prefix, then match it only against live inventory of the same type at these
cut-offs:

- **Products: 0.85.** Accepts some "same suffix, different product" matches (a
  discontinued `-jacket` landing on another `-jacket`). That is the acceptable
  cost of recall; the review pass pulls the ones that are genuinely wrong.
- **Collections: 0.70.** Most dead collection URLs are restructure churn. Any
  nearby collection is a better landing than the homepage.
- **Blogs / pages: 0.85.** Brand pages that resolve to collections: 0.70. The
  review queue catches the rest.

## Cross-type fallback order

When a path can't clear its own-type threshold, fall *down* a type rather than
giving up:

- **Product path:** product match @0.85 → fuzzy collection match @0.70 → review
  queue. A category page is a better landing than the homepage; a *wrong*
  product is worse than no product, so a weak product match falls through to
  collection rather than being forced.
- **Collection path:** collection match @0.70 → review queue.

**Never silently fall back to `/` (the homepage).** Homepage fallback looks like
100% coverage but destroys the one signal that tells you a URL still needs human
attention, and it dilutes the redirect's topical value to nothing. A path that
matches nothing goes to the review queue, not to home.

## What thresholds cannot fix

Spec mismatches that are string-identical to the algorithm: a 12mm part slug is
one character off a 14mm part slug, a size-S variant reads almost identical to
size-XL. Fuzzy matching will confidently pick the wrong one. These get
hand-pulled from the auto-apply set during review. That judgment call does not
go away, and no threshold removes it.

## Three-bucket output

Every matched path lands in exactly one bucket. This is what makes the pass
auditable and the review scoped:

1. **auto-apply**: cleared its type threshold. Still eyeballed before pushing,
   but the default is to ship it.
2. **review**: low-confidence matches, media assets (`.jpg`, `.mp4`,
   `/assets/`), malformed rows, and anything that fell through to the queue. A
   human sets or confirms the target here.
3. **skip**: no-op, where the best target equals the source path. Dedupe source
   paths so one dead URL yields one redirect.

## Review-pass budget

Expect iteration. The anonymized case above took several passes (6 → 725
redirects) as fallback stages were added and the review queue was worked down.
Budget for at least 2–3 passes on a first engagement: run, review the buckets,
adjust thresholds or hand-edit targets, re-run. A one-shot redirect map is a
sign you tuned for precision and left coverage on the table.

## Store access

This skill reads inventory and writes redirects through the Admin API. Pick one
lane; never write a token to a committed file.

**Lane A, custom-app token.** In Shopify admin: Settings → Apps and sales
channels → Develop apps → create an app → grant this skill's minimum scopes
(`read_products`, `read_content`, `read_online_store_navigation`,
`write_online_store_navigation`), install, and copy
the Admin API access token. Keep it in the env:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="<your Admin API access token>"   # env, not disk
```

**Lane B, Shopify CLI OAuth (no stored token).** `shopify store auth --store
$SHOPIFY_STORE --scopes read_products,read_content,read_online_store_navigation,write_online_store_navigation`
then `shopify store execute` to run a validated operation.

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

## Preview before you mutate; stay non-destructive

- **Read before you write.** Pull the live inventory and the existing redirect
  list first. Before creating a redirect, query the existing set and skip
  duplicates: `urlRedirectCreate` will error on a source path that already
  redirects.
- **Back up first.** Export the store's current redirects (Matrixify export or a
  `urlRedirects` dump) before a large write, so the pass is reversible.
- **Verify against the Admin API, not the storefront.** The storefront is
  CDN-cached and lies about freshness. Confirm each write by re-querying the
  redirect through the API, then spot-check a handful of old paths with
  `curl -I` and look for `301` plus the mapped `location`.

## Recipes, not scripts

The GraphQL and matching logic in [references/pipeline.md](references/pipeline.md)
are copy-and-adapt starting points. Your agent writes throwaway code per
engagement against the current schema, runs it, and discards it: that keeps the
pass honest across Shopify's quarterly schema changes rather than shipping a
binary that silently rots. The eight-step runbook, the matching-algorithm spec,
the `urlRedirectCreate` and Matrixify apply paths, the redirect-to-404 rot sweep
(`urlRedirectUpdate`), and the WordPress URL transforms all live there.

## References

- [references/pipeline.md](references/pipeline.md): the 8-step runbook, from GSC
  404 export → inventory pull → matching-algorithm spec → apply → redirect-to-404
  rot sweep → `curl -I` verify, plus WordPress pattern transforms.

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions on a rolling quarterly schedule, so verify the mutation and
query names against
[shopify.dev](https://shopify.dev/docs/api/admin-graphql) before trusting a
version-specific claim. Read-only re-verification a stranger can run:

```bash
# 1. List existing redirects (confirms scope + shows current map)
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ urlRedirects(first:10){ edges{ node{ path target } } } }"}'

# 2. Probe an old path and confirm it 301s where you expect
curl -sI "https://$SHOPIFY_STORE/old-path" | grep -iE "^(HTTP|location)"
```

Canonical docs: Shopify [URL redirects](https://help.shopify.com/en/manual/online-store/os/menus-and-links/url-redirect)
and the [Admin GraphQL API](https://shopify.dev/docs/api/admin-graphql); source
the 404 export from [Google Search Console](https://search.google.com/search-console)
(Pages → Not found). These skills capture operational lessons the docs don't;
they are not a replacement for the reference.
