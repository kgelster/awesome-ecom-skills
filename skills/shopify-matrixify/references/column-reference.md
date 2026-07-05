# Matrixify Column Reference

Full column schemas per entity, loaded on demand. Headers are case-insensitive
and order-independent; unknown columns are silently ignored, so a sheet only
needs the columns whose values you want to write. Columns marked **Export Only**
cannot be set on import (Matrixify populates them on export and ignores them on
import).

Verify any specific header against the current
[matrixify.app documentation](https://matrixify.app/documentation/): the format
is app-versioned. The single fastest ground-truth check is to run an Export of a
few records and read the header row.

## Products

### Core product fields

- **ID**: Shopify numeric ID (highest-priority row match).
- **Handle**: URL slug; auto-generated from Title if blank on create.
- **Command**: NEW / MERGE / UPDATE / REPLACE / DELETE / IGNORE.
- **Title**: the only mandatory field for a new product.
- **Body HTML**: description (plain text or HTML). Blank cell clears it.
- **Vendor**: brand; Shopify requires it non-empty.
- **Type**: product type / classification.
- **Tags**: comma-separated. Always pair with **Tags Command**.
- **Tags Command**: MERGE (add) / DELETE (remove listed) / REPLACE (exact list).
- **Status**: active / archived / draft.
- **Published**: TRUE/FALSE (Online Store visibility).
- **Published At**: date/time; supports future scheduling (`YYYY-MM-DD HH:MM:SS`).
- **Published Scope**: global (Online Store + POS) or web (Online Store only).
- **Template Suffix**: custom theme template.
- **Gift Card**: TRUE/FALSE; settable only at creation, immutable after.
- **Custom Collections**: comma-separated collection names to add the product to.

### Variant fields (prefix `Variant`)

- **Variant ID**: include when updating existing variants or you risk duplicates.
- **Variant SKU**, **Variant Barcode** (UPC).
- **Variant Price**, **Variant Compare At Price** (strikethrough).
- **Variant Inventory Qty**: absolute quantity (single-location).
- **Variant Inventory Adjust**: relative (+5 / -3).
- **Variant Inventory Policy**: deny / continue (overselling).
- **Variant Weight**, **Variant Weight Unit** (g / kg / lb / oz).
- **Variant Taxable** (TRUE/FALSE), **Variant Tax Code** (Shopify Plus only).
- **Variant Requires Shipping** (TRUE/FALSE).
- **Variant Fulfillment Service**: manual or a service name.
- **Variant Position**: display order.
- **Variant Command**: MERGE / UPDATE / DELETE / REPLACE.

### Option fields

- **Option1 Name** / **Option1 Value**: e.g. Size / Large.
- **Option2 Name** / **Option2 Value**: e.g. Color / Red.
- **Option3 Name** / **Option3 Value**: max three options per product.

Each variant needs a unique Option1/Option2/Option3 combination within the
product. Max 100 variants per product.

### Image fields

- **Image Src**: direct, publicly reachable URL (not auth-gated, not a Drive
  share link, no redirects).
- **Image Position**: 1-based display order.
- **Image Alt Text**: alt text for SEO/accessibility.
- **Image Command**: MERGE (add) / DELETE (remove listed) / REPLACE (keep only
  file's images).

Multiple images: one per row, or semicolon-separated URLs in one cell.

### Export-only product fields

- **Created At**, **Updated At**, **URL** (live page), **Total Inventory Qty**,
  **Row #**, **Top Row** (TRUE on a product's first row).

## Metafields

### Header format

```
Metafield: namespace.key [type]
Variant Metafield: namespace.key [type]
```

Examples:
- `Metafield: custom.care_instructions [multi_line_text_field]`
- `Metafield: my_fields.finished_size [dimension]`
- `Variant Metafield: custom.color_code [single_line_text_field]`

### Rules

- Product metafields only need a value in the product's top row.
- Variant metafields can differ per variant row; a filled Variant Metafield
  column marks the row as a variant row.
- Omitted namespace defaults to `global`.
- Escape literal dots in a namespace/key with a backslash: `\.`.
- Define the metafield in Settings → Custom Data **before** importing, or values
  import "without definition."
- A blank metafield cell in an import **deletes** the metafield. Omit the column
  to leave it untouched.
- Matrixify **cannot** write category (taxonomy) metafields: those are reserved
  metaobjects. Use the category-taxonomy skill.

### Supported types

- Text: `single_line_text_field`, `multi_line_text_field`, `rich_text_field`
  (accepts Shopify JSON / HTML / plain / Markdown), plus `list.single_line_text_field`.
- Numbers: `number_integer`, `number_decimal` (+ `list.*`).
- Date/time: `date` (ISO `2021-10-25`), `date_time` (`2021-10-25T14:30:00`) (+ `list.*`).
- Measurement: `weight` (kg/g/lb/oz), `volume` (ml/l/us_gal…), `dimension`
  (mm/cm/m/in/ft/yd) (+ `list.*`). Value as `{"unit":"kg","value":2.5}` or plain.
- Boolean: `boolean`.
- References: `product_reference`, `collection_reference`, `variant_reference`
  (`product_handle.variant_title`), `file_reference`, `page_reference`,
  `metaobject_reference` (all with `list.*` forms).
- Other: `color`, `url`, `json`, `money`, `rating`.

List values separate with commas, semicolons, in-cell line breaks, or a JSON array.

## Custom Collections (manual)

- **ID**, **Handle**, **Title**, **Body HTML**, **Command**.
- **Sort Order**: alpha-asc / alpha-desc / best-selling / created / created-desc
  / manual / price-asc / price-desc.
- **Template Suffix**, **Published** (TRUE/FALSE).
- **Image Src**, **Image Alt Text**.
- Membership: **Product: ID**, **Product: Handle**, **Product: Position**,
  **Product: Command** (MERGE add / DELETE remove / REPLACE exact set).
- Metafields (including SEO Title / SEO Description via the metafield header form).

## Smart Collections (automated)

Same base fields as Custom Collections, plus rule columns:

- **Rule: Column**: title / type / vendor / tag / variant_price / etc.
- **Rule: Relation**: equals / not_equals / starts_with / ends_with / contains /
  greater_than / less_than.
- **Rule: Condition**: the value to match.
- **Disjunctive**: TRUE (match any rule) / FALSE (match all rules).

## Redirects (301)

Two columns, one of the simplest and safest imports:

- **Path**: source path (e.g. `/old-page`).
- **Target**: destination path or full URL (e.g. `/new-page` or
  `https://example.com/new-page`).

## Customers

### Core

- **ID**, **Email** (unique), **Phone** (with country code).
- **First Name**, **Last Name**, **Command**.
- **State**: disabled / invited / enabled / declined.
- **Tax Exempt** (TRUE/FALSE), **Note**, **Language** (2-char ISO).
- **Tags** / **Tags Command**.

### Marketing consent

- **Email Marketing Status**: subscribed / unsubscribed / pending / invalid /
  not_subscribed. **Email Marketing Level**: confirmed_opt_in / single_opt_in.
- **SMS Marketing Status** / **SMS Marketing Level**: same option sets.

### Addresses (multi-row)

One address per row: **Address First Name**, **Address Last Name**,
**Address Phone**, **Address Company**, **Address1**, **Address2**,
**Address City**, **Address Province** / **Address Province Code**,
**Address Country** / **Address Country Code**, **Address Zip**,
**Address Default** (TRUE), **Address Command** (MERGE / DELETE / REPLACE).

Export-only: **Total Spent**, **Total Orders**, **Created At**, **Updated At**.

## Menus (navigation)

Menus import is stricter than most entities. The common traps:

- Every row of one menu import needs a **uniform Command**; mixing commands
  within a menu import is unreliable. Practically, use **MERGE** or **DELETE**
  only.
- Menu links reference their target; when a link points at a **collection**, the
  target is resolved by collection **handle**, so a handle mismatch silently
  produces a dead link. Verify collection handles before importing a menu that
  links to them.
- Because a menu is a tree, keep parent/child rows adjacent and ordered the way
  Matrixify's export lays them out: export the existing menu first and edit that
  structure rather than authoring the hierarchy from scratch.

## Resources

- Documentation hub: <https://matrixify.app/documentation/>
- Products: <https://matrixify.app/documentation/products/>
- Metafields: <https://matrixify.app/documentation/metafields/>
- Commands: <https://matrixify.app/documentation/list-of-commands-across-matrixify-sheets/>
- Template format: <https://matrixify.app/documentation/matrixify-format-template/>
