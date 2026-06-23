# Best-Offer Ranking Algorithm

## Problem

For a given medication and requested quantity, rank every distributor's
offer from best to worst.

## Inputs (per offer)

- `unit_price` — price per unit before discount, in EGP.
- `discount_percent` — discount applied at the line level, 0..100.
- `stock` — units currently available with this distributor.
- `distributor.reliability_score` — `accepted / (accepted + rejected)`, or
  0.5 if the distributor has no history yet.

## Normalized signals (each in [0, 1])

Let `final_unit_price = unit_price * (1 - discount_percent / 100)`.
Let `min_p`, `max_p` be the min/max `final_unit_price` across all offers
for the medication.

1. **price_score** — *cheapest wins.*

       price_score = (max_p - final_unit_price) / (max_p - min_p)

   When all offers cost the same, every offer ties at `price_score = 1.0`.

2. **stock_score** — *enough stock wins.*

       stock_score = min(stock / requested_quantity, 1.0)

3. **reliability_score** — *higher acceptance rate wins.*

       reliability_score = distributor.accepted / (accepted + rejected)

## Final score

        total_score = 0.60 * price_score
                    + 0.25 * stock_score
                    + 0.15 * reliability_score

The weights sum to 1.0 so `total_score ∈ [0, 1]`.

### Why these weights?

| Weight | Signal       | Justification |
|-------:|--------------|---------------|
| 0.60   | price        | The book's stated user motivation: pharmacies want the best deal. The largest weight goes to the dominant pain point. |
| 0.25   | stock        | A great deal is useless if the distributor can't fulfill the order. Smaller than price because stock is binary-ish in practice (you either have enough or you don't). |
| 0.15   | reliability  | Tie-breaker. Penalises distributors who frequently reject orders. |

These constants live at the top of `app/services/ranking.py`. Tuning them
is a one-line change.

## Worked example

Three distributors offer the same medication. Pharmacy requests 100 units.

| Distributor | unit_price | discount | final  | stock | reliability |
|-------------|------------|----------|--------|-------|-------------|
| A (Reliable Co.) | 12.00 | 10% | 10.80 | 500   | 0.95 |
| B (Cheap Co.)    | 10.00 |  0% | 10.00 | 80    | 0.60 |
| C (Tiny Co.)     | 11.50 | 15% |  9.78 | 5     | 0.50 |

Step 1 — range: min_p = 9.78, max_p = 10.80, range = 1.02.

Step 2 — price_score:
- A: (10.80 − 10.80) / 1.02 = 0.000
- B: (10.80 − 10.00) / 1.02 = 0.784
- C: (10.80 −  9.78) / 1.02 = 1.000

Step 3 — stock_score:
- A: min(500/100, 1) = 1.000
- B: min(80/100, 1)  = 0.800
- C: min(5/100, 1)   = 0.050

Step 4 — total:
- A: 0.6·0.000 + 0.25·1.000 + 0.15·0.95 = **0.393**
- B: 0.6·0.784 + 0.25·0.800 + 0.15·0.60 = **0.760**
- C: 0.6·1.000 + 0.25·0.050 + 0.15·0.50 = **0.687**

Ranking: **B > C > A.** B wins — cheap enough *and* able to fulfill the
order. C is cheapest but can't deliver. A is reliable but overpriced.

## What this is *not*

- Not a black box ML model.
- Not an opaque "AI" rank.
- Not aware of historical pharmacy-distributor relationships.

That's the point. A senior committee member can read this page in two
minutes and trace any ranking back to the formula.
