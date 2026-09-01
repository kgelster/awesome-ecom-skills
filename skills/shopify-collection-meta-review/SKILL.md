---
name: shopify-collection-meta-review
description: >-
  Use when collection SEO titles and meta descriptions exist but need a
  controlled review queue before publication: "review collection meta in bulk",
  "dedupe collection descriptions", "handoff SEO copy to a merchant",
  "collection metadata QA spreadsheet", or "track draft/ready/published meta".
  This is a read-only export-and-review workflow with no store mutation. Not for
  generating missing metadata in the Admin API; use shopify-seo-metadata.
compatibility: >-
  Requires a CSV export and a spreadsheet application. Optional read-only
  Shopify Admin API access can create the export; no write scope is needed.
---

# Shopify Collection Meta Review

Turn collection metadata into a bounded review queue before anyone publishes a
change. The core principle is **separate draft, QA, approval, and publication**:
a plausible line of generated copy is not a ready-to-publish value.

Use `shopify-seo-metadata` when the job is safe-mode generation and API writes.
Use this skill when copy already exists in an export, a draft column, or both,
and a merchant or agency needs to review dozens of collections consistently.

## Define the unit before counting

One row represents one Shopify collection. Keep the collection handle or Admin
GraphQL ID as the stable key; titles are labels, not identifiers. Do not split a
single collection into separate title and description rows, because that hides
whether the two fields describe the same search intent.

Minimum input columns:

```text
collection_key,current_title,current_description,proposed_title,proposed_description
```

Useful optional columns include `collection_url`, `primary_query`, `owner`,
`notes`, and `source_updated_at`. Never put customer data, Admin URLs with
session tokens, preview passwords, or credentials in the sheet.

## Export without mutation

Prefer a merchant-supplied CSV or a Matrixify backup export. If neither exists,
a read-only Admin GraphQL query can collect handles, titles, descriptions, and
SEO fields. Use only the minimum read scope and save the response outside any
public repository.

Before building the queue:

1. Count source rows and unique collection keys.
2. Stop if keys are blank or duplicated; a review sheet cannot safely drive a
   later update until each row maps to exactly one collection.
3. Preserve the raw export on a separate read-only tab or file.
4. Record export time and store timezone. "Current" means current at that time,
   not current forever.

## Normalize for comparison, not publication

Create helper values for QA without rewriting the proposed copy:

- trim leading and trailing whitespace;
- collapse runs of whitespace for duplicate comparison;
- lowercase only the comparison key;
- preserve punctuation, capitalization, and Unicode in the proposed value;
- treat empty as empty, never as permission to delete a live value.

Exact-duplicate detection should compare normalized proposed descriptions. A
spreadsheet formula can use a count over the normalized helper column:

```text
=IF(E2="","",IF(COUNTIF($H$2:$H$204,H2)>1,"DUPLICATE","UNIQUE"))
```

Adjust the range to the actual data, or use a table reference. `H` is the
normalized helper here; it is not a field to publish.

## Character counts are review signals

Count proposed titles and descriptions with the spreadsheet's character-count
function. Use bands to prioritize review, not to promise search appearance.
Search engines can truncate, rewrite, or choose page content instead.

A practical description queue can label rows below 70 characters as `SHORT`,
70–160 as `REVIEW`, and above 160 as `LONG`. Those boundaries are operating
heuristics, not Google requirements. Preserve the actual count beside the
label so a reviewer can see whether a row misses by one character or ninety.

Never pad a weak description merely to enter a band. Specificity and honest
alignment with the collection matter more than occupying every character.

## Four-state handoff

Use one controlled status column:

| State | Meaning |
|---|---|
| `Draft` | Copy exists but has not passed review. |
| `Ready` | A reviewer checked intent, accuracy, duplication, and limits. |
| `Published` | A separate write process landed and was read back. |
| `Hold` | Blocked by missing facts, ownership, or a deliberate exception. |

Default every imported row to `Draft`. A formula must never set `Ready`; that
is a review decision. `Published` is also not a synonym for "sent to an API."
It requires a post-write readback against the collection's Admin API record.

## Review order

Triage the queue in this order:

1. blank collection key or duplicate key;
2. exact duplicate proposed descriptions;
3. proposal that equals another collection's current description;
4. blank proposal paired with a nonblank current value;
5. `LONG` and `SHORT` rows;
6. mismatch between collection name, primary query, and proposed promise;
7. remaining `Draft` rows.

This ordering catches identity and overwrite risks before editorial polish.

## Review checklist per row

A row can move to `Ready` only when all applicable checks pass:

- the stable key maps to the intended collection;
- proposed title and description describe that collection, not the store at
  large or a neighboring category;
- facts, prices, availability, guarantees, and geographic claims are verified;
- no exact normalized duplicate exists in the reviewed set;
- the text is readable without keyword repetition or unsupported superlatives;
- a blank proposal is intentional and cannot erase a live value by accident;
- the reviewer records any exception in `notes`.

Do not claim that passing this checklist will improve rankings or control the
snippet shown by a search engine.

## Summary without vanity metrics

The summary tab should count work states and risks:

- total unique collections;
- `Draft`, `Ready`, `Published`, and `Hold` rows;
- blank proposals;
- exact duplicate groups and affected rows;
- `SHORT` and `LONG` descriptions;
- rows lacking an owner or review note when one is required.

Do not turn an average character count into a quality score. Do not hide `Hold`
rows from the denominator.

## Publication boundary

This skill stops at a verified review package. If another workflow publishes
`Ready` rows, it must:

1. back up the current values;
2. write only rows explicitly marked `Ready`;
3. refuse blank keys and duplicate keys;
4. log old and new values per collection;
5. read each changed collection back through the Admin API;
6. mark `Published` only after the readback matches.

A storefront page is CDN-cached and is not the immediate source of truth for a
write verification.

## Deliverables

Return the reviewed spreadsheet or CSV plus a short manifest containing source
export time, row count, unique-key count, duplicate-group count, state counts,
known limitations, and the filename/checksum of the raw export. Keep the raw
source separate from the editable review queue.

## Provenance and maintenance

Last verified: 2026-09-01. This workflow was exercised on a synthetic 203-row
collection workbook with separate instructions, QA summary, exact-duplicate
checks, character counts, and controlled states. A public, data-free evaluation
of that workflow is available at
https://github.com/Kndll33/shopify-collection-meta-qa-kit-preview . The linked
commercial workbook is optional; this skill is complete without it.

Canonical platform boundaries: Shopify Admin GraphQL documentation at
https://shopify.dev/docs/api/admin-graphql and Google's snippet guidance at
https://developers.google.com/search/docs/appearance/snippet . Recheck both
before relying on version-specific fields or search-appearance behavior.
