"""Illustrative Rupiah amounts that reconcile.

These numbers exist so line arithmetic is *checkable*, not so it resembles a real tariff. The
one property that matters is internal consistency: a claim total equals the sum of its lines,
and a line total equals quantity times unit price, both within a documented tolerance.

`docs/canonical/04_data_card.md` forbids presenting any of this as real cost, and nothing here
is derived from a published tariff.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from random import Random

ROUNDING_TOLERANCE = Decimal("0.01")
"""Amounts within this are the same amount.

Documented here and asserted in tests rather than buried inside a float comparison, so a
rounding discrepancy is a named tolerance instead of an accident.
"""

RUPIAH = Decimal("1")
"""Rupiah amounts carry no sub-unit; quantising to 1 keeps every total an exact integer."""


def money(value: Decimal | int | float | str) -> Decimal:
    """Coerce to a Rupiah amount, rounding half up.

    Half-up rather than banker's rounding: an amount a reviewer sees on screen should round
    the way they would round it by hand.
    """
    return Decimal(str(value)).quantize(RUPIAH, rounding=ROUND_HALF_UP)


def unit_price(rng: Random, bounds: tuple[int, int]) -> Decimal:
    """A price inside `bounds`, drawn from the seeded stream so runs stay reproducible."""
    low, high = bounds
    # Step of 5,000 keeps the numbers legible on screen and the arithmetic easy to verify.
    step = 5_000
    steps = rng.randint(low // step, high // step)
    return money(steps * step)


def line_total(quantity: Decimal, price: Decimal) -> Decimal:
    return money(quantity * price)


def claim_total(line_amounts: tuple[Decimal, ...]) -> Decimal:
    return money(sum(line_amounts, Decimal("0")))


def reconciles(total: Decimal, line_amounts: tuple[Decimal, ...]) -> bool:
    """Whether a claim total matches its lines within the documented tolerance."""
    return abs(total - claim_total(line_amounts)) <= ROUNDING_TOLERANCE
