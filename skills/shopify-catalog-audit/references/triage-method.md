# Hypothesis-driven triage for catalog work

The method behind the audit loop, generalized for Shopify catalog work. Read
this before any audit-shaped task over a catalog too large to read whole.

The core move: **do not feed the whole catalog to the model.** Build a cheap
deterministic index over all of it, let the model hypothesize and justify where
the problems are, deep-read only the targeted slice, then verify findings against
the live Admin API. Cheap reasoning on a cheap abstraction aims expensive
analysis.

## When to use it

- The task is audit-shaped: "find what's wrong across this catalog", "where are
  the gaps / anomalies / debris".
- The catalog is larger than fits comfortably in context, or large enough that
  reading every PDP is slow and expensive.
- The problem class is enumerable up front — you can describe what a "defect"
  looks like well enough to index for it (missing photos, thin descriptions,
  pricing anomalies, taxonomy gaps).

## When NOT to use it

- The catalog is small enough to read whole cheaply. Just read it.
- Code alone produces the answer (a count of $0 variants, a diff of two exports).
  Skip the model; deterministic transforms are code's job.
- The question is open-ended discovery where you can't yet describe the defect
  you're hunting. Triage finds what the index was built to surface; it is blind
  to problem classes you didn't index for. Explore a sample of PDPs by hand
  first, then triage once the defect shape is known.

## The loop

**1. Build the cheap index.**
Deterministic code paginates the catalog and computes per-product flags — the
structural facts that reveal where problems live without reading every PDP.
Missing/low image count, empty/thin description, $0 or inverted pricing, empty
type/vendor, plus status context. Code answers what code can. The output is a
compact flag table, one row per product — not the raw catalog.

**2. Hypothesize on the index.**
The model reasons over the flag table (not the raw PDPs) to rank where problems
cluster. **Every hypothesis must carry a stated reason. No reason, drop it.**
Unjustified flags are noise that cost expensive deep-reads downstream. Aim for
patterns over rows: "all products from one vendor imported the same week have
zero images — broken feed" is worth more than a flat list of imageless products.

**3. Deep-read only the targeted slice.**
Feed the model full detail for only the products the justified hypotheses pointed
at. This is where the frontier model and the real tokens go. **Never widen back
out to the whole catalog "just to be safe"** — that defeats the method and the
budget.

**4. Verify against ground truth.**
Confirm each surviving finding by re-querying the live Shopify Admin API. Not
against the model's own assertion, not against the index, and **not against the
sitemap** — the sitemap is published-only and misses the drafts and archived
products where debris hides. The passing Admin-API read is the evidence.

## Discipline rails

- **Justify-or-drop.** A hypothesis without a reason does not get deep-read.
- **Triage is not assurance.** It finds what the index was built to surface,
  never what it wasn't. Always log coverage: which flags you indexed and which
  defect classes you did **not** check. "Found N problem products" must never be
  allowed to read as "the catalog is clean." You can't measure the false
  negatives, so name the blind spot explicitly.
- **Route the model.** Code and cheap reasoning do the index and the volume; the
  frontier model is spent only on the targeted deep-read in step 3.
- **Ground truth over self-grading.** Verify against the external system (the
  Admin API). If the model both writes the indexing code and grades its own
  output, the green check is circular and proves nothing.
- **Re-aim, don't widen.** When triage comes up thin, the fix is a better index
  (flag a different signal), not feeding more raw catalog to the model.

## Worked example: PDP quality sweep

**Index.** Paginate `products`, pull `mediaCount`, `descriptionHtml`, variant
`price`/`compareAtPrice`, `productType`, `vendor`, `status`, `publishedAt` (see
[queries.md](queries.md)). In code, emit per product: `images_missing`,
`images_thin`, `desc_thin`, `price_zero`, `price_inverted`, `no_type`,
`no_vendor`, plus `status`. One row each. For a 6,000-product catalog that's a
6,000-row boolean table the model can reason over in one pass.

**Hypothesize.** Model reads the table and ranks: the 40 active-published
products with `price_zero` are the top defect (live revenue leak, justified by
status); the 300 `images_missing` rows correlate with one vendor and one import
date (justified: broken feed, one root cause not 300); the 900 `desc_thin` rows
on archived products are noise (justified: not shopper-facing, deprioritize).

**Deep-read.** Pull the full PDPs for only the 40 $0 products and a sample of the
imageless-vendor products to confirm the pattern. Skip the 900 archived rows.

**Verify.** Re-query those 40 products through the Admin API and confirm each
still has a $0 variant on the live object. Report the confirmed count.

**Coverage statement.** "Indexed for images, description length, pricing
anomalies, and type/vendor across all 6,000 products. Did NOT check: variant
option consistency, metafield completeness, broken image URLs, SEO metadata.
Findings below cover the indexed classes only."

## Anti-patterns

- Pasting the whole catalog into the model "to be thorough." The cost trap this
  method exists to avoid.
- Acting on a flag the model couldn't justify.
- Reporting findings with no coverage statement, so triage output masquerades as
  a clean bill of health.
- Grading the model's index with the model's own summary instead of the live
  Admin API.
- Treating a thin triage result as proof the catalog is healthy. It's proof only
  that the indexed defect class is mostly absent.

---

*Generalized from a large-surface triage method: build a cheap deterministic
abstraction, have the model hypothesize and justify, feed only targeted segments
to expensive analysis, verify against ground truth.*
