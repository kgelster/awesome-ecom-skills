# Catalog-audit GraphQL recipes

Copy-and-adapt starting points for building the cheap index (SKILL step 1). Your
agent writes throwaway code per engagement against the current schema, runs it,
and discards it. All queries here are **read-only**; this skill never mutates.

## The index query

Pull only the fields that reveal PDP quality. Don't over-fetch: every extra
connection raises the query cost and slows a full crawl.

```graphql
query CatalogIndex($first: Int!, $after: String) {
  products(first: $first, after: $after, sortKey: ID) {
    edges {
      node {
        id
        handle
        title
        status                 # ACTIVE | ARCHIVED | DRAFT
        publishedAt            # null = not published to Online Store
        productType            # empty = taxonomy gap
        vendor                 # empty = taxonomy gap
        descriptionHtml        # empty / short = thin description
        mediaCount { count }   # 0 = missing photo, 1 = thin
        variants(first: 100) {
          edges {
            node {
              id
              price            # "0.00" = pricing anomaly
              compareAtPrice   # <= price when set = inverted "sale"
            }
          }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
```

Variables: `{ "first": 100, "after": null }`, then feed `endCursor` back as
`after` until `hasNextPage` is false.

### What each field feeds

- `mediaCount.count` → missing-photo (0) and thin-media (1) flags. Cheaper than
  pulling the `media` connection; you only need the count for the index. Escalate
  to the full `media(first: N)` connection in the **deep-read** step, not the
  index.
- `descriptionHtml` → strip tags in code, measure length. Empty or under a small
  threshold (~20 chars) is "thin/missing". Judge quality only in the deep-read.
- `price` / `compareAtPrice` per variant → `price == 0` is a $0 anomaly;
  `compareAtPrice` set **and ≤** `price` is an inverted or fake sale. Compare as
  decimals, not strings.
- `productType` / `vendor` empty → taxonomy gaps that break filtered collections
  and product feeds.
- `status` / `publishedAt` → weight the flags. A $0 **DRAFT** is noise; a $0
  **ACTIVE + published** product is a live revenue defect.

### Scoping the crawl

Narrow with the `query:` argument on `products` when you only need a slice: it
runs server-side and shrinks the crawl:

- `query: "status:active"`: skip drafts/archived (live-storefront audit).
- `query: "published_status:published"`: only what shoppers can reach.
- `query: "vendor:'Acme'"`: audit one vendor's feed import in isolation.
- `query: "created_at:>2026-06-01"`: audit a recent bulk import.

But remember the sitemap caveat from the SKILL: to audit for *debris* (drafts,
archived, unpublished), do **not** filter to published: that's where the
problems hide. Filter for a live-storefront pass; go unfiltered for a debris
pass.

## Query cost and rate limits

The Admin GraphQL API is **cost-throttled**, not request-throttled. Every query
returns its cost in `extensions.cost`:

```json
"extensions": { "cost": {
  "requestedQueryCost": 92,
  "actualQueryCost": 41,
  "throttleStatus": {
    "maximumAvailable": 2000.0,
    "currentlyAvailable": 1959.0,
    "restoreRate": 100.0
  }
}}
```

- Connection cost scales with `first` **and** nested connections. A page of 100
  products each with a 100-variant sub-connection costs far more than 100 bare
  products. Keep the index query lean (above) and only fan out variants/media in
  the deep-read.
- The leaky bucket refills at `restoreRate` points/sec. Read
  `throttleStatus.currentlyAvailable` from each response and pause when it drops
  below your next query's cost, rather than sleeping a fixed interval: adaptive
  pacing is faster and never trips the throttle.
- On a `THROTTLED` error (or HTTP 429), back off ~2s and retry the same page.
  Don't advance the cursor on a throttle; you didn't get the page.
- Prefer a smaller `first` (e.g. 100) with lean fields over a large `first` with
  deep nesting. Two cheap pages beat one expensive page that throttles.

## Plus-store concurrency

Shopify Plus stores get a **higher cost bucket** (roughly 2× the standard
`maximumAvailable`), which allows modest concurrent pagination: several
in-flight page requests instead of strictly serial. Read the actual
`maximumAvailable` from `throttleStatus` rather than assuming a number; it varies
by plan. Guard concurrency with a shared point-budget check (decrement the
in-memory available-points count before each request, restore on the response's
reported `currentlyAvailable`) so parallel requests don't collectively overrun
the bucket. On a non-Plus store, stay serial: the standard bucket throttles
under concurrency and you gain nothing.

## Bulk operations for very large catalogs

For catalogs in the tens of thousands, a single `bulkOperationRunQuery` streams
the whole `products` connection to a JSONL file with no pagination and no
per-page cost management: one operation, poll for completion, download. It's the
right tool when the index itself is large. It's still read-only. See
[the bulk operations guide](https://shopify.dev/docs/api/usage/bulk-operations/queries).

## Canonical docs

- [products query](https://shopify.dev/docs/api/admin-graphql/latest/queries/products)
- [Query cost / rate limits](https://shopify.dev/docs/api/usage/rate-limits)
- [Bulk operations](https://shopify.dev/docs/api/usage/bulk-operations/queries)
