"""Checks that the data is sound and the findings hold up. Run from the repository root with `pytest`."""

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "findings"), str(ROOT / "data")]

import analysis as an  # noqa: E402
import charts  # noqa: E402
import prepare  # noqa: E402


def raw(**rows) -> pd.DataFrame:
    """A tiny download with one row per library name, every figure set to 10 unless given."""
    frame = pd.DataFrame({column: [10.0] * len(rows) for column in prepare.COLUMNS})
    frame["Fiscal Year"] = [year for year, _ in rows.values()]
    frame["Library"] = [name for _, name in rows.values()]
    frame["County"] = "Hartford"
    return frame


# Preparing the data -------------------------------------------------------------------------------------

def test_renamed_libraries_are_joined():
    d = prepare.tidy(raw(a=(2010, "Glastonbury - East"), b=(2011, "Glastonbury, East"), c=(2024, "Greenwich - Greenwich Library"),
                         d=(2023, "Greenwich")))
    assert d["library"].nunique() == 2
    assert d.groupby("library")["name"].nunique().eq(1).all(), "each library should show under one name"


@pytest.mark.parametrize("name, town", [
    ("Ashford-Babcock", "Ashford"), ("Berlin Free", "Berlin"), ("East Berlin", "Berlin"), ("Derby Neck", "Derby"),
    ("New Hartford - Bakerville", "New Hartford"), ("Woodstock, North", "Woodstock"), ("East Hartford", "East Hartford"),
])
def test_each_library_gets_its_town(name, town):
    assert prepare.tidy(raw(a=(2010, name))).loc[0, "town"] == town


def test_a_closed_branch_reporting_zeros_becomes_blank():
    frame = raw(a=(2021, "Woodstock - North"))
    frame[["Total Library Visits", "Total Circulation", "Operating Expenditures"]] = 0
    assert prepare.tidy(frame)[["visits", "loans", "spending"]].isna().all(axis=None)


def test_materials_spending_for_2024_is_left_out():
    d = prepare.tidy(raw(a=(2023, "Avon"), b=(2024, "Avon")))
    assert d.loc[d["year"] == 2023, "materials_spending"].notna().all()
    assert d.loc[d["year"] == 2024, "materials_spending"].isna().all()


def test_fiscal_years_run_july_to_june():
    monthly = pd.DataFrame({"year": [2023] * 12 + [2024] * 12, "month": list(range(1, 13)) * 2,
                            "cpi": [100.0] * 6 + [200.0] * 12 + [300.0] * 6})
    prices = prepare.fiscal_year_prices(monthly).set_index("year")
    assert prices.loc[2024, "cpi"] == 200 and prices.loc[2024, "to_2024_dollars"] == 1
    assert 2023 not in prices.index, "a fiscal year with missing months shouldn't appear"


# The data in the repo ---------------------------------------------------------------------------------------

def test_raw_download_is_complete():
    d = pd.read_csv(an.DATA / "raw" / "Public_Libraries.csv")
    assert d.shape == (5278, 27)
    assert (d["Fiscal Year"].min(), d["Fiscal Year"].max()) == (1996, 2024)


def test_tidy_file_matches_prepare():
    fresh = prepare.tidy(pd.read_csv(an.DATA / "raw" / "Public_Libraries.csv"))
    saved = pd.read_csv(an.DATA / "libraries.csv")
    pd.testing.assert_frame_equal(fresh, saved, check_dtype=False)


def test_one_row_per_library_and_year():
    assert not an.libraries().duplicated(["year", "library"]).any()


def test_town_populations_add_up_to_connecticut():
    """Connecticut had about 3.6 million people in 2019. Double counting branches would give far more."""
    population = an.towns().query("year == 2019")["population"].sum()
    assert 3.4e6 < population < 3.7e6


def test_libraries_in_a_town_share_its_wealth_rank():
    ranks = an.libraries().groupby(["year", "town"])["wealth_rank"].nunique()
    assert (ranks > 1).sum() <= 2


def test_inflation_index_covers_every_year():
    prices = pd.read_csv(an.DATA / "prices.csv").set_index("year")
    assert list(prices.index) == list(range(1996, 2025))
    assert prices["to_2024_dollars"].is_monotonic_decreasing


# The findings ---------------------------------------------------------------------------------------------------

def test_visits_peaked_before_covid_and_fell():
    visits = an.long_run()["visits"]
    assert visits.loc[:2019].idxmax() == 2010
    assert visits[2019] < 0.85 * visits[2010]


def test_2024_visits_agree_with_published_figures():
    """CT Mirror reported about 3.9 visits per resident for the following year, as libraries kept recovering."""
    assert 3.5 < an.long_run()["visits"][2024] < 3.9


def test_events_came_back_and_computers_didnt():
    back = an.recovery()
    assert back.index[0] == "Event attendance" and back.iloc[0] > 1
    assert back.index[-1] == "Public computer use" and back.iloc[-1] < 0.5


def test_the_wealth_gap_grew():
    table = an.by_wealth()
    gap = table.iloc[0] / table.iloc[-1]
    assert gap[an.LATEST] > gap[an.BEFORE] > 2
    assert table["kept"].iloc[0] > table["kept"].iloc[-1]
    assert len(an.same_towns()) >= 150


def test_spending_and_visits_go_together():
    assert an.spending_link()["r"] > 0.6


def test_the_copied_column_gives_the_first_score_away():
    first = an.first_version()
    assert first["copied"] > 0.99 and first["match"] > 0.99


def test_fair_methods_rank_as_reported():
    explained = an.models()["explained"]
    assert explained.iloc[0] < explained["Town wealth"] < explained["Wealth, spending and size"] < explained.iloc[-1]
    assert 0.5 < explained["Wealth, spending and size"] < 0.7


# The outputs ---------------------------------------------------------------------------------------------------

def test_every_chart_is_built():
    for name in charts.ALL:
        assert (ROOT / "charts" / f"{name}.svg").exists(), name


@pytest.mark.parametrize("page", ["README.md", "findings/README.md"])
def test_pages_link_to_real_files_and_have_no_gaps(page):
    path = ROOT / page
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"\{f\[|nan|None", text)
    for link in re.findall(r"\]\(((?:\.\./)?[\w/.-]+\.(?:svg|py|md|ipynb|json))\)", text):
        assert (path.parent / link).resolve().exists(), link
