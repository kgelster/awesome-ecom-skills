---
name: ecom-landing-pages
description: >-
  Use when someone wants landing page ideas, concepts, or angles for a store:
  "give me landing page concepts", "LP ideas", "landing page angles", a
  campaign or ad landing page, pages for a new audience/segment, a
  seasonal/event/promo page, or a geo/local page. Also use when a chosen concept
  gets picked and needs building out into an actual page (section-by-section
  blueprint), or when auditing an existing landing page against best practice.
  The core insight: one product becomes dozens of pages by varying the ANGLE,
  not the product. Not for full-site information architecture, product detail
  pages, collection pages, or blog/SEO content (a landing page has ONE goal, no
  site chrome) — use an SEO/content skill. Not for the ad or email creative
  itself, though message match with the page matters.
compatibility: >-
  Platform-neutral. No Admin API or credentials required. Ideation runs
  from the public storefront; the build blueprint is theme-agnostic.
---

# Ecom Landing Pages

Turn a store brief into two deliverables: a ranked list of landing-page
concepts, and a build blueprint for the ones worth shipping. The method was
reverse-engineered from Mill.com, a DTC brand running ~40 production `/lp/`
pages off a single product. That spread is the whole idea in one sentence:
**one product becomes many landing pages by varying the angle, not the
product.** A person who clicks a "feed your chickens" ad and a person searching
"nyc curbside compost" want the same device but need different first sentences.

This is the one platform-neutral skill in the collection: landing-page thinking
is the same on any CMS, so the `ecom-` prefix, not `shopify-`. Execution notes
that differ by platform are called out where they matter.

## When this fires

- A store needs landing-page concepts for paid traffic, a campaign, a new
  segment, a season, or an event.
- A concept got chosen and needs building into a real page.
- An existing landing page needs an audit against best practice.

Not for full-site IA, PDPs, collection pages, or blog/SEO articles: those live
inside the browse flow and compete for attention. A landing page has one goal
and strips the chrome. Different rules.

## The loop

### 1. Intake from the live storefront

Read the store's real site: homepage, key product pages, collections, the
sitemap if it helps. Never invent products, audiences, or offers — an empty
intake field is a signal, not a license to make something up. Pull:

- **Product / offer:** what sells, price, the single most important thing it does.
- **Core value prop:** the one-sentence promise.
- **Distinct audiences:** buyers segmented by identity, not demographics.
- **Top pains:** the problems that drive purchase, in the customer's own words.
- **Use-cases:** the different jobs the product does.
- **Geos / markets:** cities or regions with concentrated demand or local programs.
- **Seasonal / event calendar:** sale moments, in-person events, launches.
- **Offers:** trials, guarantees, discounts, bundles, financing.
- **Gift / occasion fit:** is it giftable? which occasions?
- **B2B / segments:** institutional buyers with a longer cycle and different criteria.
- **Partner / affiliate channels:** creators, trade partners, referrers.

### 2. Generate against the 8 archetypes

Every landing page is one of these angles. Walk each one against the intake and
ask "is there a page here?" A page can stack archetypes; lead with the dominant
one, because the headline only gets to make one promise.

| # | Archetype | When to reach for it |
|---|-----------|----------------------|
| 1 | Audience / persona | A distinct buyer identity with its own motivation; the headline names them |
| 2 | Use-case | The product does several jobs and a segment cares about exactly one |
| 3 | Pain / emotional reframe | Cold top-of-funnel traffic that doesn't know the category yet |
| 4 | Location / geo | Geo-targeted ads, local programs, regional logistics or PR |
| 5 | Event / seasonal / promo | A campaign window, a sale, or an in-person moment; urgency-driven |
| 6 | Offer / trial / guarantee | Conversion-stage traffic that needs a nudge or risk reversal |
| 7 | Occasion / gift | Holiday and gifting; reframes the reader as the giver |
| 8 | Segment / B2B + partner | Institutional buyer or referral partner; metrics and process, not lifestyle |

Push every archetype at least once before ranking. The failure mode is
generating the same angle ten times. The full taxonomy with Mill examples and
the stacking rules is in [references/build-blueprint.md](references/build-blueprint.md).

### 3. Key each candidate to a traffic source

**Traffic source is the primary angle selector.** It dictates the angle and the
headline's job. Drop any idea that can't name a source — a page with no campaign
behind it is an orphan.

- **Paid social, cold** → pain/emotional or audience. The viewer wasn't looking
  for you; earn the click with a felt problem or an identity hook.
- **Search, intent** → use-case, geo, or offer. Match the query language exactly.
- **Local / geo ads** → location, with local proof and local logistics.
- **Email / retargeting, hot** → offer/guarantee or bundle. They know you; remove friction.
- **Partner / affiliate** → segment/partner, usually a different conversion goal
  (a sign-up, not a purchase).

### 4. Prioritize on 4 axes

Score each candidate 1–5 and rank. Intent match carries the most weight.

- **Intent match:** how precisely the page answers the traffic source's mindset.
- **Demand / traffic availability:** real search volume, an ad audience, or a
  live event to send traffic. No traffic is a no.
- **Business value:** margin, AOV, strategic segment, or lifetime value of who converts.
- **Build cost:** copy + assets + (for B2B) a lead-capture/CRM path. Cheaper wins ship first.

### 5. Output: lead with the ranked table

One row per concept. This table is the deliverable — put it first.

| # | Concept | Archetype | Target | Core promise | Primary CTA | Traffic source |
|---|---------|-----------|--------|--------------|-------------|----------------|
| 1 | "Feed your flock" | Audience/use-case | Backyard chicken owners | Turn scraps into chicken snacks | Shop now | Paid social |
| 2 | "NYC: skip the trash chute" | Geo + pain | NYC apartment dwellers | No more takeout-trash trips | Shop now | Search + geo ads |

Then, below the table:

- **Deliberately deprioritized:** the archetypes or ideas you cut and why (e.g.
  "geo is thin for a national DTC with no local programs"). Never a silent cap.
- **Build first:** the top 2–3 with one line each on why they lead.
- Offer to take one concept through the build blueprint. Stop at the ranked
  list unless asked to build.

## Building a chosen concept

When a concept is picked, build it on the 10-section page skeleton in
[references/build-blueprint.md](references/build-blueprint.md): hero → benefit
pillars → how it works → use-cases → tiered social proof → risk reversal →
comparison → FAQ → cross-sell → final CTA. That reference also carries the copy
patterns, the archetype-specific structural deltas (B2B swaps lifestyle for
metrics; promo moves price up top; partner leads with terms), and the
pre-launch checklist. Worked teardowns of live Mill pages are in
[references/mill-teardown.md](references/mill-teardown.md).

## Red flags: stop and correct

- **Inventing the store's products or audiences** instead of reading the site →
  go read the live storefront and re-ground every concept.
- **A flat list with no archetype spread**, or concepts with no traffic source →
  you skipped steps 2–3. Force every archetype once; every row names a source.
- **A table where everything wins** → you're listing, not prioritizing. Rank
  honestly and state what you cut.
- **Jumping straight to building the page** → the deliverable is the ranked list
  first. Build is a separate step, on request.
- **Same angle repeated** → the whole point is angle variety off one product.
  If three rows are the same archetype with a new noun, collapse them.

## References

- [references/build-blueprint.md](references/build-blueprint.md) — full 8-archetype
  taxonomy, the 10-section page anatomy, copy patterns, archetype deltas, and the
  pre-launch checklist.
- [references/mill-teardown.md](references/mill-teardown.md) — archetype→URL map
  and section-by-section teardowns of live Mill.com landing pages.

## Provenance and maintenance

Last verified: 2026-07-05. The method is reverse-engineered from a public,
observable system, so a stranger can re-verify it read-only: visit
[mill.com](https://mill.com) and browse its `/lp/` landing pages, then map each
live page to one of the 8 archetypes above. If the pages still cluster into
audience, use-case, pain, geo, event, offer, gift, and B2B/partner angles off a
single product, the taxonomy holds. Landing-page best practice drifts slowly;
the archetypes and the section skeleton are durable, but re-confirm any
Mill-specific claim (page counts, exact headlines) against the live site before
quoting it, since a brand can restructure its funnel at any time.
