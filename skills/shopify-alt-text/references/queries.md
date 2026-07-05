# Alt-text recipes: product media and Files library

Copy-and-adapt GraphQL for the two surfaces. Every mutation is preceded by the
read-only count/preview for the same surface. Run the count, sanity-check it,
then mutate; re-query to verify. Pin the API version in the URL
(`/admin/api/2025-07/graphql.json`).

The candidate rule is identical for both surfaces: an image qualifies only when
its alt is null or empty after trimming whitespace, its type is an image
(`MediaImage`), and it has a resolvable URL. Never touch an image that already
has alt.

---

## Surface 1 — Product media (`productUpdateMedia`)

Product images are `MediaImage` nodes under a product's `media` connection.
Filtering by `mediaContentType: IMAGE` keeps videos and 3D models out.

### Count / preview (read-only)

Page products, count image media with empty `altText`. Do this first and read
the number back before any write.

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
                altText
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

Client-side, a media node is a candidate when `altText` is null or
`altText.trim() == ""`. Sum candidates across all pages for the preview count.
Paginate on `pageInfo.endCursor` until `hasNextPage` is false. A product can
have more than 25 images; raise the inner `first` or page the media connection
if a product is truncated.

### Update (`productUpdateMedia`)

`productUpdateMedia` updates media that already belong to a product. It takes the
`productId` and a list of `media`, each keyed by the media `id` with the new
`alt`. Batch a handful of images per call for one product; keep the batch small
so a single bad node doesn't fail the set.

```graphql
mutation SetProductMediaAlt($productId: ID!, $media: [UpdateMediaInput!]!) {
  productUpdateMedia(productId: $productId, media: $media) {
    media {
      ... on MediaImage { id altText }
    }
    mediaUserErrors { field message code }
  }
}
```

Variables (fill missing only — every `id` here came from the count as a
candidate):

```json
{
  "productId": "gid://shopify/Product/1234567890",
  "media": [
    { "id": "gid://shopify/MediaImage/1111", "alt": "Front view of the item on a plain background" },
    { "id": "gid://shopify/MediaImage/2222", "alt": "Close-up of the stitched seam and hardware" }
  ]
}
```

Check `mediaUserErrors` on every response — an empty array is the only success.
Throttle writes (roughly one call per half-second) to stay under the Admin API
rate limit; the GraphQL bucket is cost-based, so watch `throttleStatus` if you
parallelize.

### Verify (read-only, Admin API)

Re-query the products you touched and confirm `altText` is now populated. Do not
check the storefront — its CDN serves stale alt for minutes.

```graphql
query VerifyProductMediaAlt($id: ID!) {
  product(id: $id) {
    title
    media(first: 25, query: "media_type:IMAGE") {
      edges { node { ... on MediaImage { id altText } } }
    }
  }
}
```

---

## Surface 2 — Files library (`fileUpdate`)

Files-library images are `MediaImage` nodes in the `files` connection (Content →
Files in admin). The connection returns mixed types (`MediaImage`,
`GenericFile`, `Video`, 3D models); filter to `MediaImage` with an `image/*` MIME
type. `fileUpdate` only accepts `alt` for image files anyway — PDFs and videos
are skipped.

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
writing.

### Update (`fileUpdate`)

`fileUpdate` takes a list of `FileUpdateInput`, each with the file `id` and new
`alt`.

```graphql
mutation SetFileAlt($files: [FileUpdateInput!]!) {
  fileUpdate(files: $files) {
    files { id alt }
    userErrors { field message code }
  }
}
```

Variables:

```json
{
  "files": [
    { "id": "gid://shopify/MediaImage/3333", "alt": "Store logo on a dark banner" }
  ]
}
```

An empty `userErrors` array is success; a populated `files` array echoes the new
alt. Batch a few files per call, throttle to stay under the rate limit, and cap
each caption at 125 characters before sending.

### Verify (read-only, Admin API)

Re-query by file `id` (or re-run the count and confirm it dropped by the number
you wrote). Confirm `alt` is populated through the Admin API, not the storefront.

```graphql
query VerifyFileAlt($id: ID!) {
  node(id: $id) {
    ... on MediaImage { id alt }
  }
}
```

---

## Notes

- **Whitespace-only alt counts as missing.** Trim before testing; a single space
  is not real alt text.
- **Decorative images want empty alt on purpose.** If an image is purely
  decorative, leave `alt` empty rather than inventing a caption — but that is a
  human call per image, not something a sweep should auto-fill.
- **Two surfaces, independent alt.** The same underlying asset used as both a
  product image and a Files entry carries separate alt on each; fixing one does
  not fix the other.
