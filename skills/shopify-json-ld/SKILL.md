---
name: shopify-json-ld
description: >-
  Use when adding structured data / JSON-LD / schema markup to a Shopify store:
  recipe, FAQ, Article/BlogPosting, CollectionPage, AboutPage, or Organization
  schema; chasing Google rich-results / rich-snippet eligibility; debugging a
  Search Console "Invalid object type" or "missing field" schema error; or a
  request like "add schema to my store", "add recipe schema", or "why isn't my
  product showing rich results". This skill adds SUPPLEMENTAL JSON-LD the theme
  cannot emit dynamically, stored in a metafield and rendered by one Liquid
  snippet. Not for meta titles, meta descriptions, canonical tags, or Open Graph
  (use shopify-seo-metadata for those).
compatibility: >-
  Requires Shopify Admin API access (custom-app token or Shopify CLI 3.x) plus
  theme/Liquid edit access to add one render snippet. GraphQL written against
  Admin API 2025-07.
---

# Shopify JSON-LD

Adds **supplemental** structured data to a Shopify store: the schema types the
theme can't generate on its own (Recipe, FAQPage, richer Article/Collection
nodes), stored as JSON-LD in a per-entity metafield and rendered through a
single Liquid snippet. The governing principle: **you add what's missing, you
never duplicate what the theme already emits.** For meta tags, descriptions, and
Open Graph (a different job), use the sibling skill **shopify-seo-metadata**.

## Store access

**Lane A: custom-app token (scriptable).** In Shopify admin: Settings → Apps
and sales channels → Develop apps → create an app → grant this skill's minimum
scopes, then install and copy the Admin API access token. Export it; never write
it to a committed file:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="<your Admin API access token>"   # env only, not on disk
```

Minimum scopes: `read_products`, `write_products`, `read_content`,
`write_content`. There is no standalone metafield scope; metafield access is
governed by the owning resource's scope (products → `write_products`,
pages/articles → `write_content`). Rendering the snippet needs **theme edit
access** (theme editor or the theme's Git repo), which is separate from the API.
Sanity-check the token:

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name } }"}'
```

**Lane B: Shopify CLI OAuth (no stored token).** `shopify store auth --store
$SHOPIFY_STORE --scopes read_products,write_products,read_content,write_content` then
`shopify store execute`. Good for token-less stores where the owner logs in.

For the full Admin GraphQL schema, use Shopify's official AI toolkit plugin:
that gives your agent the API; this skill gives it the playbook.


## Supplemental-only doctrine: audit before you generate

Modern Shopify themes already emit Product schema on PDPs (price, variants,
availability, and, with a review app like Judge.me, Yotpo, or Stamped,
`aggregateRating`), plus Organization/WebSite sitewide and often
Article/BreadcrumbList. **Duplicating any of it creates conflicting nodes that
degrade eligibility, not improve it.**

So the first move is always read-only: fetch the homepage, a PDP, a collection,
and a blog post, and extract every `<script type="application/ld+json">` block.

```bash
curl -s "https://$SHOPIFY_STORE/products/<some-handle>" \
  | grep -o '<script type="application/ld+json">[^<]*' | head
```

Whatever the theme already covers, you do **not** touch. Supplemental schema is
a *separate* type on the same page (a FAQPage or Recipe node alongside the
theme's Product node), never a second Product node. If the theme's Product
schema is broken or missing, fix the theme. Don't paper over it with a
duplicate.

## The metafield + snippet pattern

Store the JSON-LD in a metafield and render it verbatim. Nothing transforms the
value at render time, so the stored string must already be valid JSON-LD.

1. **Define the metafield** (Settings → Custom Data → the entity type → Add
   definition): namespace `custom`, key `json`, type `multi_line_text_field`.
   Create it for each entity type you'll populate (Products, Collections, Pages,
   Articles).

2. **Add one render snippet** to `theme.liquid`, before `</head>`:

```liquid
{%- if request.page_type == 'product' and product.metafields.custom.json != blank -%}
  <script type="application/ld+json">{{ product.metafields.custom.json }}</script>
{%- elsif request.page_type == 'collection' and collection.metafields.custom.json != blank -%}
  <script type="application/ld+json">{{ collection.metafields.custom.json }}</script>
{%- elsif request.page_type == 'page' and page.metafields.custom.json != blank -%}
  <script type="application/ld+json">{{ page.metafields.custom.json }}</script>
{%- elsif request.page_type == 'article' and article.metafields.custom.json != blank -%}
  <script type="application/ld+json">{{ article.metafields.custom.json }}</script>
{%- endif -%}
```

3. **Write the value with `metafieldsSet`** (GraphQL). It upserts by
   namespace/key, so it updates an existing metafield instead of duplicating it:
   this sidesteps the classic REST trap of POSTing a second metafield when one
   already exists. Store the JSON compact (`JSON.stringify(obj)`, no pretty
   spacing). Preview the target count before a bulk write; a count far above
   expectation means stop and re-scope. Full pipeline and per-entity prompts:
   [references/pipeline-and-prompts.md](references/pipeline-and-prompts.md).

## Two schema rules that are non-negotiable

Google validates **every** typed node it finds, including deeply nested ones. A
single malformed node fails the whole block. Two rules prevent nearly all of it:

- **No bare `Product` nodes.** Google requires `offers`, `review`, or
  `aggregateRating` on every `@type: "Product"`. In supplemental schema you
  rarely have those (the theme owns them), so referencing a product by name uses
  `@type: "Thing"`, never `Product`.
- **No partial `VideoObject` nodes.** `VideoObject` requires `name`,
  `description`, `thumbnailUrl`, `uploadDate`, and a `contentUrl` or `embedUrl`.
  If you don't have real video metadata, don't emit `VideoObject`: use `Thing`
  or an `ItemList` of `ListItem` entries instead.

These two mistakes are the usual cause of "Invalid object type for field" and
"missing field" errors in Search Console.

## FAQPage is not a rich-result win anymore

Google **removed FAQ rich results for non-authoritative (commerce) sites in
2026.** FAQPage markup on a product or store page will no longer render the
expandable Q&A snippet in search. It's still valid structured data and still
feeds machine understanding of the page, but **do not sell or promote it as a
rich-result / SERP-visibility win**. That claim is stale. Recipe, and where
genuinely applicable Article, remain eligible; verify current eligibility per
type against Google's docs (see Provenance) before promising a visible result.

## Hallucination-guarded generation

When an agent generates FAQ or descriptive schema from product/page content, it
**may only assert facts present in the source text.** No invented dimensions,
weight limits, materials, or features. If the source description is thin,
generate fewer entries: three grounded Q&As beat five with two fabricated
answers, and a fabricated spec in schema is a factual claim Google (and the
customer) can catch. The prompt must prohibit fabrication explicitly and prefer
"omit" over "guess". Per-entity prompt scaffolding is in the reference.

## Verify against the Admin API, not the storefront

After a write, the storefront can serve the **old** JSON-LD for minutes to hours:
Shopify's CDN caches the rendered page. Confirm the write by reading the
metafield **back through the Admin API**, not by curling the product page:

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ product(id:\"gid://shopify/Product/<ID>\") { metafield(namespace:\"custom\",key:\"json\"){ value } } }"}'
```

The metafield value is ground truth. Once it's correct, the storefront will
catch up on its own cache cycle: that lag is not a bug to chase.

## Non-destructive defaults

- Read before you write; a blank metafield cell in a bulk update **deletes** the
  value, it doesn't skip it. Fill-missing-only unless overwrite is intended.
- Back up before a bulk write (export the existing `custom.json` values first).
- Never print or commit the Admin API access token; read it from the env.

## References

- [references/pipeline-and-prompts.md](references/pipeline-and-prompts.md): the
  generation pipeline (fetch → filter → generate → validate → write) and
  per-entity prompt recipes (Product FAQ, Recipe, Collection, Page, Article),
  loaded on demand.

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions quarterly, so confirm the version before trusting a
version-specific claim. **Google's rich-result eligibility changes**: FAQ rich
results were deprecated for commerce sites, and other types shift too, so
re-verify per schema type against
[Google's structured-data docs](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)
before promising a visible SERP result. Canonical type definitions live at
[schema.org](https://schema.org/). Read-only re-verification a stranger can run:

```bash
# 1. Confirm the token reaches the store.
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name } }"}'

# 2. Confirm a product page actually renders a JSON-LD block.
curl -s "https://$SHOPIFY_STORE/products/<some-handle>" \
  | grep -c 'application/ld+json'
```

Then validate any live URL in Google's Rich Results Test
(https://search.google.com/test/rich-results). These skills capture operational
lessons the docs don't; they don't replace the schema.org or Google references.
