# SEO metadata: queries, mutations, and prompts

Copy-and-adapt recipes for the four entity types. Every one follows the same
loop: **read (with existing SEO) → count the blanks → generate only the missing
field → write → read back.** GraphQL is pinned to Admin API 2025-07; verify
against [shopify.dev](https://shopify.dev/docs/api/admin-graphql) before a run.

Two storage shapes to keep straight:

- **Products and collections** expose a first-class `seo { title description }`
  field, written through `productUpdate` / `collectionUpdate`.
- **Pages and blog articles** have no `seo` field. Their search-appearance
  metadata lives in two reserved metafields, `global.title_tag`
  (`single_line_text_field`) and `global.description_tag`
  (`multi_line_text_field`), read and written like any other metafield.

"Missing" means the field is absent or an empty string. That test is the entire
safe-mode contract; apply it identically in the count and in the write loop.

---

## Products

**Read (paginate with `after`/`endCursor`):**

```graphql
query($cursor: String) {
  products(first: 100, after: $cursor, query: "status:active") {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      descriptionHtml
      seo { title description }
    }
  }
}
```

**Count needing a backfill** (client-side over the paginated read): increment
when `descriptionHtml` is non-empty (something to summarize) AND at least one of
`seo.title` / `seo.description` is blank. This is your preview number: sanity
check it before writing.

**Write (fill only the blank subfield):**

```graphql
mutation($input: ProductInput!) {
  productUpdate(input: $input) {
    product { id seo { title description } }
    userErrors { field message }
  }
}
```

```json
{ "input": { "id": "gid://shopify/Product/123",
             "seo": { "title": "<generated or existing>",
                      "description": "<generated or existing>" } } }
```

`seo` is a whole-object write: pass the existing value back for the subfield that
was already populated, and only the newly generated string for the one that was
blank. A `userErrors` array of length 0 is a *claim*: read `product { seo }`
back to confirm.

---

## Collections

**Read:**

```graphql
query($cursor: String) {
  collections(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      description
      seo { title description }
    }
  }
}
```

**Count:** increment when `seo.title` or `seo.description` is blank. Source text
for generation = `description` (fall back to `title` when the description is
empty).

**Write:**

```graphql
mutation($input: CollectionInput!) {
  collectionUpdate(input: $input) {
    collection { id seo { title description } }
    userErrors { field message }
  }
}
```

Same fill-only-the-blank rule as products.

---

## Pages

**Read (existing SEO comes from the `global` metafields):**

```graphql
query($cursor: String) {
  pages(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      bodySummary
      seoTitle: metafield(namespace: "global", key: "title_tag") { value }
      seoDesc:  metafield(namespace: "global", key: "description_tag") { value }
    }
  }
}
```

**Count:** increment when `seoTitle.value` or `seoDesc.value` is null/empty.
Source text = `bodySummary` (fall back to `title`).

**Write (metafields, not a `seo` field):**

```graphql
mutation($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { key value }
    userErrors { field message }
  }
}
```

```json
{ "metafields": [
  { "ownerId": "gid://shopify/Page/123", "namespace": "global",
    "key": "title_tag", "type": "single_line_text_field",
    "value": "<generated title>" },
  { "ownerId": "gid://shopify/Page/123", "namespace": "global",
    "key": "description_tag", "type": "multi_line_text_field",
    "value": "<generated description>" }
] }
```

Only include the metafield(s) whose field was blank: `metafieldsSet` overwrites
any key you pass, so passing a key you meant to leave alone would clobber a
human-written value. Send the blank one(s) only.

---

## Blog articles

**Read (same metafield storage as pages; parent blog title adds context):**

```graphql
query($cursor: String) {
  articles(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      summary
      blog { title }
      seoTitle: metafield(namespace: "global", key: "title_tag") { value }
      seoDesc:  metafield(namespace: "global", key: "description_tag") { value }
    }
  }
}
```

**Count:** increment when `seoTitle.value` or `seoDesc.value` is null/empty.
Source text = `summary` (fall back to `title`); pass `blog.title` into the
prompt for topical context.

**Write:** identical `metafieldsSet` mutation as pages, with
`ownerId: gid://shopify/Article/…`. Send only the blank field(s).

---

## Prompt guidance

Generate the two fields as one JSON object so the model reasons about them
together:

```
You are an SEO writer for {MERCHANT}.
Store positioning: {ONE_PARAGRAPH_BRAND_DESCRIPTION}

Return JSON with keys "meta_title" and "meta_description" for this
{product|collection|page|article}'s Google search-result snippet.

meta_title:
- Max ~60 characters. Google truncates longer titles in results.
- Front-load the single primary keyword a buyer would actually search.
- Title Case. No ALL CAPS, no promotional language, no extra whitespace.

meta_description:
- ~150-160 characters.
- Include the primary keyword once, naturally. Summarize the real benefit.
- No HTML, no keyword stuffing, no "Buy now!!!" promo tone.

Source title: {TITLE}
Source content: {BODY_OR_SUMMARY}
```

Three things the model can't infer, so you must supply or enforce them:

- **Positioning is load-bearing.** The `{ONE_PARAGRAPH_BRAND_DESCRIPTION}` (who
  the store sells to, its voice, its category) is what separates on-brand copy
  from generic filler. A thin or wrong description yields off-brand meta at
  scale. Write a real one.
- **Enforce length in code.** Models cannot count characters. After generation,
  measure both strings; if either is over its limit, re-prompt with "your
  previous answer was N characters, over the limit; rewrite to fit." Do not
  trust the stated limit alone.
- **Keyword restraint.** One primary keyword, front-loaded, written for a human
  reading a search result. Repetition and caps read as spam to both Google and
  buyers.

For structured output, request JSON mode / a JSON response format so parsing is
deterministic rather than scraping prose.
