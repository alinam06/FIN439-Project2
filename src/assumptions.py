"""Fixed Version 1 classroom inputs, in annual decimal units."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    name: str
    gross_return: float
    volatility: float
    investment_grade: bool = False
    reserve_eligible: bool = False
    company: str | None = None


DATASET = "Lab 14 course assumptions plus Version 1 fictional company and fee"
ASSETS = (
    Asset("U.S. Treasury bills", .035, .005, reserve_eligible=True),
    Asset("U.S. Treasury 10-year note", .043, .07, True, True),
    Asset("U.S. investment-grade bond fund", .05, .06, True),
    Asset("Global equity index fund", .08, .16),
    Asset("Fictional company stock", .09, .28, company="Fictional company"),
)
CORRELATIONS = (
    (1, .10, .05, 0, 0),
    (.10, 1, .80, -.10, -.07),
    (.05, .80, 1, .25, .175),
    (0, -.10, .25, 1, .70),
    (0, -.07, .175, .70, 1),
)
ANNUAL_COST = .0015
