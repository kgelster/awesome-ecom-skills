---
name: shopify-seo-metadata
description: >-
  Use when a store has missing SEO titles or meta descriptions and you want to
  backfill them: "backfill missing SEO titles/descriptions", "meta description
  sweep", "SEO meta backfill across products/collections/pages/blog posts",
  "missing page titles", "fix blank search-appearance metadata", "generate SEO
  meta for products". Safe-mode: fills only the empty search-appearance fields
  (SEO title, meta description) on products, collections, pages, and blog
  articles, never touching human-written values. Not for image alt text (use
  shopify-alt-text) or JSON-LD (use shopify-json-ld).
compatibility: >-
  Requires Shopify Admin API (custom-app token or Shopify CLI 3.x); GraphQL
  written against Admin API 2025-07. Minimum scopes: read_products,
  write_products (products/collections), plus read_content, write_content for
  pages and blog articles. Generation needs an LLM API key.
---

# Shopify SEO Metadata

Safe-mode backfill of **missing** search-appearance metadata (the SEO title and
meta description Google shows in the results snippet) across products,
collections, pages, and blog articles. The core principle: **fill blanks, never
overwrite**. A merchant's hand-written meta title is worth more than anything a
model generates; this skill only touches fields that are empty.

Sister skill `shopify-alt-text` runs the same fill-missing backfill for
product-image alt text; `shopify-json-ld` handles structured data. To first
measure how much metadata is missing store-wide, `shopify-catalog-audit` is the
FIND stage that scopes this FIX.

## Store access

Every skill that touches the Admin API opens with this stanza (minimum scopes
for *this* skill below). Two lanes; pick one.

**Lane A: custom-app token (scriptable).** In Shopify admin: Settings → Apps
and sales channels → Develop apps → create an app → grant the scopes below, then
install and copy the Admin API access token. Export it; never write it to a
committed file:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="<your Admin API access token>"   # env, not disk
```

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name } }"}'
```

**Lane B: Shopify CLI OAuth (no stored token).** `shopify store auth --store
$SHOPIFY_STORE --scopes read_products,write_products,read_content,write_content`
then `shopify store execute` to run a validated operation. Good for token-less
stores where the owner logs in interactively.

**Minimum scopes for this skill:** `read_products` + `write_products` cover
products and collections (both live on the products scope). Pages and blog
articles need `read_content` + `write_content`. Scope only what the run touches.

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

Every GraphQL block in [references/queries-and-prompts.md](references/queries-and-prompts.md)
is a copy-and-adapt starting point. Write throwaway code per engagement against
the current schema, run it, discard it. Two rules keep a metadata backfill safe.

## Safe mode is the whole job

State this out loud before any run, and treat it as non-negotiable:

1. **Fill missing ONLY. Never overwrite a value that already exists.** For each
   entity, read `seo { title description }` (products/collections) or the
   `global.title_tag` / `global.description_tag` metafields (pages/articles)
   FIRST. A field with a non-empty value is skipped, full stop. An "overwrite
   everything" mode is a different, deliberate job: it is never the default and
   a stranger running this skill does not get it for free.
2. **Fill the two fields independently.** A product can have a title but no
   description. Generate and write only the blank one; leave the populated one
   byte-for-byte untouched.

## Preview first, then mutate

Never open a bulk write without a number in front of you.

1. **Run the read-only COUNT** (per entity, in the reference) of how many items
   have a *missing* field. This is the exact count the mutation loop will act
   on, using the same skip logic.
2. **Sanity-check the number against expectation.** A 40-product store reporting
   3,000 items needing SEO means the skip logic is wrong or you are pointed at
   the wrong store. A count far above expectation means **STOP and re-scope**:
   do not proceed into a mutation run to "see what happens." An unscoped write
   over a catalog is not free to undo.
3. Only after the count is sane do you generate and write.

## Preflight the LLM key with a real completion

Before a bulk run, send the generation model a **real 1-token completion**, not
a `models.list()` / model-listing call. A key with read access to the model list
can still fail on an actual completion (billing lapsed, org quota, wrong
project). A dead key discovered mid-run burns the whole queue as failed rows and
wastes the crawl. One tiny completion up front is the cheapest insurance there
is.

## Generate, write, verify: per entity

For each entity type the shape is identical; only the read query, the write
mutation, and the content source field differ (all four are in the reference):

- **Products:** source = product title + body HTML. Write via `productUpdate`
  with `input.seo { title description }`.
- **Collections:** source = collection title + description. Write via
  `collectionUpdate`, same `seo` input.
- **Pages:** source = title + `bodySummary`. SEO lives in `global.title_tag`
  (single line) and `global.description_tag` (multi line) metafields; write via
  `metafieldsSet`.
- **Blog articles:** source = title + `summary` (+ parent blog title for
  context). Same `global.*_tag` metafields, same `metafieldsSet`.

Log every write (resource id, field, old value, new value, status) to a CSV or
newline log as you go. That log is your evidence and your retry list.

## Verify AFTER the write: via the Admin API, never the storefront

A mutation returning no `userErrors` is a *claim*, not proof. Confirm it:

- After the run, re-read `seo { title description }` (or the `global.*_tag`
  metafields) for 2–3 written resources through
  `admin/api/2025-07/graphql.json` and confirm the value matches what you wrote.
- **Read back through the Admin API, not the storefront.** The storefront `<meta>`
  tags are CDN-cached and lie about freshness: a stale edge page will show the
  old (or empty) tag long after the write landed, sending you chasing a
  non-bug. The Admin API is the source of truth.

## Prompt guidance

Quality of the generated meta depends on three things the model can't infer:

- **Feed the store's positioning into every prompt.** A one-paragraph brand
  description (who they sell to, the voice, the category) is the difference
  between on-brand copy and generic filler. A thin or wrong description produces
  off-brand meta at scale: write a real one before a bulk run.
- **Length targets.** SEO title ~50–60 characters (Google truncates past ~60);
  meta description ~150–160. Models cannot count characters reliably, so
  validate length in code and re-prompt anything over the limit rather than
  trusting the model to obey.
- **No keyword stuffing.** Front-load the one primary keyword a buyer would
  actually search, write for a human reading a result, and stop. Repeated
  keywords and ALL-CAPS promo language read as spam and help nothing.

Full query/mutation/prompt detail:
[references/queries-and-prompts.md](references/queries-and-prompts.md).

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions on a rolling quarterly schedule, so verify the `seo` field
and the resource mutations against
[shopify.dev](https://shopify.dev/docs/api/admin-graphql) before trusting a
version-specific claim. Read-only re-verification a stranger can run, confirming
the token reaches the store and the `seo` field resolves on products:

```bash
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ products(first: 3) { nodes { title seo { title description } } } }"}'
```

Canonical docs: the `seo` field on resources and the metafield model at
[Admin GraphQL](https://shopify.dev/docs/api/admin-graphql). This skill captures
the operational safe-mode doctrine the reference doesn't; it is not a
replacement for it.
