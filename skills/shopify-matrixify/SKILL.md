---
name: shopify-matrixify
description: >-
  Use when a store owner is doing bulk data work through the Matrixify (formerly
  Excelify) app: bulk import/export, "migrate my catalog", "bulk update prices",
  "bulk edit metafields", CSV or Excel import, "my import deleted my metafields",
  "my import wiped my tags", MERGE vs REPLACE vs UPDATE, "how do I undo an
  import", building a Matrixify sheet by hand or programmatically, or a data
  migration between stores/platforms. Covers products, variants, metafields,
  collections, redirects, customers, and menus. Not for minting category
  (taxonomy) metafields, which Matrixify cannot do (use shopify-category-taxonomy);
  not for one-off single-record edits via the Admin API (use the relevant
  entity skill).
compatibility: >-
  Requires the Matrixify app installed on the store. Files are CSV
  (comma-delimited, double-quoted, UTF-8) or Excel XLSX (multi-sheet). Format is
  app-versioned; verify columns against matrixify.app docs.
---

# Shopify Matrixify

The bulk-data workhorse of the catalog-cleanup suite. Matrixify moves store data
in and out as spreadsheets, so it is how you touch thousands of records at once
instead of one at a time in the admin. Almost every destructive mistake here
comes from one of two misunderstandings: what a *blank cell* means, and what
*omitting a row* means. Internalize the safety doctrine below before you touch a
production catalog.

Canonical docs: [matrixify.app/documentation](https://matrixify.app/documentation/).
This skill is the operational playbook the docs don't spell out.

## Store access

Matrixify runs inside the store, not through the Admin API. You do the work in
two places:

- **The Matrixify app** (Shopify admin → Apps → Matrixify): run Export to pull a
  sheet, run Import to push one. Every import shows an **Analyze** preview and,
  after it runs, an **Import Results** file.
- **A spreadsheet** you edit locally (Excel or any CSV editor) or generate with
  throwaway code.

No token lives in this skill. To verify a write landed, re-export the affected
records and inspect the cells, or read them back through the Admin API: the
storefront is CDN-cached and lies about freshness.

## Safety doctrine

Read this section twice. Every rule here was learned by someone breaking a live
store.

1. **Back up first: the export IS the backup.** Before any bulk write, run a
   full export of the entity you're about to touch (Products, Collections, etc.)
   and save the file. If the import goes wrong, that export is your restore path.
   There is no "undo import" button.
2. **MERGE is the default and it is safe.** An empty Command cell defaults to
   MERGE (except Orders/Draft Orders, which default to NEW). MERGE updates rows
   that exist, creates rows that don't, and leaves untouched anything you didn't
   put in the file. Stay on MERGE unless you have a specific reason not to.
3. **A blank cell in an import DELETES that value: it does not skip it.** This
   is the single most expensive trap in Matrixify. If your sheet has a
   `Metafield: custom.care [multi_line_text_field]` column and a product's cell
   is empty, the import writes *empty*, wiping the existing metafield. Same for
   any field: blank Body HTML clears the description, blank Vendor errors out.
   **Only include columns you intend to change.** The fix is column *omission*,
   not blank cells. Absent column = untouched; present-but-blank column =
   deleted.
4. **REPLACE is destructive by definition.** REPLACE deletes the existing record
   (or nested set: variants, images, tags) and recreates it from *only* what's
   in the file. Anything not in the file is gone. Reach for REPLACE only when you
   truly want the file to be the complete new truth, and back up first.
5. **Omitting a row does NOT revert a prior import.** Dropping a handle from your
   next file doesn't undo what a previous import did to it. Matrixify only acts
   on rows present in the current file; it has no memory of the last run. To
   reverse a change you must import a new file that explicitly sets the old
   values back.
6. **Sub-command MERGE ≠ entity MERGE.** Setting the entity `Command` to MERGE
   does not by itself govern tags, images, or variants. Those have their own
   command columns (`Tags Command`, `Image Command`, `Variant Command`), each of
   which defaults to MERGE when absent (per the
   [matrixify.app docs](https://matrixify.app/documentation/list-of-commands-across-matrixify-sheets/)).
   MERGE is the safe default, but state it anyway: always pair a `Tags` column
   with an explicit `Tags Command` so the intent (add vs. REPLACE the exact list
   vs. DELETE listed) is unambiguous on the sheet rather than relying on the
   default.

## Row identification and adjacency

Matrixify decides which rows belong to the same record by matching, in priority
order: **ID** (Shopify numeric), then **Handle** if ID is blank, then **Title**
if both are blank. Prefer ID or Handle; Title matching is fragile.

**Rows for one record must be adjacent.** When the ID/Handle/Title in a row
differs from the row above, Matrixify treats it as a new record. A multi-variant
product with its variant rows scattered across the file gets split into broken
fragments. Always sort the file by Handle (or ID) so every record's rows sit
together. A row is treated as a variant row when any `Variant …` or `Option …`
column is filled; a row is treated as an image row when `Image Src` is filled.

## Commands

Set per row in the `Command` column.

| Command | Behavior |
|---------|----------|
| (empty) | MERGE (except Orders/Draft Orders → NEW) |
| NEW | Create; fails if the ID/Handle already exists |
| MERGE | Update if present, create if not. Safe default. |
| UPDATE | Update existing only; fails if not found |
| REPLACE | Delete and recreate from file data only. Destructive. |
| DELETE | Delete the record; fails if not found |
| IGNORE | Skip the row entirely (keep context rows in your sheet) |

Nested data has its own command columns, same verbs, scoped to the nested set:

- **Tags Command** (products, customers, orders, blog posts): MERGE adds, DELETE
  removes listed, REPLACE sets the exact list.
- **Image Command** (products): MERGE adds, DELETE removes listed, REPLACE keeps
  only the file's images.
- **Variant Command** (products): MERGE / UPDATE / DELETE / REPLACE across the
  variant set. When updating existing variants, include **Variant ID** or
  Matrixify may create duplicates instead of updating.
- **Product: Command** (custom collections): MERGE adds products to the
  collection, DELETE removes them, REPLACE sets the exact membership.

## Generating sheets programmatically

When you write a CSV in code instead of editing Excel by hand:

1. Double-quote every value; comma delimiter; UTF-8.
2. First row is the header with **exact** Matrixify column names (case-
   insensitive, order-independent, unknown columns silently ignored).
3. Include **only the columns the operation touches**: this is your primary
   guard against the blank-cell-deletes trap.
4. Sort rows by Handle/ID so multi-row records are adjacent; repeat the Handle on
   each variant/image row of the same product.
5. Default `Command` to MERGE; pair any `Tags` column with an explicit
   `Tags Command`.
6. Name the file so it contains the entity: `products-update.csv`,
   `redirects.csv`. A file named `data.csv` may not be recognized as Products.
7. Metafield headers use the full form `Metafield: namespace.key [type]`; set the
   metafield **definition** in Settings → Custom Data *before* importing, or the
   values land "without definition."

### Worked examples

Add a tag to products without wiping existing tags (note: no other product
columns, so nothing else is touched):

```csv
"Handle","Tags","Tags Command"
"summer-hat","clearance","MERGE"
"winter-hat","clearance","MERGE"
```

Set one product metafield across many rows (definition must already exist):

```csv
"Handle","Metafield: custom.care_instructions [multi_line_text_field]"
"linen-shirt","Machine wash cold. Line dry."
"wool-scarf","Hand wash only. Lay flat to dry."
```

Bulk 301 redirects after a URL restructure (one entity, two columns):

```csv
"Path","Target"
"/collections/old-name","/collections/new-name"
"/products/discontinued-item","/collections/replacements"
```

## Sibling skills

- **shopify-category-taxonomy**: Matrixify *cannot* mint category (taxonomy /
  "Category metafields") values; those are reserved metaobjects set via the
  Admin API. Route any taxonomy-attribute rollout there.
- Single-record edits (one product, one redirect) don't need a sheet: use the
  admin UI or the relevant entity skill's Admin API recipe.

## References

- [references/column-reference.md](references/column-reference.md): full column
  schemas per entity: products, variants, metafields, collections, redirects,
  customers, menus.

## Provenance and maintenance

Last verified: 2026-07-05. The Matrixify sheet format is **app-versioned**: the
vendor adds columns and adjusts behavior across releases, so treat any specific
column name or default here as needing confirmation against the current
[matrixify.app documentation](https://matrixify.app/documentation/) before you
rely on it. Read-only re-verification a stranger can run:

- Open [matrixify.app/documentation/products](https://matrixify.app/documentation/products/)
  and [matrixify.app/documentation/list-of-commands-across-matrixify-sheets](https://matrixify.app/documentation/list-of-commands-across-matrixify-sheets/)
  and confirm the command verbs and column names still match this skill.
- In any store with Matrixify installed, run **Export** for a single small
  entity (a handful of products), open the resulting sheet, and inspect the
  actual column headers and command columns: the export is always authoritative
  for that store's current format.

This skill captures operational lessons the vendor docs don't stress; it is not a
replacement for them.
