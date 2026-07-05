# Alt-text recipes: one mutation, two find paths

Copy-and-adapt GraphQL. Both product images and Files-library images are
`MediaImage` nodes (a `File` subtype), so **both write through `fileUpdate`**:
there is only one mutation to learn. The two sections below differ only in how
you FIND the images. Every mutation is preceded by the read-only count/preview
for the same find path. Run the count, sanity-check it, then mutate; re-query to
verify. Pin the API version in the URL (`/admin/api/2025-07/graphql.json`).

The candidate rule is identical everywhere: an image qualifies only when its
`alt` is null or empty after trimming whitespace, its type is `MediaImage`, its
MIME is `image/*`, and it has a resolvable URL. Never touch an image that already
has alt.

`productUpdateMedia` is **deprecated**; do not reach for it. `fileUpdate` on the
`MediaImage` GID is the current write for product media too.

---

## The one write: `fileUpdate`

Both find paths below yield `MediaImage` GIDs. Feed them into this mutation.

```graphql
mutation SetAlt($files: [FileUpdateInput!]!) {
  fileUpdate(files: $files) {
    files { id alt }
    userErrors { field message code }
  }
}
```

Variables (fill missing only: every `id` here came from a count as a candidate;
batch a handful per call so one bad node does not fail the set):

```json
{
  "files": [
    { "id": "gid://shopify/MediaImage/1111", "alt": "Front view of the item on a plain background" },
    { "id": "gid://shopify/MediaImage/2222", "alt": "Close-up of the stitched seam and hardware" }
  ]
}
```

An empty `userErrors` array is the only success; the returned `files` echo the
new `alt`. Throttle writes (roughly one call per half-second) to stay under the
Admin API rate limit; the GraphQL bucket is cost-based, so watch `throttleStatus`
if you parallelize. Log each write (GID, old alt, new alt, status) so a bad batch
is auditable.

---

## Find path 1: product media

Product images are `MediaImage` nodes under a product's `media` connection.
Filter with `query: "media_type:IMAGE"` to keep videos and 3D models out.

### Count / preview (read-only)

Page products, count image media with empty `alt`. Do this first and read the
number back before any write.

```graphql
query ProductMediaMissingAlt($cursor: String) {
  products(first: 50, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id
        title
        media(first: 25, query: "media_type:IMAGE") {
          edges {
            node {
              ... on MediaImage {
                id
                alt
                mimeType
                image { url }
              }
            }
          }
        }
      }
    }
  }
}
```

Client-side, a media node is a candidate when `alt` is null or `alt.trim() == ""`,
`mimeType` starts with `image/`, and `image.url` is non-null. Sum candidates
across all pages for the preview count. Paginate on `pageInfo.endCursor` until
`hasNextPage` is false. A product can have more than 25 images; raise the inner
`first` or page the media connection if a product is truncated.

Collect the candidate `MediaImage` `id`s and write them via the `fileUpdate`
recipe above.

### Verify (read-only, Admin API)

Re-query the products you touched and confirm `alt` is populated. Do not check
the storefront; its CDN serves stale alt for minutes.

```graphql
query VerifyProductMediaAlt($id: ID!) {
  product(id: $id) {
    title
    media(first: 25, query: "media_type:IMAGE") {
      edges { node { ... on MediaImage { id alt } } }
    }
  }
}
```

---

## Find path 2: Files library

Files-library images are `MediaImage` nodes in the `files` connection (Content →
Files in admin). The connection returns mixed types (`MediaImage`, `GenericFile`,
`Video`, 3D models); filter to `MediaImage` with an `image/*` MIME type.

### Count / preview (read-only)

```graphql
query FilesMissingAlt($cursor: String) {
  files(first: 250, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        id
        alt
        __typename
        ... on MediaImage {
          mimeType
          image { url }
        }
      }
    }
  }
}
```

Client-side, a node is a candidate when all of these hold:

- `__typename == "MediaImage"`
- `alt` is null or empty after trimming
- `mimeType` starts with `image/`
- `image.url` is non-null

Count candidates across all pages (250 is the Admin API max page size) before
writing. Collect the candidate `id`s and write them via the `fileUpdate` recipe
above (the same mutation used for product media).

### Verify (read-only, Admin API)

Re-query by file `id` (or re-run the count and confirm it dropped by the number
you wrote). Confirm through the Admin API, not the storefront.

```graphql
query VerifyFileAlt($id: ID!) {
  node(id: $id) {
    ... on MediaImage { id alt }
  }
}
```

---

## Preflight the caption key (if using an LLM)

If you generate captions with a vision model, before the bulk run send one real
1-token completion and confirm a 200. A `models.list` / auth-only check is not
enough: a key that lists models can still fail on the actual completion (billing,
per-model access, org limits). Preflighting once saves discovering the failure
400 images into the sweep. Read the key from the env; never print or commit it.

---

## Notes

- **Whitespace-only alt counts as missing.** Trim before testing; a single space
  is not real alt text.
- **Decorative images want empty alt on purpose.** If an image is purely
  decorative, leave `alt` empty rather than inventing a caption, but that is a
  human call per image, not something a sweep should auto-fill.
- **Same asset, two entries, independent alt.** An asset used as both a product
  image and a Files entry has a distinct `MediaImage` GID in each place; writing
  one does not write the other. That is why there are two find paths even though
  there is one mutation.
