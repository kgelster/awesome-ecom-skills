# Mill.com Teardown

Mill.com is a DTC food-recycler brand that runs a mature landing-page system:
roughly 40 production `/lp/` pages built off a single hardware product. It's a
public, browsable example of the whole method — one product, dozens of pages,
each keyed to a different traffic source and mindset. This file maps its pages
to the archetypes and tears down two of them section by section, so the
abstractions in the SKILL and build-blueprint have concrete ground truth.

Everything here is observable at [mill.com](https://mill.com) by browsing the
`/lp/` paths. Page counts and exact headlines can change when a brand
restructures its funnel; re-confirm any specific claim against the live site
before quoting it.

---

## Archetype → representative URL map

| Archetype | Representative Mill pages |
|-----------|---------------------------|
| Audience / persona | `/lp/chickens`, `/lp/offices`, `/lp/commercial` |
| Use-case | `/lp/food-grounds`, `/lp/gardens-archive` |
| Pain / emotional | `/lp/busy-schedule`, `/lp/one-easy-thing` |
| Location / geo | `/lp/nyc`, `/lp/la`, `/lp/avondale`, `/lp/nyc-curbside-compost` |
| Event / seasonal / promo | `/lp/memorial-day-sale`, `/lp/event-tabling`, `/lp/big-night`, `/lp/mill-pickups-bfcm` |
| Offer / trial / guarantee | `/lp/free-trial`, `/lp/90-day-mbg`, `/lp/event-two-month-trial` |
| Occasion / gift | `/lp/gifting` |
| Segment / B2B + partner | `/lp/municipalities`, affiliate/trade program, LEED/TRUE certification ebook, `/lp/lca` |

The lesson lives in the spread: a food-recycler turned "food waste" into
chickens, gardens, gifting, municipalities, seasonal sales, and an affiliate
program. Same device, many first sentences.

---

## Teardown A — `/lp/busy-schedule` (pain/emotional, cold paid social)

- **Hero:** "Save time — and the planet." / "Mill makes recycling your food
  scraps effortless and odorless." / CTA "Buy Mill."
- **Angle:** pain/emotional reframe for cold traffic. The viewer wasn't
  searching for a food recycler; the felt benefit (save time) earns the click.
- **Body order:** Runs automatically while you sleep → Completely odorless →
  Keep filling it for weeks → How it works (3 steps) → Ways to use your grounds
  → Risk-free trial → Customer stories → Featured in (press) → audience
  expansion (chickens, gardeners).
- **Why it works:** leads with a felt benefit for cold traffic, pre-handles the
  two killer objections (time and smell) before they surface, then proves with
  press and testimonials before the ask. The audience-expansion block at the
  bottom captures visitors who don't convert on the pain angle but recognize a
  different use-case.

Mapped to the 10-section skeleton: hero → (pillars: automatic / odorless /
weeks-long capacity) → how it works → use-cases → tiered proof (testimonials +
press) → risk reversal → cross-sell → implied final CTA.

---

## Teardown B — `/lp/municipalities` (B2B/segment, long cycle)

- **Hero:** "Mill for Municipalities" / "building a new system for food… scales
  to communities" / CTA "Stay in the loop" (email capture, not a cart).
- **Angle:** B2B segment. The buyer is a decision-maker on a long procurement
  cycle, so the page sells a system and a pipeline entry, not an impulse purchase.
- **Body order:** Increase Diversion → Goodbye Contamination → Improve
  Efficiency (with an "80% reduction" figure and cost stats) → Case studies
  (named cities) → "Get in touch."
- **Why it differs from the consumer pages:** quantified metrics and case
  studies replace lifestyle copy; the CTA feeds a sales pipeline rather than a
  checkout. Same product, an entirely different page, because the buyer and the
  cycle differ.

This is the archetype delta from build-blueprint in production: swap lifestyle
for metrics, testimonials for case studies, and a cart CTA for a soft lead-gen
CTA.

---

## How to use these teardowns

When building a chosen concept, find the archetype's representative Mill page,
open it, and note the section order and where proof sits relative to the ask.
Don't copy the copy — copy the structure and the objection-handling discipline.
The two teardowns above bracket the range: a cold-traffic consumer page that
leads with a felt benefit and a warm-cycle B2B page that leads with metrics.
Most concepts land somewhere between them.
