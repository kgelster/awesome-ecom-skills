# JSON-LD pipeline and per-entity prompt recipes

Detail loaded on demand from the `shopify-json-ld` skill. This is a **recipe**,
not a program: your agent writes throwaway code per engagement against the
current Admin API, runs it, and discards it. Everything here is a starting point
to adapt, not a binary to ship.

Worked numbers below come from a JSON-LD rollout on a baby-gear DTC brand
(~200 products, April 2026); the shape generalizes, the categories do not.

---

## The pipeline

Five stages, each with a checkpoint before the next:

1. **Fetch** entities from the Admin API, paginated (250/page). Products,
   collections (both custom and smart — they're separate resources), pages, and
   blog articles if the store blogs.
2. **Filter** to entities worth marking up (see Filtering below). Skip utility
   pages, gift cards, drafts, and duplicates.
3. **Generate** the JSON-LD per entity — deterministically where the shape is
   fixed (CollectionPage, Organization), with the model only where judgment is
   needed (FAQ Q&As, choosing an @type for a freeform page).
4. **Validate** every generated object *before* writing: parse it as JSON, then
   grep the serialized string for the forbidden `"Product"` and partial
   `"VideoObject"` patterns. A test batch of 3-5 entities gets eyeballed and, for
   flagship products, owner-reviewed before the full run.
5. **Write** via `metafieldsSet`, compact-serialized, upserting by
   namespace/key. Export the pre-existing values first as a backup.

### Fetch + write shape (GraphQL)

Read a page of products with their current `custom.json`:

```graphql
query($cursor: String) {
  products(first: 250, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id title handle descriptionHtml productType tags
      metafield(namespace: "custom", key: "json") { id value }
    }
  }
}
```

Upsert the generated JSON-LD (updates in place, never duplicates):

```graphql
mutation($mf: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $mf) {
    metafields { id namespace key }
    userErrors { field message }
  }
}
```

with each variable:

```json
{ "ownerId": "gid://shopify/Product/123",
  "namespace": "custom", "key": "json",
  "type": "multi_line_text_field",
  "value": "{\"@context\":\"https://schema.org\",\"@type\":\"FAQPage\", ...}" }
```

Always check `userErrors`. Rate-limit courtesy: small concurrent batches (≈5),
a short delay between them, and exponential backoff on 429/`THROTTLED`.

### Filtering

**Skip these pages** — flag any handle containing `subscribe`, `confirmation`,
`success`, `test`, `copy-of`, `nofraud`, or a fraud/cookie-declaration slug, plus
non-English translation pages unless you're targeting that market, and
abbreviated policy duplicates.

**Skip these products** — gift cards (no meaningful content), draft/unpublished
(`publishedAt` null), and inventory-planner or `copy-of` duplicate SKUs.

Review the full page list before running. Filtering wrong is how utility pages
end up with schema that confuses crawlers.

---

## Per-entity prompt recipes

Use the model **only for judgment** — grounded Q&A wording, @type selection.
Fixed-shape schema (Organization, most CollectionPage fields) is a deterministic
transform; don't route it through the model. Every prompt carries the two hard
rules from the skill (no bare `Product`, no partial `VideoObject`) and the
anti-fabrication rule.

### System prompt (shared)

State verbatim, every entity type:

```
- Output only valid JSON-LD. No prose, no code fences.
- NEVER use @type "Product". Google requires offers/review/aggregateRating on
  every Product node; the theme already emits those. Reference a product by name
  with @type "Thing".
- NEVER use @type "VideoObject" without ALL of: name, description, thumbnailUrl,
  uploadDate, and contentUrl or embedUrl.
- Assert ONLY facts present in the supplied content. Invent nothing — no
  dimensions, weights, materials, or capacities not in the source text. If the
  content is thin, produce fewer items. Omitting beats guessing.
```

### Product FAQ

Give the model: title, URL, full description (truncate ~2000 chars), product
type, tags, variant colors/price range, and a detected category for context.
Request **3-5 product-specific Q&As** as a FAQPage. Prohibit shipping/returns/
warranty/discount questions (those are site-wide, not product-specific) and
generic "check the product details" non-answers. Thin description → 3 max, or
skip. **Remember FAQ no longer earns a rich result for commerce sites** (see
skill) — generate it for machine understanding, not for a SERP promise.

Category detection is per-store: the baby-gear rollout mapped ~18 categories
(carrier, diaper bag, stroller, …) off title/type/tags. A jewelry or food store
needs its own mapping — analyze the catalog's product types and tags first.

For flagship/hero products, an owner may supply **pre-approved** FAQ copy. Build
that FAQPage by hand from the approved Q&As, write it directly, and exclude that
handle from the model batch.

### Recipe

For stores whose content is genuinely recipe-shaped (food, supplements, DIY),
Recipe schema is one of the types that **still earns a rich result** — worth
doing well. Require the real fields: `name`, `recipeIngredient` (a list),
`recipeInstructions` (`HowToStep` items), and where present `totalTime`
(ISO-8601 duration), `recipeYield`, `nutrition`. Pull all of it from the source
content; if ingredients or steps aren't actually in the text, it isn't a recipe
page — don't force the type.

### Collection

CollectionPage: `name`, `description` (write a concise one if none exists), URL,
`isPartOf` (the WebSite), `provider` (the Organization). Mostly deterministic;
the model only helps when a human-readable description must be composed.

### Page (freeform)

Let the model pick the @type from content: `AboutPage` (about/team), `ContactPage`
(contact), `FAQPage` (help/FAQ, with Question/Answer `mainEntity`), or `WebPage`
(policies, general info). One clearly-correct type beats a fancy wrong one.

### Blog article

Supplemental `BlogPosting` — the theme usually handles the base `Article`. Add
`articleSection`, `keywords` (4-8 specific terms drawn from the actual copy),
`about` (a `Thing`), `isPartOf` (the Blog), and `publisher` (Organization with
`logo`). Keywords must come from the real content, not the model's imagination.

---

## Validation checklist

Before the full run: test 3-5 entities across categories, confirm Q&As are
product-specific and answers trace to the source, and grep the output for the
forbidden `"Product"` / partial `"VideoObject"` strings.

After the full run: spot-check 5-10 live URLs in Google's Rich Results Test,
confirm your backup row count matches the entities written, and read a sample of
metafields **back through the Admin API** (not the storefront — the CDN lies)
to confirm the values landed. Watch Search Console for structured-data errors
over the following couple of weeks.
