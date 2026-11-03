"""Draw every chart and write the findings report.

Run from the repository root:

    python findings/build.py

Charts go into charts/ as SVG files. The report is written to findings/README.md, and the key findings in the
main README are rewritten between their marker comments. Every number is worked out from the data. Nothing in
them is typed in by hand.
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "findings"))

import analysis as an  # noqa: E402
import charts  # noqa: E402

CHARTS = ROOT / "charts"
REPORT = ROOT / "findings" / "README.md"
README = ROOT / "README.md"


def facts() -> dict:
    """Every number the writing uses, in one place."""
    rates = an.long_run()
    visits, loans, events, questions, computers = (rates[c] for c in rates.columns)
    back = an.recovery()
    wealth = an.by_wealth()
    spend_by_wealth = an.by_wealth("real_spending")
    link = an.spending_link()
    cost = an.cost()
    first = an.first_version()
    model = an.models()
    notes = an.data_notes()
    cards = an.per_resident("borrowers")
    rich, poor = wealth.index[0], wealth.index[-1]
    peak = int(visits.idxmax())
    spend_peak = int(cost["per_resident"].drop(2000).idxmax())
    return {
        "first_year": int(rates.index.min()), "last_year": an.LATEST, "before": an.BEFORE,
        "towns": notes["towns"], "libraries": notes["libraries"], "names": notes["names"], "rows": f"{notes['rows']:,}",
        "usual": notes["usual"], "missing_2024": notes["missing_2024"], "no_population": notes["no_population"],
        "mat23": notes["materials_2023"], "mat24": notes["materials_2024"],
        "v_first": visits.iloc[0], "v_peak": visits[peak], "peak": peak, "v_before": visits[an.BEFORE],
        "v_fall": 1 - visits[an.BEFORE] / visits[peak], "v_2021": visits[2021], "v_low": 1 - visits[2021] / visits[an.BEFORE],
        "v_last": visits[an.LATEST],
        "l_peak": loans[int(loans.idxmax())], "l_peak_year": int(loans.idxmax()), "l_before": loans[an.BEFORE],
        "l_fall": 1 - loans[an.BEFORE] / loans.max(),
        "e_first": events.iloc[0], "e_before": events[an.BEFORE], "e_last": events[an.LATEST],
        "e_growth": events[an.BEFORE] / events.iloc[0],
        "q_peak": questions.max(), "q_last": questions[an.LATEST],
        "c_peak": computers.max(), "c_peak_year": int(computers.idxmax()), "c_last": computers[an.LATEST],
        "back_events": back["Event attendance"], "back_loans": back["Loans"], "back_visits": back["Visits"],
        "back_questions": back["Questions for staff"], "back_computers": back["Public computer use"],
        "same_towns": len(an.same_towns()),
        "rich_before": wealth.loc[rich, an.BEFORE], "poor_before": wealth.loc[poor, an.BEFORE],
        "rich_last": wealth.loc[rich, an.LATEST], "poor_last": wealth.loc[poor, an.LATEST],
        "gap_before": wealth.loc[rich, an.BEFORE] / wealth.loc[poor, an.BEFORE],
        "gap_last": wealth.loc[rich, an.LATEST] / wealth.loc[poor, an.LATEST],
        "rich_kept": wealth.loc[rich, "kept"], "poor_kept": wealth.loc[poor, "kept"],
        "rich_spend": spend_by_wealth.loc[rich, an.LATEST], "poor_spend": spend_by_wealth.loc[poor, an.LATEST],
        "r": link["r"], "scatter_towns": link["towns"],
        "s_first": cost.loc[cost.index.min(), "per_resident"], "s_peak": cost.loc[spend_peak, "per_resident"],
        "s_peak_year": spend_peak, "s_last": cost.loc[an.LATEST, "per_resident"],
        "s_fall": 1 - cost.loc[an.LATEST, "per_resident"] / cost.loc[spend_peak, "per_resident"],
        "pv_peak": cost.loc[peak, "per_visit"], "pv_before": cost.loc[an.BEFORE, "per_visit"],
        "pv_last": cost.loc[an.LATEST, "per_visit"],
        "old_r2": an.FIRST_VERSION_R2, "copied": first["copied"], "match": first["match"],
        "old_mse": first["printed_rmse"], "old_rmse": first["true_rmse"],
        "kept_rows": f"{first['rows_kept']:,}", "dropped": 1 - first["rows_kept"] / first["rows"], "kept_from": first["first_year"],
        "m_base": model.loc["The state's typical town", "error"], "m_wealth": model.loc["Town wealth", "explained"],
        "m_all": model.loc["Wealth, spending and size", "explained"], "m_all_err": model.loc["Wealth, spending and size", "error"],
        "m_last": model.loc["The town's own figure last year", "explained"],
        "m_last_err": model.loc["The town's own figure last year", "error"],
        "m_avg": model.attrs["average"], "m_train": f"{model.attrs['train_rows']:,}",
        "m_towns": int(model.loc["Town wealth", "towns"]),
        "town_share": an.town_share(), "cards_peak": cards.max() * 100, "cards_peak_year": int(cards.idxmax()),
        "cards_last": cards[an.LATEST] * 100,
    }


def key_findings(f: dict) -> str:
    return f"""### Visits were falling long before Covid

Connecticut residents made {f['v_peak']:.2f} library visits each in {f['peak']}. By {f['before']}, before the pandemic, that was down to
{f['v_before']:.2f}, a fall of {f['v_fall']:.0%}. Borrowing fell even faster.

![Library visits and loans per resident each year](charts/visits.svg)

### Events came back. Computers didn't

Per resident, event attendance in {f['last_year']} was **{f['back_events']:.0%}** of its {f['before']} level, and borrowing {f['back_loans']:.0%}. But visits
were only {f['back_visits']:.0%} and public computer use {f['back_computers']:.0%}.

![Each activity in {f['last_year']} as a share of {f['before']}](charts/what-came-back.svg)

### Richer towns' libraries bounced back. Poorer towns' didn't

In {f['before']}, people in the richest quarter of towns visited their library {f['gap_before']:.1f} times as often as people in the poorest
quarter. By {f['last_year']} it was **{f['gap_last']:.1f} times**, because rich towns got back to {f['rich_kept']:.0%} of their old visits and poor
towns only {f['poor_kept']:.0%}.

![Visits per resident by town wealth, {f['before']} and {f['last_year']}](charts/wealth-gap.svg)

### The first version's 99.5% score was the answer, copied in

The original model predicted visits per resident, using a column it had made by dividing visits by population. That's the
same number. That column alone scores {f['copied']:.1%}. A fair test, on a later year, is in finding 7."""


def report(f: dict) -> str:
    return f"""# Findings

What {f['last_year'] - f['first_year'] + 1} years of Connecticut's public library statistics can and can't tell you. This page is written by
[`build.py`](build.py), so every number comes straight from the data.

The data covers {f['libraries']} libraries in {f['towns']} towns, from {f['first_year']} to {f['last_year']}. Years are the libraries' fiscal years, so
{f['last_year']} means July {f['last_year'] - 1} to June {f['last_year']}. Most figures are **per resident**: every library in a town is added up and
divided by the town's population. That keeps years comparable when a library didn't report, and stops a small branch
being compared with a whole city. Money is in {f['last_year']} dollars, adjusted with the US Consumer Price Index.

## 1. Visits were falling long before Covid

Connecticut residents made {f['v_first']:.1f} library visits each in {f['first_year']}, rising to a peak of {f['v_peak']:.2f} in {f['peak']}. Then visits
fell almost every year, to {f['v_before']:.2f} in {f['before']}, down {f['v_fall']:.0%}, before the pandemic began. Loans followed the same
path, peaking at {f['l_peak']:.1f} per resident in {f['l_peak_year']} and falling {f['l_fall']:.0%} by {f['before']}.

![Library visits and loans per resident each year](../charts/visits.svg)

Other everyday uses fell too. Public computer use peaked at {f['c_peak']:.1f} sessions per resident in {f['c_peak_year']}, and questions for staff peaked at
{f['q_peak']:.1f}. The data doesn't say why. Loans count every format, including e-books, so the fall isn't only print.

The one thing that grew was events. Attendance at talks, classes, story times and other events went from {f['e_first']:.2f} per
resident in {f['first_year']} to {f['e_before']:.2f} in {f['before']}, {f['e_growth']:.1f} times as many.

![Event attendance per resident each year](../charts/events.svg)

## 2. Events came back after Covid. Computers didn't

In 2021, the first full year of the pandemic, visits fell to {f['v_2021']:.2f} per resident, {f['v_low']:.0%} below {f['before']}. By {f['last_year']}
they were back to {f['v_last']:.2f}.

The comeback depends on what people came for. Event attendance per resident in {f['last_year']} was {f['back_events']:.0%} of its {f['before']} level,
a new record at {f['e_last']:.2f}. Borrowing was {f['back_loans']:.0%}. But visits were {f['back_visits']:.0%}, questions for staff
{f['back_questions']:.0%} and public computer use only {f['back_computers']:.0%}.

![Each activity in {f['last_year']} as a share of {f['before']}](../charts/what-came-back.svg)

So people still borrow, and come in for events, but fewer drop in, and far fewer use the computers. One likely reason is
that e-books can be borrowed without going in at all.

## 3. Richer towns' libraries bounced back. Poorer towns' didn't

Connecticut ranks all 169 of its towns by wealth each year, using property values and income per person. Splitting the
{f['same_towns']} towns with figures for both {f['before']} and {f['last_year']} into four equal groups by wealth shows a large gap. In {f['before']}, people in the
richest quarter made {f['rich_before']:.1f} visits each and people in the poorest quarter {f['poor_before']:.1f}. That's {f['gap_before']:.1f} times as many.

![Visits per resident by town wealth, {f['before']} and {f['last_year']}](../charts/wealth-gap.svg)

After Covid the gap grew. Rich towns got back to {f['rich_kept']:.0%} of their {f['before']} visits and poor towns only {f['poor_kept']:.0%}, so by
{f['last_year']} it was {f['rich_last']:.1f} visits against {f['poor_last']:.1f}, **{f['gap_last']:.1f} times** as many. The towns are the same in both years, so
this isn't caused by which libraries reported.

## 4. Towns that spend more on their library see more use

In {f['last_year']}, the richest quarter of towns spent ${f['rich_spend']:.0f} per resident on their libraries, and the poorest quarter
${f['poor_spend']:.0f}. Across all {f['scatter_towns']} towns, spending per resident and visits per resident go together closely, with a correlation of
{f['r']:.2f} (1 would be a perfect straight line).

![Each town's library spending and visits per resident](../charts/spending-and-visits.svg)

This shows a link, not a cause. Spending could bring people in, with longer hours and more staff, or busy libraries could
win bigger budgets. Both are likely. Town taxes paid for {f['town_share']:.0%} of library income in {f['last_year']}, so richer towns can simply afford more.

## 5. Each resident pays less, each visit costs more

After inflation, library spending rose from ${f['s_first']:.0f} per resident in {f['first_year']} to a peak of ${f['s_peak']:.0f} in {f['s_peak_year']}. Since
then it has drifted down to ${f['s_last']:.0f} in {f['last_year']}, {f['s_fall']:.0%} lower.

![Library spending per resident each year, in {f['last_year']} dollars](../charts/cost.svg)

Visits fell faster than spending, so each visit now costs more: ${f['pv_peak']:.0f} in {f['peak']}, ${f['pv_before']:.0f} in {f['before']} and ${f['pv_last']:.0f} in
{f['last_year']}. That's not waste. Visits are only one part of what a library does, and loans and events don't need one.
Spending in 2000 jumps and falls back the next year at many large libraries, which looks like a change in what was counted
rather than real money.

## 6. The first version's 99.5% score was the answer, copied in

The first version of this project trained a model to predict each library's visits per resident and reported a score
(R²) of {f['old_r2']:.1%}. But one of its inputs was a column it had made itself, visits divided by population. That's the same
thing it was predicting, and the two columns are almost identical (a correlation of {f['match']:.3f}). That one column on its
own scores {f['copied']:.1%}.

Three more things went wrong:

- **It printed the wrong error.** The number labelled "RMSE", {f['old_mse']}, was the squared error. The real figure is
  {f['old_rmse']:.2f} visits per resident.
- **It quietly dropped {f['dropped']:.0%} of the data.** Removing every row with a blank left {f['kept_rows']} rows and no year before
  {f['kept_from']}, because public computers weren't counted until then.
- **Its full score isn't even stable.** Its 25 inputs overlap so much that the same code scores differently on different
  versions of scikit-learn.

## 7. Wealth and spending explain more than half the difference between towns

A fairer question is how well you can predict a town's library use without counting it. Here each method learns from {an.TRAIN_YEARS[0]}
to {an.TRAIN_YEARS[1]} ({f['m_train']} town-years) and is tested on {an.TEST_YEAR}, which it hasn't seen. Towns made {f['m_avg']:.1f} visits per resident on average.

![How much of the difference between towns each method explains](../charts/model-scores.svg)

Guessing the state's typical town is off by {f['m_base']:.1f} visits per resident. Knowing a town's wealth explains {f['m_wealth']:.0%} of
the differences between towns. Adding its library spending per resident and its size explains {f['m_all']:.0%}, and gets
within {f['m_all_err']:.1f} visits on average. The best guess by far is the town's own figure from the year before, which explains {f['m_last']:.0%}:
library use changes slowly, and each town's habits run deep.

## What this data can't tell you

- **Why use fell.** The data shows patterns, not causes. E-books, phones and opening hours are all possible, and none is
  measured here.
- **Who uses libraries.** There's nothing about age, income or background of the people walking in, only town totals.
- **Whether fewer people have a card.** Registered borrowers fell from {f['cards_peak']:.0f} per 100 residents in {f['cards_peak_year']} to {f['cards_last']:.0f} in
  {f['last_year']}, but libraries sometimes clear out old records, so it's not clear how much of that is real.
- **Anything outside Connecticut.** This is one state's data, despite the first version calling it national.

## About the data

The Connecticut State Library publishes these figures each year for every public library in the state. A few things
needed fixing before they could be used:

- **Libraries change names.** {f['names']} names in the file are really {f['libraries']} libraries, for example "Glastonbury - East" and
  "Glastonbury, East". They're joined up in [`data/prepare.py`](../data/prepare.py).
- **{f['last_year']} is incomplete.** {f['missing_2024']} libraries that reported in {f['last_year'] - 1} are missing, including Norwalk, so totals for {f['last_year']}
  are too low. Per-resident figures leave those towns out instead.
- **Materials spending for {f['last_year']} isn't comparable.** The typical library spent {f['mat23']:.0%} of its budget on books
  and other materials in {f['last_year'] - 1} and {f['mat24']:.1%} in {f['last_year']}, which means it was counted differently. It's left blank.
- **Branch libraries have no population** of their own. {f['no_population']} rows have none, which is why figures are worked out
  by town.
- **Closed branches reported zeros** during Covid. Those rows are treated as blank, not as a year with no use.

## How it was worked out

1. [`data/prepare.py`](../data/prepare.py) tidies the download, joins renamed libraries, matches each library to its town and builds the
   inflation index.
2. [`analysis.py`](analysis.py) holds every calculation as a small, tested function.
3. [`charts.py`](charts.py) draws each chart with [bezel-charts](https://pypi.org/project/bezel-charts/).
4. [`notebooks/public_libraries_analysis.ipynb`](../notebooks/public_libraries_analysis.ipynb) walks through the same steps with the working shown.
"""


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:start -->\n).*?(\n<!-- {name}:end -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"Marker {name} not found")
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), text)


def main() -> None:
    # bezel-charts gives each gradient a random id so charts can share a page. A fixed seed keeps the
    # files identical between runs, so a rebuild only shows up in git when something really changed.
    random.seed(2026)
    CHARTS.mkdir(exist_ok=True)
    for name, draw in charts.ALL.items():
        draw().save(CHARTS / f"{name}.svg")
    f = facts()
    REPORT.write_text(report(f), encoding="utf-8")
    README.write_text(replace_block(README.read_text(encoding="utf-8"), "key-findings", key_findings(f)), encoding="utf-8")
    print(f"Wrote {len(charts.ALL)} charts, {REPORT.relative_to(ROOT)} and the README findings")


if __name__ == "__main__":
    main()
