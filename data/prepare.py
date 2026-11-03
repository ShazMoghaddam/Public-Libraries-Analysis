"""Turn the Connecticut State Library download into one tidy table, plus an inflation index.

Both raw files are small, so they live in data/raw/. To fetch them again:

    curl -fL -o data/raw/Public_Libraries.csv 'https://data.ct.gov/api/views/kf75-36tt/rows.csv?accessType=DOWNLOAD'
    python data/prepare.py

The inflation file is the US Consumer Price Index for All Urban Consumers (CPI-U, series CUUR0000SA0) from the
Bureau of Labor Statistics, one row per month. Its source is in data/sources.json.

What this script changes, and why:

- Libraries that were renamed are joined up, so "Glastonbury - East" and "Glastonbury, East" are one library.
- Each library gets its town. Some towns have several libraries, and only the main one carries the town's population.
- The per-resident columns in the download are rounded and sometimes disagree with the totals, so they're dropped
  and worked out again from the totals when needed.
- Rows where a closed branch reported every figure as zero become blanks, so they don't count as a year of no use.
- Materials spending for 2024 becomes blank. It falls from 9% of the typical library's budget to 1.5% in one year,
  which is a change in what was counted, not a real cut.
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent
RAW = DATA / "raw" / "Public_Libraries.csv"
CPI = DATA / "raw" / "cpi_u.csv"

COLUMNS = {
    "Fiscal Year": "year",
    "Library": "name",
    "County": "county",
    "AENGLC Rank": "wealth_rank",
    "Population of Service Area": "population",
    "Total Library Visits": "visits",
    "Total Registered Borrowers": "borrowers",
    "Reference Questions": "questions",
    "Total Circulation": "loans",
    "Total Programs (Synchronous + Prerecorded)": "events",
    "Total Program Attendance & Views": "attendance",
    "Use of Public Internet Computers": "computer_uses",
    "Total Collection": "collection",
    "Total Operating Income": "income",
    "Town Tax Appropriation for Library": "town_funding",
    "Library Materials Expenditures": "materials_spending",
    "Wages & Salaries Expenditures": "wages",
    "Operating Expenditures": "spending",
}
ACTIVITY = ["visits", "borrowers", "questions", "loans", "events", "attendance", "computer_uses", "collection",
            "income", "town_funding", "materials_spending", "wages", "spending"]

# Names that changed over the years, written as a key with everything but letters removed. Each maps to the key the
# library is filed under. Woodstock's East library becomes May in 2008, with the same visits and collection size.
RENAMED = {
    "berlinberlinpeck": "berlinpeck",
    "eastberlin": "berlineastberlin",
    "bloomfield": "bloomfieldprosser",
    "derbyneck": "derbyderbyneck",
    "essexessexlibrary": "essex",
    "fairfieldfairfieldpublic": "fairfield",
    "glastonburywellst": "glastonburywellest",
    "greenwichgreenwichlibrary": "greenwich",
    "grotongrotonpublic": "groton",
    "newhartfordbeekley": "newhartfordliciamb",
    "windhamfree": "windhamwindhamfree",
    "woodstockeast": "woodstockmay",
}
# Library names that don't start with their town
TOWNS = {"berlinfree": "Berlin", "berlineastberlin": "Berlin", "derbyderbyneck": "Derby", "windhamwindhamfree": "Windham"}


def key(name: str) -> str:
    found = re.sub(r"[^a-z]", "", name.lower())
    return RENAMED.get(found, found)


def town(name: str) -> str:
    for separator in (" - ", ",", "-"):
        if separator in name:
            return name.split(separator)[0].strip()
    return name.strip()


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.rename(columns=lambda c: c.strip()).rename(columns=COLUMNS)[list(COLUMNS.values())].copy()
    d["name"] = d["name"].str.strip().str.replace(r"\s+", " ", regex=True)
    d["library"] = d["name"].map(key)
    d["town"] = [TOWNS.get(k, town(n)) for k, n in zip(d["library"], d["name"])]
    # Show each library under the name it used most often
    d["name"] = d.groupby("library")["name"].transform(lambda s: s.value_counts().index[0])

    closed = d[["visits", "loans", "spending"]].eq(0).all(axis=1)
    d.loc[closed, ACTIVITY] = np.nan
    d.loc[d["year"] == 2024, "materials_spending"] = np.nan

    first = ["year", "library", "name", "town", "county", "wealth_rank", "population"]
    return d[first + ACTIVITY].sort_values(["year", "library"]).reset_index(drop=True)


def fiscal_year_prices(monthly: pd.DataFrame) -> pd.DataFrame:
    """Average prices over each July to June fiscal year, and what a dollar then is worth in 2024 dollars."""
    fiscal = monthly["year"] + (monthly["month"] >= 7)
    cpi = monthly.groupby(fiscal)["cpi"].agg(["mean", "size"])
    cpi = cpi[cpi["size"] == 12]["mean"].rename("cpi").to_frame()
    cpi.index.name = "year"
    cpi["to_2024_dollars"] = cpi.loc[2024, "cpi"] / cpi["cpi"]
    return cpi.round(4).reset_index()


def main(raw_path: Path = RAW) -> None:
    libraries = tidy(pd.read_csv(raw_path))
    libraries.to_csv(DATA / "libraries.csv", index=False)
    prices = fiscal_year_prices(pd.read_csv(CPI))
    prices.to_csv(DATA / "prices.csv", index=False)
    print(f"{len(libraries):,} rows, {libraries['library'].nunique()} libraries, {libraries['town'].nunique()} towns, "
          f"{libraries['year'].min()} to {libraries['year'].max()}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else RAW)
