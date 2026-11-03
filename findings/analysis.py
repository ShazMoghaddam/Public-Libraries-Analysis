"""The analysis behind every finding. Plain functions, no charts and no files written.

Most figures are per resident and worked out by town: every library in a town is added up and divided by the town's
population. That keeps years comparable when a library is missing, as ten are in 2024, and stops a branch library
being compared with a whole city. Money is in 2024 dollars.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

DATA = Path(__file__).resolve().parent.parent / "data"
MEASURES = ["visits", "loans", "attendance", "questions", "computer_uses", "borrowers", "real_spending"]
BEFORE, LATEST = 2019, 2024
QUARTERS = ["Richest quarter", "Second", "Third", "Poorest quarter"]
FIRST_VERSION_R2 = 0.995  # Saved in the original notebook's output
FIRST_VERSION_MSE = 0.0725  # Printed as "RMSE" in the original, but it's the squared error


@lru_cache
def libraries() -> pd.DataFrame:
    d = pd.read_csv(DATA / "libraries.csv")
    prices = pd.read_csv(DATA / "prices.csv").set_index("year")["to_2024_dollars"]
    d["real_spending"] = d["spending"] * d["year"].map(prices)
    return d


@lru_cache
def towns() -> pd.DataFrame:
    """One row per town and year. Only the main library carries the town's population, so it's the largest one."""
    d = libraries()
    sums = {m: (m, lambda s: s.sum(min_count=1)) for m in MEASURES}
    t = d.groupby(["year", "town"]).agg(population=("population", "max"), wealth_rank=("wealth_rank", "min"), **sums)
    t = t.reset_index()
    for m in MEASURES:
        t[f"{m}_pr"] = t[m] / t["population"]
    return t


def per_resident(measure: str) -> pd.Series:
    """Statewide figure per resident each year, from the towns that reported it."""
    t = towns().dropna(subset=["population", measure])
    years = t.groupby("year")
    return years[measure].sum() / years["population"].sum()


# Finding 1: fewer visits, long before Covid ---------------------------------------------------------

def long_run() -> pd.DataFrame:
    return pd.DataFrame({m: per_resident(m) for m in ["visits", "loans", "attendance", "questions", "computer_uses"]})


# Finding 2: what came back after Covid ---------------------------------------------------------------

RECOVERY = {"attendance": "Event attendance", "loans": "Loans", "visits": "Visits", "questions": "Questions for staff",
            "computer_uses": "Public computer use"}


def recovery() -> pd.Series:
    """Each activity per resident in 2024, as a share of 2019."""
    rates = long_run()
    return (rates.loc[LATEST] / rates.loc[BEFORE])[list(RECOVERY)].rename(RECOVERY).sort_values(ascending=False)


# Finding 3: richer towns, and the gap since Covid -----------------------------------------------------

def same_towns() -> pd.Index:
    """Towns with visits, population and a wealth rank in both 2019 and 2024."""
    t = towns().dropna(subset=["visits", "population", "wealth_rank"]).set_index("town")
    return t[t["year"] == BEFORE].index.intersection(t[t["year"] == LATEST].index)


def wealth_quarters() -> pd.Series:
    """Each town's quarter by its 2019 wealth rank. Rank 1 is the richest town in Connecticut."""
    t = towns().set_index("town")
    ranks = t[t["year"] == BEFORE].loc[same_towns(), "wealth_rank"]
    return pd.qcut(ranks, 4, labels=QUARTERS)


def by_wealth(measure: str = "visits") -> pd.DataFrame:
    quarters = wealth_quarters()
    t = towns().set_index("town")
    result = {}
    for year in (BEFORE, LATEST):
        rows = t[t["year"] == year].loc[quarters.index]
        groups = rows.groupby(quarters, observed=True)
        result[year] = groups[measure].sum() / groups["population"].sum()
    table = pd.DataFrame(result)
    table["kept"] = table[LATEST] / table[BEFORE]
    return table


# Finding 4: spending and use ---------------------------------------------------------------------------

def spending_and_visits(year: int = LATEST) -> pd.DataFrame:
    t = towns()
    rows = t[t["year"] == year].dropna(subset=["visits_pr", "real_spending_pr", "wealth_rank"])
    return rows[["town", "wealth_rank", "population", "visits_pr", "real_spending_pr"]].set_index("town")


def spending_link(year: int = LATEST) -> dict:
    rows = spending_and_visits(year)
    return {
        "r": rows["visits_pr"].corr(rows["real_spending_pr"]),
        "rank_r": rows["visits_pr"].corr(rows["real_spending_pr"], method="spearman"),
        "towns": len(rows),
    }


# Finding 5: what libraries cost ------------------------------------------------------------------------

def cost() -> pd.DataFrame:
    spend = per_resident("real_spending")
    return pd.DataFrame({"per_resident": spend, "per_visit": spend / per_resident("visits")})


# Finding 6: the first version's model --------------------------------------------------------------------

def first_version() -> dict:
    """Rerun the original model with only the column that gave the answer away.

    The original's full set of 25 overlapping columns is numerically fragile: the same code and split score 0.995 with
    scikit-learn 1.8 and 0.88 with 1.9. So only the copied column, which scores the same everywhere, is used here.
    """
    raw = pd.read_csv(DATA / "raw" / "Public_Libraries.csv")
    raw["visits_per_capita"] = raw["Total Library Visits"] / raw["Population of Service Area"]
    target = "Library Visits Per Capita Served"
    numbers = raw.select_dtypes(include=[np.number]).dropna()
    # The same split as the original: random, a quarter held back, seed 42
    x_train, x_test, y_train, y_test = train_test_split(
        numbers[["visits_per_capita"]], numbers[target], test_size=0.25, random_state=42
    )
    copied = r2_score(y_test, LinearRegression().fit(x_train, y_train).predict(x_test))
    return {
        "copied": copied, "printed_rmse": FIRST_VERSION_MSE, "true_rmse": FIRST_VERSION_MSE ** 0.5,
        "match": numbers[target].corr(numbers["visits_per_capita"]),
        "rows_kept": len(numbers), "rows": len(raw), "first_year": int(numbers["Fiscal Year"].min()),
    }


# Finding 7: a fair test -------------------------------------------------------------------------------------

TRAIN_YEARS, TEST_YEAR = (2010, 2017), BEFORE
FEATURES = {"Town wealth": ["wealth_rank"], "Wealth, spending and size": ["wealth_rank", "real_spending_pr", "log_population"]}


@lru_cache
def models() -> pd.DataFrame:
    """Predict each town's visits per resident in 2019, learning only from 2010 to 2017."""
    t = towns().dropna(subset=["visits_pr", "real_spending_pr", "wealth_rank", "population"]).copy()
    t = t[t["visits_pr"] > 0].sort_values(["town", "year"])
    t["log_population"] = np.log(t["population"])
    t["last_year"] = t.groupby("town")["visits_pr"].shift()
    t["previous"] = t.groupby("town")["year"].shift()
    train = t[t["year"].between(*TRAIN_YEARS)]
    test = t[t["year"] == TEST_YEAR]

    guesses = {"The state's typical town": np.full(len(test), train["visits_pr"].median())}
    for name, columns in FEATURES.items():
        guesses[name] = LinearRegression().fit(train[columns], train["visits_pr"]).predict(test[columns])
    rows = {name: (r2_score(test["visits_pr"], g), mean_absolute_error(test["visits_pr"], g), len(test))
            for name, g in guesses.items()}
    known = test[test["previous"] == TEST_YEAR - 1]
    rows["The town's own figure last year"] = (r2_score(known["visits_pr"], known["last_year"]),
                                               mean_absolute_error(known["visits_pr"], known["last_year"]), len(known))
    table = pd.DataFrame(rows, index=["explained", "error", "towns"]).T
    table["towns"] = table["towns"].astype(int)
    table.attrs["train_rows"] = len(train)
    table.attrs["average"] = test["visits_pr"].mean()
    return table


# Data quality, for the report and the changelog ---------------------------------------------------------------

def data_notes() -> dict:
    raw = pd.read_csv(DATA / "raw" / "Public_Libraries.csv")
    d = libraries()
    years = d.groupby("year")["library"].nunique()
    in_2023 = set(d.loc[d["year"] == 2023, "library"])
    in_2024 = set(d.loc[d["year"] == 2024, "library"])
    materials = raw["Library Materials Expenditures"] / raw["Operating Expenditures"]
    by_year = materials.groupby(raw["Fiscal Year"]).median()
    return {
        "names": raw["Library"].nunique(), "libraries": d["library"].nunique(), "towns": d["town"].nunique(),
        "rows": len(raw), "missing_2024": len(in_2023 - in_2024), "usual": int(years.loc[2010:2023].median()),
        "materials_2023": by_year[2023], "materials_2024": by_year[2024],
        "no_population": int(raw["Population of Service Area"].isna().sum()),
    }


def town_share(year: int = LATEST) -> float:
    """Share of library income paid by town taxes."""
    rows = libraries()[libraries()["year"] == year]
    return rows["town_funding"].sum() / rows["income"].sum()
