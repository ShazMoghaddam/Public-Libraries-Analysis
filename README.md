📚 Public Libraries Dataset — Data Cleaning & Exploratory Data Analysis (EDA)
📝 Overview

This project explores and analyses the Public Libraries Dataset sourced from DATA.GOV.
It was developed as a study project to practise Python, data cleaning, exploratory analysis, and data visualisation, using tools such as:

Pandas (data manipulation)
NumPy
Matplotlib (visualisation)
Jupyter Notebook

The project includes:
✔️ Data cleaning
✔️ Feature engineering
✔️ Visualisations (histograms, scatter plots, trends, rankings)
✔️ Insights about library usage and engagement
✔️ A cleaned dataset ready for further modelling or exploration

📂 Dataset Information

Source: DATA.GOV
Format: CSV
File Used: Public_Libraries.csv
Cleaned Output: Public_Libraries_cleaned.csv
Key Fields Include
Fiscal year
Library name
County
Population served
Total library visits
Visits per capita
Expenditures (wages, operating, etc.)
Registered borrowers
Rankings and service metrics

🔧 Data Cleaning Steps

Below is a summary of the main cleaning choices implemented:

✔ 1. Standardised Column Names
Converted names to lowercase
Replaced spaces with underscores
Removed special characters
Example:
"Operating Expenditures Per Capita" → operating_expenditures_per_capita

✔ 2. Numeric Conversion

Columns such as population, visits, expenditures, and per-capita metrics were converted to numeric using:
df[col] = pd.to_numeric(df[col], errors='coerce')
This fixed formatting issues such as strings, commas, or unexpected characters.

✔ 3. Missing Values

Columns with more than 50% missing were removed
Numeric columns with mild missing percentages (<10%) were filled using the median
Categorical columns with small missing amounts were filled with "Unknown"

✔ 4. Derived Column: Visits Per Capita

If not provided in the original dataset, the following column was calculated:
visits_per_capita = total_library_visits / population_of_service_area
This helps measure community engagement in a standardised way.

🧹 Cleaned Data Preview

A preview of the cleaned dataset (as shown in the notebook):
df_cleaned.head()

📊 Visualisations Included
📈 1. Distribution Plots

Visits per capita
Population served

🔍 2. Relationship Plots

Total visits vs. population
Visits per capita vs. expenditures per capita

🗺 3. County-Level Comparisons

Counties ranked by mean visits per capita
Top libraries by total visits
Top libraries by visits per capita

📆 4. Trends Over Time

If fiscal year data is present, a line plot shows trends in:
Total library visits
Mean visits per capita
All plots are saved to:
/plots/


🔎 Key Insights
1. Smaller communities can show extremely high engagement

Some libraries serving small populations had the highest visits per capita, showing strong usage relative to community size.

2. County-level differences are significant

Certain counties consistently showed:
Higher library engagement
More visits per capita
Greater investment per resident
These counties may benefit from stronger funding or outreach programs.

3. Population correlates with total visits — but not always engagement

Larger population → more total visits
But visits per capita varied widely
This suggests that library engagement depends on more than just population size.

4. Expenditure per capita has a mixed relationship with engagement

Higher spending can lead to higher visits per capita, but the correlation is not perfectly linear.

This indicates that:
Outreach
Community programs
Accessibility
Library events
also play a major role.

5. Long-term trends (if fiscal year is available)

There may be observable increases or drops in:
Overall library visits
Per-capita engagement
These trends can reflect economic changes, population shifts, or policy updates.

🙌 Acknowledgements

Data provided by: DATA.GOV
Project created as part of a personal learning journey in Python, data science, and exploratory analysis.
