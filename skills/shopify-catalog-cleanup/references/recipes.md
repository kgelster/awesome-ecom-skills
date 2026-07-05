# Catalog cleanup recipes

Copy-and-adapt GraphQL against Admin API 2025-07. Every mutation is preceded by
its read-only count/preview. Run the count, sanity-check the number, then mutate.
Endpoint and auth are in the parent SKILL.md.

## 1. Bulk-archive dead products

### 1a. Preview the count (ALWAYS run this first)

Build a `query:` filter from your dead-product criteria. Shopify's product
search supports `inventory_total`, `created_at`, `updated_at`, `tag`, `status`,
`published_status`, and more. Example: zero inventory, not already archived,
untouched since before a cutoff.

```graphql
query DeadPreview {
  productsCount(query: "inventory_total:0 status:active updated_at:<2025-01-01") {
    count
  }
  products(first: 25, query: "inventory_total:0 status:active updated_at:<2025-01-01") {
    nodes { id title totalInventory updatedAt tags }
  }
}
```

Read `count`. If it is wildly above what you expected, your filter is wrong:
re-scope, do not proceed. Sales history is not a product-search field; if "zero
sales" is a criterion, pull it separately (orders/analytics) and intersect the
ID lists yourself before archiving.

### 1b. Archive one product (loop the ID list from 1a)

`productUpdate` sets status and appends a dated undo tag in the same call. Fetch
existing tags first (or read them from 1a) and pass the full merged list:
`tags` replaces, it does not append.

```graphql
mutation Archive($id: ID!, $tags: [String!]!) {
  productUpdate(product: { id: $id, status: ARCHIVED, tags: $tags }) {
    product { id status tags }
    userErrors { field message }
  }
}
```

Variables per product (merge the dated tag onto the product's current tags):

```json
{ "id": "gid://shopify/Product/123", "tags": ["existing-tag", "archived-2026-07-05"] }
```

Check `userErrors` on every response. Respect throttling: read
`extensions.cost.throttleStatus.currentlyAvailable` and back off as it drops.

### 1c. Unarchive (the reversible path)

Archiving is reversible precisely because of the dated tag. To undo a batch:

```graphql
query UndoPreview { productsCount(query: "tag:archived-2026-07-05") { count } }
```

Then loop `productUpdate` with `status: ACTIVE` (or `DRAFT`) over those IDs.
Deletion has no equivalent: that is why archive is the default.

## 2. Orphaned metafield debris (ghost review stars)

### 2a. Confirm the app is gone, then inventory the namespace

The ghost-star class: an uninstalled review app leaves a review namespace plus
rating / rating-count fields the theme still renders as empty stars. First
verify in admin that the owning app is uninstalled (not paused). Then inventory:

```graphql
query MetafieldInventory {
  # definitions still on file for the suspect namespace
  metafieldDefinitions(first: 50, ownerType: PRODUCT, namespace: "reviews") {
    nodes { namespace key name type { name } }
  }
  # how many products actually carry values, with a sample
  products(first: 10) {
    nodes {
      id title
      metafields(first: 30) { nodes { id namespace key value } }
    }
  }
}
```

Note the exact `namespace.key` pairs you intend to remove (e.g. a rating and a
rating-count under a reviews namespace). To count reach precisely, page through
products and tally which carry those keys; do not assume every product has them.

### 2b. Delete the orphaned metafields in batches

`metafieldsDelete` takes up to 25 identifiers (owner GID + namespace + key) per
call. Preview the affected count first (2a). Build identifiers, batch, delete.

```graphql
mutation PurgeOrphans($ids: [MetafieldIdentifierInput!]!) {
  metafieldsDelete(metafields: $ids) {
    deletedMetafields { ownerId namespace key }
    userErrors { field message }
  }
}
```

```json
{
  "ids": [
    { "ownerId": "gid://shopify/Product/123", "namespace": "reviews", "key": "rating" },
    { "ownerId": "gid://shopify/Product/123", "namespace": "reviews", "key": "rating_count" }
  ]
}
```

Re-read a few products to confirm the fields are gone, then reload a storefront
product page (Admin API to confirm the data; storefront only to confirm the
render). If the empty-star snippet persists, its now-dead metafield reference in
the theme needs removing too; flag that to whoever owns the theme.

**Matrixify note:** a blank metafield cell in a Matrixify update **deletes** the
metafield rather than skipping it. Deliberate bulk removal can exploit that;
accidental blanks destroy data. See the `shopify-matrixify` skill.

## 3. HTML artifacts in descriptions

### 3a. Cheap index scan for artifacts

Pull `descriptionHtml` for the scope and regex for the artifact patterns locally
rather than reading products by hand.

```graphql
query DescIndex($cursor: String) {
  products(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes { id title descriptionHtml }
  }
}
```

Flag a product when `descriptionHtml` matches, e.g.: `<strong>\s*<strong>`
(double-nested bold), a `<p>` whose entire inner text sits inside one
`<strong>` (fully-bold paragraph), `<(p|span)>\s*</(p|span)>` (empty tags), or
stray `style="…"` inline attributes.

### 3b. Targeted rewrite (never a from-scratch regen)

Fix `descriptionHtml` per flagged product with a string transform that removes
only the artifact and preserves real formatting: do not regenerate the
description, you will lose intentional structure.

```graphql
mutation FixDesc($id: ID!, $html: String!) {
  productUpdate(product: { id: $id, descriptionHtml: $html }) {
    product { id descriptionHtml }
    userErrors { field message }
  }
}
```

### 3c. Post-edit re-scan (mandatory before "done")

Re-run 3a over the same scope after the batch. A bulk regex fix routinely leaves
a fresh artifact on the products whose markup didn't match your assumption
(unclosed tags, nested spans, entity-encoded brackets). The clean re-scan is the
evidence the job is finished; "the transform ran" is not.

## Canonical docs

- [productUpdate](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productupdate)
- [metafieldsDelete](https://shopify.dev/docs/api/admin-graphql/latest/mutations/metafieldsdelete)
- [Product search query syntax](https://shopify.dev/docs/api/usage/search-syntax)
