---
name: shopify-category-taxonomy
description: >-
  Use when you assign the Shopify Standard Product Taxonomy category, "set the
  product category", "categorize the catalog", or fill the category / taxonomy
  metafields: the admin "Category metafields" panel (Color, Size, Material,
  Caffeine content), a.k.a. product category attributes / taxonomy attributes,
  including the attributes a Google feed asks for.
  Covers bulk classification, discovering a category's attributes and allowed
  values, minting the reserved value metaobjects, and writing them safely. Also:
  "category metafields show blank/null", "my Color attribute won't save". Not
  for bulk CSV data loads (Matrixify can't do this; see shopify-matrixify for
  bulk data).
compatibility: >-
  Shopify Admin API 2025-07 (GraphQL). Needs read_products + write_products AND
  read_metaobjects + write_metaobjects. The metaobjects scopes are the #1 trap:
  without read_metaobjects the values return null and look unwritable.
---

# Shopify Category Taxonomy

Two jobs that chain together: **assign** a product's Standard Product Taxonomy
category (Part 1), then **fill** the category metafields that category exposes
(Part 2). You cannot do Part 2 until Part 1 is true: the "Category metafields"
panel only exists once a product is assigned to a category. Bulk CSV data work
lives in the sibling `shopify-matrixify`; the one thing Matrixify **cannot** do
is mint the reserved value metaobjects Part 2 needs, which is the entire reason
this skill exists.

## Store access

**Lane A: custom-app token (scriptable).** Shopify admin → Settings → Apps and
sales channels → Develop apps → create an app → grant the four scopes below →
install → copy the Admin API access token. Export it; never write it to disk:

```bash
export SHOPIFY_STORE="your-store.myshopify.com"
export SHOPIFY_ACCESS_TOKEN="<your Admin API access token>"   # env, not disk
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" -d '{"query":"{ shop { name } }"}'
```

Minimum scopes: **`read_products`, `write_products`, `read_metaobjects`,
`write_metaobjects`.** The metaobjects pair is not optional (see the null trap).

**Lane B: Shopify CLI OAuth (no stored token).** `shopify store auth --store
$SHOPIFY_STORE --scopes read_products,write_products,read_metaobjects,write_metaobjects`
then `shopify store execute`. Good for token-less stores where the owner logs in
interactively. For the full Admin GraphQL schema, use Shopify's official AI
toolkit plugin. That gives your agent the API; this skill gives it the playbook.

## Recipes, not scripts

Treat every GraphQL block as a copy-and-adapt recipe your agent writes fresh,
runs, and discards. Two rules keep that safe:

1. **Preview before you mutate.** Precede every write with a read-only count of
   the products in the target category and sanity-check it. A count far above
   expectation means stop and re-scope.
2. **Non-destructive defaults.** Fill missing only; a blank value in
   `metafieldsSet` **deletes** the metafield, so only emit non-blank values.
   Abort the run on first-batch `userErrors`.

Verify against ground truth via the Admin API, not the storefront (CDN-cached,
lies about freshness). Never print or commit the token.

## Part 1: Assign the category

Set each product's `category` field to a Standard Product Taxonomy category via
`productUpdate` (or the Matrixify `Category` column for a pure bulk load).

**CRITICAL: verify every category ID against the official taxonomy source; never
guess an ID.** A guessed taxonomy ID resolves to the *wrong* category or a dead
node, and it fails silently: the product looks categorized but every downstream
attribute, filter, and feed mapping is now wrong. Guessed IDs have burned real
product feeds. Resolve the ID by `search:` against `taxonomy { categories }`
(Part 2 step 1 shows the query), or from the official taxonomy repo linked in
Provenance.

Classification **signal priority** (highest to lowest confidence):
**title** (strongest lexical signal) > **product type** (good when populated,
many stores don't) > **vendor** (a mono-line vendor pins it, a multi-line one
doesn't) > **tags** (noisy, but often encode type on catalogs that tag by
category) > **description** (last resort; easy to mis-key on flavor words).

Emit a confidence flag per product. Ship the high-confidence rows; route the
ambiguous ones (bundles, samplers, cross-category items) to a human review sheet
rather than guessing.

```graphql
# preview: how many products land in this category assignment
mutation Assign($id: ID!, $cat: ID!) {
  productUpdate(product: {id: $id, category: $cat}) {
    product { id category { id fullName } }
    userErrors { field message }
  }
}
```

## Part 2: Fill the category metafields

A category metafield is **not** a plain text/choice value. It is a metafield in
the reserved `shopify` namespace, of type `list.metaobject_reference`, whose
value is a JSON array of **Metaobject GIDs**. Each of those metaobjects is a
reserved taxonomy value (`type: "shopify--<attribute>"`) with a `label` and a
`taxonomy_reference` pointing at a global `TaxonomyValue`. The chain:

```
Product
  └─ metafield  shopify.<attribute>  (list.metaobject_reference)
       └─ value: ["gid://shopify/Metaobject/…"]
            └─ Metaobject  type: shopify--<attribute>   label: "Decaf"
                 └─ taxonomy_reference ─▶ TaxonomyValue/26137  (global)
```

These value metaobjects are **minted on demand**: a store only holds
metaobjects for values it has actually used. A brand-new value must be created
before you can reference it. That mint-then-reference step is what Matrixify
cannot do.

**Top 5 gotchas (fuller list in the reference):**

1. **The null/scope trap.** Without `read_metaobjects`, the value metaobjects
   return `null` from `node()`, `references`, and `metaobjectDefinitions`: the
   whole feature looks read-only. With the scope they resolve. Minting needs
   `write_metaobjects`.
2. **A `TaxonomyValue` GID is rejected on write.** `metafieldsSet` demands the
   **Metaobject** GID, not the taxonomy value GID (else "Value require that you
   select a metaobject"). The TaxonomyValue GID is only the `taxonomy_reference`
   you pass when *creating* the metaobject.
3. **The product must already be in the category** or the metafield doesn't
   render as a category metafield. Scope targets by `product.category`, not by
   product type or title.
4. **GIDs are store-specific.** Metaobject GIDs minted in one store do not port
   to another. Re-mint per store.
5. **Matrixify cannot mint these.** It can't create the reserved metaobjects and
   won't resolve value names. The Admin API is the only reliable path.

### SOP

**1. Discover the category, its attributes, and allowed values.**

```graphql
query {
  taxonomy {
    categories(first: 1, search: "Tea & Infusions > Tea") {
      nodes {
        id fullName
        attributes(first: 50) {
          nodes {
            ... on TaxonomyChoiceListAttribute {
              id name
              values(first: 50) { nodes { id name } }   # id = TaxonomyValue GID
            }
            ... on TaxonomyMeasurementAttribute { id name }
          }
        }
      }
    }
  }
}
```

Record per attribute: the **metafield key** (the attribute handle,
lowercased-hyphenated, confirm it by reading an already-set product in step 4;
the Color attribute's key is `color-pattern`, not `color`) and the **value name →
TaxonomyValue GID** map.

**2. Mint each missing value metaobject (once per store).** Reuse an existing
metaobject when its `label` already matches; only mint when genuinely absent.

```graphql
mutation M($m: MetaobjectCreateInput!) {
  metaobjectCreate(metaobject: $m) {
    metaobject { id displayName } userErrors { field message code }
  }
}
# variables:
# {"m":{"type":"shopify--caffeine-content","handle":"decaf",
#   "fields":[{"key":"label","value":"Decaf"},
#             {"key":"taxonomy_reference","value":"gid://shopify/TaxonomyValue/26137"}]}}
```

Build a `value name → Metaobject GID` map from the results plus existing entries.

**3. Apply via `metafieldsSet`, batches of ≤25 metafields per call.**

```graphql
mutation S($m: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $m) {
    metafields { id } userErrors { field message code }
  }
}
# each entry: {ownerId, namespace:"shopify", key:"tea-variety",
#   type:"list.metaobject_reference",
#   value:"[\"gid://shopify/Metaobject/…\"]"}
```

Emit only non-blank values. Abort on first-batch errors.

**4. Verify by reading back resolved labels**, not by trusting the write's
`userErrors: []`.

```graphql
query { product(id: "gid://shopify/Product/…") {
  metafields(namespace: "shopify", first: 10) { nodes {
    key references(first: 5) { nodes { ... on Metaobject { displayName } } } } } } }
```

Spot-check several products; confirm every name resolves to what you intended.

## References

- [references/gotchas-and-scoping.md](references/gotchas-and-scoping.md):
  gotchas 6-10 (freeform labels, per-type mint fields, multi-category scoping),
  which surface each attribute reaches (Google feed vs Search & Discovery vs
  JSON-LD), and two worked examples with real numbers.

## Provenance and maintenance

Last verified: 2026-07-05. GraphQL pinned to Admin API 2025-07; Shopify
deprecates versions on a rolling quarterly schedule, so verify field shapes
against [shopify.dev](https://shopify.dev/docs/api/admin-graphql) and the
metafields/metaobjects docs before trusting a version-specific claim. The
category IDs and taxonomy values come from Shopify's
[Standard Product Taxonomy](https://github.com/Shopify/product-taxonomy): the
canonical source to verify an ID against; never guess one.

Read-only re-verification a stranger can run (no writes):

```bash
# 1. token reaches the store and reads a product's assigned category
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ products(first:1){ nodes{ category { id name } } } }"}'

# 2. taxonomy discovery resolves (confirms the taxonomy API + your read scope)
curl -s "https://$SHOPIFY_STORE/admin/api/2025-07/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ taxonomy { categories(first:1, search:\"Tea\"){ nodes{ id fullName } } } }"}'
```

These skills capture operational lessons the docs don't; they are not a
replacement for the reference.
