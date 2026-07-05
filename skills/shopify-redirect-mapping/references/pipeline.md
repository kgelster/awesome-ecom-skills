# Redirect Mapping Pipeline: 7-Step Runbook

Recipes, not a program. Each block is a starting point your agent adapts to the
store and the current schema, runs once, and discards. Read the parent
[SKILL.md](../SKILL.md) for the recall-over-precision doctrine, the per-type
thresholds, and the cross-type fallback order these steps implement.

## Step 1: Get the 404 list

Source of record is Google Search Console: **Pages → Not found (404) → Export**.
That gives a `Table.csv` with a `URL` column. Any one-URL-per-line list works too
(server logs, a crawler's broken-link report). Put the raw export somewhere
scoped to this engagement.

## Step 2: Normalize and classify each path

Shopify redirects match on **path only**, so reduce every URL to a bare path
before matching:

- strip protocol and host
- lowercase
- percent-decode
- drop the trailing slash
- drop the query string

Then classify by prefix and route:

- `/products/…` → product
- `/collections/…` → collection
- `/blogs/…` → blog
- `/pages/…` → page
- Rewrite legacy `/collections/X/products/Y` to `/products/Y` **for matching
  only**, keeping the original path as the redirect source so the real dead URL is
  what gets caught.
- Media assets (`.jpg`, `.png`, `.mp4`, `/assets/…`) and malformed rows go
  straight to the review/skip buckets. Don't try to fuzzy-match an image.

## Step 3: Pull live inventory via Admin GraphQL

Fetch every candidate target the store currently serves: active product handles,
collection handles, page handles, blog article handles. Paginate 250 per page and
cache the result to JSON (a 24-hour TTL is plenty for a multi-pass job). Minimum
scopes: `read_products` for products and collections, `read_content` for pages
and blog articles, and `read_online_store_navigation`/`write_online_store_navigation`
for the redirect read/write in steps 6–7.

```graphql
# products (repeat the shape for collections, pages, articles)
query($cursor: String) {
  products(first: 250, after: $cursor, query: "status:active") {
    edges { node { handle } cursor }
    pageInfo { hasNextPage }
  }
}
```

Collections use `collections`, pages use `pages`, articles use `articles`
(or walk `blogs { articles }`). Store each type's handle list separately: the
matcher only ever compares a dead path against inventory of its own type first.

## Step 4: Match, the algorithm spec

Compare each normalized dead path against same-type inventory with a string
similarity ratio (Python's `difflib.SequenceMatcher` is the reference
implementation; any equivalent ratio works). Score is weighted:

```
score = 0.7 * similarity(dead_slug, candidate_slug)
      + 0.3 * similarity(dead_path, candidate_path)
```

The slug (last path segment) carries most of the signal; the full path breaks
ties and rewards shared structure. Apply the per-type threshold and the
cross-type fallback order from the SKILL body.

**Product qualifier check (prevents the confident-wrong match).** Before trusting
a product→product match, require a token-subset test: split both slugs on
hyphens, and accept only if one slug's token set is a subset of the other's
(`racing-jacket` ⊂ `mens-racing-jacket-black`). If neither is a subset, the two
are probably different products that merely share a suffix, so let it fall through
to the collection fallback rather than shipping a wrong product.

## Step 5: Bucket and dedupe

Write each result to one of three buckets (see SKILL body): **auto-apply**
(cleared threshold), **review** (low-confidence, media, malformed, fell-through),
**skip** (target equals source). Dedupe source paths so a dead URL yields exactly
one redirect. Keep the buckets as CSVs so a human can read and edit them.

## Step 6: Apply

Two routes. Pick one; both start by reading the existing redirect set so you
never collide with a redirect that already exists.

**Route A, Admin API, one redirect per row.** Query existing redirects first,
skip any source path already mapped, then create the rest.

```graphql
# existing (paginate to cover them all)
{ urlRedirects(first: 250) { edges { node { id path target } } } }

# create
mutation($path: String!, $target: String!) {
  urlRedirectCreate(urlRedirect: { path: $path, target: $target }) {
    urlRedirect { id path target }
    userErrors { field message }
  }
}
```

`urlRedirectCreate` errors on a duplicate source path: that's why the existing
query runs first. Log per-row results so a partial failure is visible.

**Route B, Matrixify Redirects sheet (bulk).** Hand the final map to the sibling
`shopify-matrixify` skill. The Redirects entity is two columns:

```csv
"Path","Target"
"/old-url","/new-url"
```

Export the store's existing redirects as a backup first, run Matrixify's analyze
step before importing, and download the Import Results file after to confirm row
counts. (Column headers vary slightly by Matrixify version, so verify against the
current Redirects sheet template.)

## Step 7: Verify (mandatory before claiming done)

- **Count.** Re-query `urlRedirects` (or read the Matrixify Import Results row
  counts) and compare created-vs-expected. A gap means duplicates were skipped or
  a create failed: reconcile it, don't wave it off.
- **Spot-check 5–10 source paths** against the live storefront:

  ```bash
  curl -sI "https://$SHOPIFY_STORE/old-path" | grep -iE "^(HTTP|location)"
  # expect: HTTP/... 301  and  location: https://.../new-path
  ```

- **Record the pass**: URLs in, redirects created, rows left in review. The review
  count is the backlog for the next pass.

## WordPress → Shopify URL transforms

When the old site was WordPress, most dead URLs won't fuzzy-match a Shopify path
directly because the *structure* differs, not just the slug. Transform the path
before matching:

- **Dated posts:** `/YYYY/MM/DD/slug/` or `/YYYY/MM/slug/` → extract `slug`, match
  as a blog article (`/blogs/<blog>/slug`) or, if it's a product write-up, a
  product.
- **Category archives:** `/category/<cat>/` or `/product-category/<cat>/` →
  match `<cat>` against collection handles at the 0.70 collection threshold.
- **Product permalinks:** `/product/<slug>/` or `/shop/<slug>/` → strip to
  `<slug>`, match as a product, and set the redirect source to the original
  `/product/<slug>` path.
- **Author/tag/paged archives** (`/author/…`, `/tag/…`, `/page/2/`): usually no
  clean target, so send to review, or map tag archives to the nearest collection.

Run the transform in Step 2 (normalize/classify), keeping the original WordPress
path as the redirect source and feeding the extracted slug into the Step 4
matcher.
