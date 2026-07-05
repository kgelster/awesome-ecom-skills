# Category taxonomy — gotchas, scoping, and adjacent surfaces

Loaded on demand from the main skill. The top-5 gotchas live in SKILL.md; these
are the deeper ones plus the disambiguation of look-alike surfaces.

## Gotchas 6–10

**6. Different categories expose different attributes, keys, and values.** Never
carry one category's key set to another. A tea category's `caffeine-content` /
`tea-variety` keys mean nothing to an apparel category. Always run the discovery
query (SOP step 1) against the *target* category and rebuild the key/value map.

**7. The metafield key is not always the obvious attribute name.** The Color
attribute's metafield key is `color-pattern` (metaobject type
`shopify--color-pattern`), not `color`. Confirm every key by reading an
already-set product before you write — guessing `color` creates an orphan
metafield that never renders in the Category panel, so it looks like nothing
happened.

**8. Store value metaobjects can carry freeform labels beyond the official
taxonomy list.** The Color attribute has ~19 canonical taxonomy values, but a
store's `shopify--color-pattern` metaobjects may already include Navy, Charcoal,
Khaki, Army Green, Camouflage — each still pointing at a canonical
`taxonomy_reference`. Reuse an existing metaobject by **label match**; only mint
when the label is genuinely absent. Same pattern for Size: labels are short codes
(`2XL`) while the `taxonomy_reference` is the canonical value
(`Double extra large (XXL)` = TaxonomyValue/17091).

**9. A multi-category catalog is a scoping problem, not just a classification
one.** Apparel and lifestyle stores spread across dozens of categories, each with
a different attribute set. Pull the category distribution first (count active
products per `category.fullName`), then scope to the high-volume head. Gate each
attribute by "does this category actually expose it": Size exists on garment
categories but snapbacks / sports-hats / vehicle-decor expose **Accessory size**
instead, and their `ECH` / `EA` / `O/S` "size" option values are inventory units,
not garment sizes — don't write them.

**10. The mint field set differs per metaobject type — check before creating.**
The `label` + `taxonomy_reference` pair is the shape for *simple* attributes
(caffeine-content, size, and most choice lists). `shopify--color-pattern` is the
exception: it requires **`color_taxonomy_reference`** (a *list* of TaxonomyValue
GIDs) plus **`pattern_taxonomy_reference`** (single — Solid for hex swatches,
Other for image swatches), or `metaobjectCreate` fails with
`OBJECT_FIELD_REQUIRED`. Before minting a new attribute type, read the field list
off `metaobjectDefinitions` or an existing entry of that type; harvesting
TaxonomyValue GIDs from existing store entries is often faster than querying the
global Taxonomy API.

## Adjacent surfaces — don't conflate

Four other "product attribute" surfaces look like this job but have different
fixes. Knowing which surface a request actually targets saves a wrong rollout.

- **Google Merchant Center feed attributes** (`age_group` / `gender` / `color`
  showing "Needs attention"). The Google & YouTube channel reads its own
  **`mm-google-shopping`** namespace (free-text `single_line_text_field`), NOT
  the `shopify.*` taxonomy metafields this skill sets. That's a plain
  `metafieldsSet` / Matrixify job, not a taxonomy-metaobject job. Setting the
  category metafield will *not* clear a Merchant Center warning by itself.
- **GSC "Merchant listings" report.** Reads the theme's schema.org Product
  JSON-LD. Metafields of any namespace don't fix it — it's a theme edit. See the
  sibling `shopify-json-ld`.
- **Search & Discovery filters.** Category (taxonomy) metafields ARE the right
  substrate here. S&D value-grouping only works on a standard product attribute
  (taxonomy metafield) or a product option — not on `custom.*` metafields. This
  is frequently the *business reason* to do a taxonomy rollout at all: the
  merchant wants filterable facets and their `custom.*` fields can't group.
- **Linked product options (swatches).** Connecting a Color *option* to
  `shopify--color-pattern` metaobjects is a separate step via
  `productOptionUpdate`, with its own failure modes:
  `LINKED_OPTION_UPDATE_MISSING_VALUES` (ALL option values must be linkable — one
  unmapped color blocks the whole product) and
  `INVALID_METAFIELD_VALUE_FOR_LINKED_OPTION` (per-product; seen with DRAFT
  status and handle collisions against standard `black-1`-style entries).

## Worked examples

**A tea retailer (single-category, tag-driven).** 717 eligible Tea products →
583 shipped from tags (**1,623 metafields set, 0 errors**), 61 ambiguous and 73
assortments held for human review. Signal priority: product tags were the
highest-confidence classifier (the store tagged by type), title keywords the
error-prone fallback (a "Mango" tea is a flavored *black*, not a fruit infusion).
The ambiguous-handling rule was agreed up front (infusions get a *blank* caffeine
value, not "Regular") rather than guessed mid-run.

**An automotive-lifestyle brand (multi-category, options-driven).** 3,241
products but only 419 active; 370 categorized across ~83 categories. Scoped to
the top 12 categories (285 products) and to attributes derivable from variant
options (Color / Size). Mapped option values to `shopify--color-pattern` /
`shopify--size` metaobjects (Color key is `color-pattern`); minted the missing
XS / 4XL / 5XL / One-size values; **126 `metafieldsSet` writes, 0 errors.**
Everything not encoded in variant options (Target gender, Fabric, Pattern,
vehicle-decor attributes) was deferred to a backlog rather than guessed — the
store's tags were merchandising-only and carried no taxonomy signal.

A third rollout, a classic-car parts store, is the origin of gotcha 10: it minted
47 `shopify--color-pattern` entries (34 hex + 13 image, each needing the
`color_taxonomy_reference` list + `pattern_taxonomy_reference`) and then linked
Color options on 130 products via `productOptionUpdate` — the proof case for the
linked-option failure modes above.
