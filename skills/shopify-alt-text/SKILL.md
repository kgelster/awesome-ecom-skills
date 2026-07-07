---
name: shopify-alt-text
description: >-
  Use when backfilling missing image alt text on a Shopify store: images with no
  alt attribute, accessibility alt text for product images, alt text for Files
  library images, image SEO, or a WCAG/accessibility pass that flags images
  missing text alternatives. Triggers: "backfill alt text", "fill in missing alt
  text", "images have no alt", "add alt attributes for accessibility", "image
  SEO sweep". One mutation, fileUpdate, covers both product media and the Files
  library. Not for meta titles/descriptions (use shopify-seo-metadata).
compatibility: >-
  Requires Shopify Admin API access (custom-app token or Shopify CLI 3.x).
  GraphQL written against Admin API 2025-07. Scopes: `read_products` to enumerate
  product-image owners, `read_files` to page the Files library, `write_files`
  because `fileUpdate` writes alt for both.
---

# Shopify Alt Text

Backfill missing image alt text across a Shopify store. Alt text is an
accessibility requirement first (screen readers announce it) and an image-SEO
signal second. This skill fills the gap for images that have none; it does not
rewrite alt text that already exists.

The sister backfill for SEO titles and descriptions is **shopify-seo-metadata**:
same safe-mode doctrine, different fields. The FIND stage (measuring how many
images lack alt across the catalog before you commit to a sweep) belongs to
**shopify-catalog-audit**.

## One mutation, two find paths

Images live in two places on a Shopify store, but both write through the **same
mutation**. A product image and a Files-library image are both `MediaImage`
nodes, which are `File` subtypes, so a single `fileUpdate` sets `alt` on either.
There is no separate product-media alt mutation to learn.

- **`fileUpdate` is the one write.** It takes the image's `MediaImage` GID and
  the new `alt`. This is the write path both source tools converge on. (Shopify's
  old `productUpdateMedia` is **deprecated on shopify.dev; do not use it** for
  alt text.)
- **Two ways to FIND the images, one way to fix them:**
  - *Product media:* page products, read each `MediaImage` under `product.media`.
    Needs `read_products`.
  - *Files library:* page the `files` connection (Content → Files: theme
    sections, metaobjects, rich-text, collection banners). Needs `read_files`.
  - Both hand you `MediaImage` GIDs; feed those straight into `fileUpdate`.

Full count/fetch/update/verify recipes for both find paths are in
[references/queries.md](references/queries.md).

## Store access

Every skill that touches the Admin API opens with this stanza. Two lanes; pick
one.

**Lane A, custom-app token (scriptable).** In Shopify admin: Settings → Apps
and sales channels → Develop apps → create an app → grant the minimum scopes
below, then install and copy the Admin API access token. Export it; never write
it to a committed file:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="<your Admin API access token>"   # keep it in the env, not on disk
```

Call the GraphQL endpoint (minimum scopes for this skill: `read_products` to
enumerate product-image owners, `read_files` to page the Files library, and
`write_files` because `fileUpdate` writes alt for both):

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name } }"}'
```

**Lane B, Shopify CLI OAuth (no stored token).** `shopify store auth --store
$SHOPIFY_STORE --scopes read_products,read_files,write_files` then `shopify store
execute` to run a validated operation. Good for token-less stores where the owner
logs in interactively.

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

## Recipes, not scripts

This is a **recipe, not a program.** The GraphQL blocks in the reference are
copy-and-adapt starting points: write throwaway code per engagement against the
current schema, run it, discard it. Do not ship a standing binary that silently
rots when Shopify changes the schema.

## Safe-mode / preview / verify doctrine

State it standalone, run it every time. This is a bulk write against a live
store; the difference between a clean sweep and a support ticket is discipline.

1. **Fill missing only, never overwrite.** Treat an image as a candidate only
   when its `alt` is null or empty after trimming whitespace. An image that
   already has alt text, even mediocre alt text, is out of scope. Overwriting
   existing alt is a separate, deliberate decision a human makes per-image, never
   the default of a sweep.
2. **Preview a read-only count first.** Before any mutation, run the count query
   for the find path you are about to touch and read the number back.
   Sanity-check it: a store with 300 products and "1,900 product images missing
   alt" is plausible; "40,000 missing" on the same store means your filter is
   wrong (probably counting non-image files or already-captioned images). A count
   far above expectation means stop and re-scope, not proceed.
3. **Preflight the generation API key with a real 1-token completion.** If you
   caption images with an LLM, before the bulk run send one real (cheap,
   1-token) completion and confirm a 200. Do **not** trust a `models.list` /
   auth-only check: a key that lists models can still fail on the actual
   completion (billing, per-model access, org limits), and you find out 400
   images into the sweep instead of before it.
4. **Log every write, then verify against the Admin API.** Keep a per-write log
   (image GID, find path, old alt, new alt, status) so a bad batch is auditable
   and reversible. After writing, re-query the same images through
   `admin/api/.../graphql.json` and confirm `alt` is populated. The storefront is
   CDN-cached and shows stale (empty) alt for minutes; it is not evidence the
   write landed. The reference has the readback query.
5. **Never print or commit the Admin API access token or the generation key.**
   Read both from the env.

## What good alt text is

Alt text describes the image for someone who cannot see it. It is not a place to
stuff keywords or repeat the product's sales pitch.

- **Describe the image, not the marketing.** "Brown leather weekender bag with
  brass zipper, side view", not "premium handcrafted bag, free shipping, shop
  now."
- **Keep it under ~125 characters.** Screen readers read the whole string;
  long alt is punishing to listen to. Most screen-reader guidance treats ~125
  chars as the practical ceiling. Cap generated captions at 125 before writing.
- **No keyword stuffing.** Repeating the product title plus a list of search
  terms hurts the accessibility use it exists for and reads as spam to search
  engines. One natural description.
- **Skip decorative and duplicate images.** A pure background texture or a
  spacer needs empty alt (`alt=""`), not a caption. If five images on a product
  are near-identical angles, they do not each need a distinct paragraph;
  differentiate only what a sighted user would notice ("front", "back",
  "worn on model").
- **No "image of" / "photo of" prefixes.** Screen readers already announce that
  it is an image; the prefix is redundant noise. Strip it if a generator adds it.

If you generate captions from the image (vision model), still gate every write
through the safe-mode rules above. Canonical guidance: the W3C WAI
[alt-text decision tree](https://www.w3.org/WAI/tutorials/images/decision-tree/).

## References

- [references/queries.md](references/queries.md): count / fetch / update /
  verify recipes for both find paths (product media and the Files library), all
  writing through `fileUpdate`, with pagination and MIME filtering.

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions on a rolling quarterly schedule, so confirm `fileUpdate`
against [shopify.dev](https://shopify.dev/docs/api/admin-graphql) before trusting
a version-specific claim. `productUpdateMedia` is deprecated; `fileUpdate` is the
current alt-text write for both product media and Files. Read-only
re-verification a stranger can run, listing product media and seeing which lack
alt while mutating nothing:

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ products(first: 5) { edges { node { title media(first: 10) { edges { node { ... on MediaImage { id alt } } } } } } } }"}'
```

Canonical docs:
[fileUpdate](https://shopify.dev/docs/api/admin-graphql/latest/mutations/fileUpdate)
and the [WAI images tutorial](https://www.w3.org/WAI/tutorials/images/). These
skills capture operational lessons the docs don't; they are not a replacement for
the reference.
