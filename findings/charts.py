"""Every chart in the project, drawn with bezel-charts (https://pypi.org/project/bezel-charts/).

Each function returns a chart, which shows up in a notebook and saves as an SVG.
"""

from __future__ import annotations

import pandas as pd

import bezel_charts as bc

try:
    from . import analysis as an
except ImportError:
    import analysis as an

WIDE = {"theme": "light", "width": 760}
TILE = {"theme": "light", "width": 270}

# The library's default order puts pink next to green, which look alike with red-green colour blindness.
PAIR = ["#6E70F0", "#D99A0E"]


def years(series: pd.Series) -> pd.Series:
    series = series.copy()
    series.index = series.index.astype(str)
    return series


def visits():
    rates = an.long_run()[["visits", "loans"]].rename(columns={"visits": "Visits", "loans": "Loans"})
    rates.index = rates.index.astype(str)
    return bc.line(
        rates.round(2), heading="Library visits and loans per Connecticut resident, each year", stat="none", zero=True,
        height=250, straight=True, decimals=1, color=PAIR, notes={"2010": "Peak", "2021": "Covid"}, **WIDE,
    )


def events():
    rates = years(an.long_run()["attendance"]).round(2)
    return bc.line(
        rates, heading="Event attendance per resident, each year. The one activity that grew", stat="none", zero=True,
        height=210, straight=True, decimals=2, notes={"2024": "Record"}, **WIDE,
    )


def what_came_back():
    return bc.bars(
        (an.recovery() * 100).round(0), heading="Each activity per resident in 2024, as a share of 2019", horizontal=True,
        stat="none", show_values=True, suffix="%", decimals=0, goal=100, goal_label="2019", **WIDE,
    )


def wealth_gap():
    table = an.by_wealth()[[an.BEFORE, an.LATEST]].round(1)
    table.columns = [str(c) for c in table.columns]
    table.index = [str(i) for i in table.index]
    return bc.bars(
        table, heading="Visits per resident, towns grouped by wealth. Same 160 towns both years", stat="none",
        show_values=True, decimals=1, height=240, color=PAIR, **WIDE,
    )


def spending_and_visits():
    rows = an.spending_and_visits().rename(
        columns={"real_spending_pr": "Spending per resident ($)", "visits_pr": "Visits per resident"}
    )
    return bc.scatter(
        rows.reset_index(), x="Spending per resident ($)", y="Visits per resident", trend=True,
        heading=f"Each town's library spending and visits, {an.LATEST}", height=300, **WIDE,
    )


def cost():
    spend = years(an.cost()["per_resident"]).round(0)
    return bc.line(
        spend, heading="Library spending per resident each year, in 2024 dollars", stat="none", zero=True, prefix="$",
        height=230, straight=True, decimals=0, notes={"2000": "Counted differently", "2009": "Peak"}, **WIDE,
    )


def model_scores():
    return bc.bars(
        (an.models()["explained"].clip(lower=0) * 100).round(0),
        heading="How much of the difference between towns each method explains, 2019", horizontal=True, stat="none",
        show_values=True, suffix="%", decimals=0, **WIDE,
    )


# Headline tiles ------------------------------------------------------------------------------------

def tile_visits():
    return bc.spark(
        years(an.long_run()["visits"]).round(2), heading="Visits per resident, 2024", delta="none", straight=True,
        height=86, decimals=1, **TILE,
    )


def tile_recovery():
    return bc.gauge(
        round(an.recovery()["Visits"] * 100), label="of 2019's visits", heading="Back since Covid", suffix="%", **TILE
    )


def tile_gap():
    table = an.by_wealth()[an.LATEST].iloc[[0, -1]].round(1)
    table.index = ["Richest", "Poorest"]
    return bc.bars(table, heading="Visits per resident, 2024", stat="none", show_values=True, decimals=1, height=150,
                   color=PAIR, **TILE)


ALL = {
    "visits": visits,
    "events": events,
    "what-came-back": what_came_back,
    "wealth-gap": wealth_gap,
    "spending-and-visits": spending_and_visits,
    "cost": cost,
    "model-scores": model_scores,
    "tile-visits": tile_visits,
    "tile-recovery": tile_recovery,
    "tile-gap": tile_gap,
}
