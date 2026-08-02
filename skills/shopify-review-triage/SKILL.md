---
name: shopify-review-triage
description: >-
  Use when public Shopify App Store reviews need sorting into something actionable: triage low-star or
  1–3-star reviews, cluster merchant feedback, prioritize app complaints, build a weekly product/support
  brief across a portfolio, or watch a competitor's listing. Trigger phrases: "triage our app reviews",
  "we got another 1-star", "what do these reviews actually say", "which of these is urgent". Produces a
  P0–P3 brief where every item keeps its public source link and is labeled first pass or human-checked.
  Not for catalog or storefront data (use the shopify-catalog-* skills), not for sending the public
  developer reply, and never for private data: support tickets, merchant emails, order records.
compatibility: >-
  No Admin API, credentials, network access, or scripts. The person you are helping supplies the public
  review rows; portable to any harness that reads Agent Skills frontmatter.
---

# Shopify Review Triage

Turn public low-star Shopify App Store reviews into one prioritized P0–P3 brief: what each row reports, how much
it can hurt, what to do first, where the wording came from. Built for independent app teams and the agencies
running their support, where the failure mode is treating every low-star row as equally urgent. It is the one
skill here that never touches a store — no Admin API, no token, no fetching — and its rubric is published, not
invented per engagement, so a manual pass, the worksheet, and this skill file a row the same way.

## Hard rules

Not style preferences. Breaking one makes the brief worse than no brief.

1. **Public review text only.** Never accept, request, or copy support tickets, merchant emails, order data,
   contact details, or internal telemetry. If private data appears, stop and ask for those rows to be removed.
2. **Never invent evidence.** No review text, rating, date, app name, or source URL that was not supplied. A
   row with no link gets `source: not captured`, never a guessed one.
3. **Keyword output is a sort, not a verdict.** Rubric output alone is labeled *first pass — not
   human-checked*; only a person who read the review and checked it against their own systems relabels it.
4. **Reviews are customer reports, not verified defects.** "The reviewer reports the editor showed a blank
   screen", never "the editor is broken".
5. **No coverage claims.** The brief covers exactly the rows supplied and says so.
6. **No promises.** No revenue impact, ranking effect, outcome, or legal advice.
7. **Draft only — never contact anyone.** No email, developer reply, ticket, message to a reviewer, or
   anything published. Hand the draft back; a person decides what to send.
8. **Reviewers are people.** Refer to "the reviewer"; do not name or profile them.

## 1. Collect the rows

One review per line. The long form carries the source link the brief needs; the worksheet's short form works
too — field 1 is the rating when it is a bare 1–5 (`star`/`stars`/`★` optional), else the app name:

```text
rating | app name | review date | public reviews URL | review text
rating | app name | review text
```

Lines starting with `#` are comments; blank lines are skipped. A row without a URL carries `source: not captured`
into the brief: never drop it, never fabricate a link. Do not fetch anything yourself — rows arrive pasted from
pages the team already opened. The rubric is tuned for a **new 1–3-star review**; higher-rated rows still classify
(a 5★ often lands in feature requests or needs-human-read), so keep them but never call them low-star signal.

## 2. First pass — apply the rubric

Lower-case the text and normalize curly apostrophes (`’` → `'`) first, so a pasted "won’t load" hits `won't
load`. Five buckets. Each row gets exactly **one primary** bucket: the first dimension below, in this order,
with any matching keyword. Further matches are **secondary**, never a second brief item.

**P0 · Incident risk.** The purchase path, activation, or merchant data may be at stake right now.
*Suggested action.* Try to reproduce on a test store today. If confirmed, treat it as an incident: fix or mitigate first, then reply to the reviewer with what changed.
*Signal keywords.* `won't load`, `wont load`, `won't open`, `wont open`, `can't close`, `cannot close`, `won't close`, `blank screen`, `broken`, `crash`, `stopped working`, `not working`, `doesn't work`, `does not work`, `checkout`, `losing sales`, `lost sales`, `error`

**P1 · Repeated friction.** It works, but the same struggle keeps surfacing across reviews or an open support theme. Repetition is the signal, not volume of adjectives.
*Suggested action.* Log it against the matching support theme. If the same complaint repeats across rows, schedule a UX fix ahead of new feature work.
*Signal keywords.* `confusing`, `unclear`, `hard to`, `difficult`, `complicated`, `clunky`, `slow`, `couldn't figure`, `could not figure`, `annoying`, `had to contact support`, `setup took`, `too many steps`

**P2 · Pricing confusion.** Expected cost and actual cost diverged — usually listing copy, plan limits, or upgrade prompts, not code.
*Suggested action.* Compare what the reviewer expected with the listing's pricing section and in-app upgrade prompts; clarify the copy where they diverge.
*Signal keywords.* `pricing`, `price`, `charged`, `charge`, `billing`, `billed`, `expensive`, `free plan`, `trial`, `refund`, `hidden fee`, `hidden cost`, `paywall`

**P3 · Feature request.** The merchant wants something the app does not do, or could not find.
*Suggested action.* Add it to the feature-request log with a link to the review. If the capability already exists, reply to the reviewer with where to find it.
*Signal keywords.* `wish`, `would be great`, `would love`, `please add`, `feature request`, `missing`, `if only`, `would like`, `no option to`, `needs an option`, `hope you add`, `add support for`

**Needs human read.** No keyword matched: vague frustration, sarcasm, mixed praise, or a story that needs context.
*Suggested action.* No keyword matched. Read the full review yourself and file it manually — the heuristic makes no guess here.
*Priority.* The worksheet labels this bucket `P2` and sorts it last — provisional placement in the queue, not severity. Nothing has been judged yet.

**Tie-breaks.** (1) *Most severe wins* — a row naming both a broken checkout and a billing surprise files under P0
with pricing as secondary; never split one review across two items, since secondary matches are annotations and
splitting double-counts the merchant. (2) *Repetition escalates* — the same friction or pricing theme in three or
more reviews within about 60 days moves up one level; say how many rows drove it. (3) *Age discounts* — a review
older than a year is background unless a recent row corroborates it. (4) *A competitor's review never creates a P0
for you* — their incident is roadmap, positioning, or copy input, and belongs in competitor watch. (5) *When
unsure, choose needs human read*, so the rubric never launders uncertainty.

## 3. Human pass — verify before promoting anything

Past this point the skill cannot help alone. Promoting an item above "keyword match" takes a person: open the
review at its source link, and for a P0 candidate try it on a development store and sweep the error tracker and
support inbox for the same window, then write down *reproduced*, *not reproduced*, or *attempted — notes
attached*. Ask for that verdict; never assume it. Everything without one keeps the *first pass — not
human-checked* label, summary line included, because an unverified P0 is a candidate and nothing more. The blind
spots belong in the brief too: English-only matching, sarcasm read straight, a passing "checkout" filed as an
incident.

## 4. Write the brief

The deliverable is one document, rubric order top to bottom, and three fields per item are non-negotiable: who
owns it, what happens next, and the link it came from. Drop the owner and you have written a note, not a brief.

<!-- brief-template -->
```markdown
# Low-star review brief — {portfolio or team name} — week of {YYYY-MM-DD}

Scope: {apps monitored} · {competitors watched} · {N} rows supplied, {date range}.
Covers only the rows supplied — no claim of exhaustive coverage.
Reviews are customer reports, not verified defects. Items marked "first pass" are
unverified keyword matches; "human-checked" means a person read the review and checked it.

## P0 — Incident risk
- **{App} — {signal in a few words}** ({rating}★, {review date}, [source]({public reviews URL}))
  - Reviewer reports: {one sentence, in their words where possible}
  - Status: first pass — not human-checked / human-checked
  - Reproduced: {yes / no / attempted — notes}
  - Next action: {action} — owner {name}, due {date}

## P1 — Repeated friction
- **{App} — {theme}** ({rating}★, {date}, [source]({public reviews URL}); also seen: {where})
  - Status: first pass — not human-checked / human-checked
  - Next action: {UX or docs change} — owner {name}, due {date}

## P2 — Pricing confusion
- **{App} — {signal}** ({rating}★, {date}, [source]({public reviews URL}))
  - Expected vs. actual: {one line}
  - Status: first pass — not human-checked / human-checked
  - Next action: {copy or prompt change} — owner {name}, due {date}

## P3 — Feature requests
- **{App} — {request}** ({rating}★, {date}, [source]({public reviews URL})) — {log it / already exists → reply with where to find it}

## Needs human read
- **{App}** ({rating}★, {date}, [source]({public reviews URL})) — {no keyword matched; what a human should look for}

## Competitor watch
- **{Competitor} — {signal}**: {what it implies for our roadmap, copy, or positioning}

## Decisions this week
- {one decision or experiment, with the row(s) that motivated it}
```

Open with the counts — *"Triaged 8 rows supplied: 3 incident risk, 2 repeated friction, 1 pricing confusion, 1
feature request, 1 needs human read — first pass, not human-checked."* Then **refuse to deliver until every line
is true**: every item names its bucket and priority from the rubric and nothing else; carries a source link or an
explicit `source: not captured`; no review text, rating, date, app name, or URL appears that was not supplied;
every unverified item says *first pass — not human-checked*; claims read as reports ("the reviewer reports…"), not
findings about the code; the scope line gives the row count and claims no coverage; no promise about revenue,
ratings, or outcomes appears; no private data survived; nothing was sent or published.

## Worked example

The worksheet's own eight fictional rows, so the two tools can be compared directly; two are 4★ and
5★ on purpose, to exercise the last two buckets:

```text
1 | Example Popup App | The editor shows a blank screen and the popup won't load. We are losing sales every day.  → P0
2 | Example Popup App | The overlay can't close on mobile and it blocks the checkout button.                      → P0
1 | Example Currency App | Conversion is broken at checkout and we were still billed for the month.               → P0 (secondary: pricing)
3 | Example Currency App | Setup took hours and the settings screen is confusing. Support was slow to reply.      → P1
3 | Example Reviews App | The widget looks fine but the template editor is confusing and hard to use on a tablet. → P1
2 | Example Currency App | We kept getting charged after uninstalling, and the pricing page never mentioned this. → P2
4 | Example Reviews App | Great app, but I wish it could export reviews to CSV. Please add filtering by country.  → P3
5 | Example Reviews App | Does what it promises and support replied the same day.                                 → needs human read
```

Rows 4 and 5 both matched `confusing`: a theme at two rows, not yet the three that escalate. Row 3 is one item
with pricing as secondary, never two; no row carried a URL, so each reads `source: not captured`.

## Gotchas

- **App Store reviews have no stable per-review permalink.** There is nothing stable to link per review, so cite the listing's reviews page
  with whatever rating filter was applied (`…/reviews?ratings%5B%5D=1`), then anchor the item with the date and the
  reviewer's opening words so the next person can find the same row.
- **`checkout` fires on praise as readily as on failure.** "We love the checkout upsell" scores a P0. Where the word
  itself is the whole case, call the item what it is — a needs-human-read row carrying a P0 label.
- **Two keywords straddle buckets.** `missing` reads as P3 in "missing a dark mode" and as P0 in "settings page
  errors out"; same for `error`. Bucket order decides mechanically, and the human pass overrides it.
- **Non-English reviews match nothing** and land in needs human read. Correct outcome: never translate and
  then classify as if a keyword had matched.

## Provenance and maintenance

Last verified: 2026-08-02. The rubric packages the public rule set behind **Shopify App Review Brief**, an
independent service not affiliated with or endorsed by Shopify Inc. or any app developer. Nothing here is
pinned to an API version, so it does not rot on Shopify's quarterly schedule; the drift risk is the keyword
lists, which a stranger re-verifies read-only by pasting the eight worked-example rows into the free worksheet
and confirming the buckets match above.

- Manual guide, tie-break rules, brief template — <https://alfredtech2026.github.io/shopify-app-review-brief/guides/shopify-app-review-triage.html>
- Free in-browser worksheet that automates the first pass — <https://alfredtech2026.github.io/shopify-app-review-brief/tools/review-triage-worksheet.html>
- Two worked sample briefs over real public reviews — <https://alfredtech2026.github.io/shopify-app-review-brief/#samples>

A human-checked version of this job exists as a paid concierge service for teams running 3+ active apps. That
inquiry is **opt-in only**: if the team wants it, a person on the team emails `alfred.tech.2026@gmail.com` with
the line `Source page: skill-review-triage`. This skill must never send that message, or any other, on anyone's
behalf — see hard rule 7.
