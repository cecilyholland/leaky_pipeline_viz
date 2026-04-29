Project: Leaky Pipeline — Women in Tech
Course: CPSC 5530 Data Visualization and Exploration
Due: Sunday May 4th 11:59pm
Repo: leaky-pipeline-viz

Project Domain & Narrative
Four-act data story about women in tech:

Act 1 — The Pipeline: Women in CS/tech education (IPEDS)
Act 2 — The Workforce: Women in tech occupations (BLS)
Act 3 — The Data Gap: Where measurement breaks down (NSF NCSES)
Act 4 — The Cliff: Big tech companies stopping DEI reporting (compiled dataset)

Central framing: the "leaky pipeline" — women enter tech education and jobs but leave by ~age 35, and the data infrastructure to study this is itself fragmenting.

Dataset 1 — IPEDS Completions

Source: nces.ed.gov/ipeds → Complete Data Files → C[year]_A.csv
Years: 2010, 2013, 2016, 2019, 2022, 2024
CIP scope: CIP 11 (all computing subfields) + CIP 14 (engineering)
Named tracks: Computer Science (11.07), Cybersecurity (11.10), Information & Data Science (11.04), IT & General Computing (11.01), Software & Media Apps (11.08), Networking & Systems (11.09), Computer Engineering (14.09), Electrical Engineering (14.10)
Script: ipeds_preprocessing.py
Key fix needed: replace pd.NA with float("nan") in pct_women calculation to fix .round(1) TypeError
Outputs: ipeds_national_by_track.csv, ipeds_bachelors_by_track.csv, ipeds_cs_cyber_ladder.csv, ipeds_filtered_raw.csv
Still needed: HD2024.csv (Institutional Characteristics file) to enable state-level choropleth — uncomment add_state() block after downloading
Key finding: CS bachelor's women % went from 18.3% (2010) → 23.8% (2024), only +5.5pp over 14 years despite total degrees nearly tripling


Dataset 2 — BLS CPS

Source: bls.gov/cps/tables.htm → Household Data Annual Averages
Sheets used: cpsaat11 (occupation × sex) and cpsaat11b (occupation × age)
Files: cpsa2015.xlsx through cpsa2024.xlsx — stored in /bls_datasets/
Script: bls_preprocessing.py
Outputs saved to /processed_bls_data/: bls_tech_by_sex.csv, bls_tech_by_age.csv, bls_combined_clean.csv
Important note: women_count_k_approx in combined file = total_in_bracket × pct_women — this is an approximation since BLS doesn't publish age × sex × occupation. Flag in report.
Key findings:

Software Developers: 17.9% → 20.3% women (2015–2024), near-stagnant

Database Administrators: 38.0% → 28.9%, going backwards
Computer Systems Analysts: 34.2% → 43.1%, the one field approaching parity
Information Security Analysts: COVID dip from 24.9% (2018) → 11.4% (2020), still not recovered
Age cliff visible: Software Devs peak at 25–34 bracket (742k) dropping 24% at 35–44 (567k) then 35% more at 45–54 (366k)




Dataset 3 — NSF NCSES WMPD 2023

Correct URL: ncses.nsf.gov/pubs/nsf23315
Data tables: ncses.nsf.gov/pubs/nsf23315/data-tables
~70 downloadable Excel files organized by topic
Tables needed: Employment (women in S&E occupations by field/year/race), Enrollment (women in CS/engineering grad programs), Degrees (CS/computing by gender)
Purpose: Act 3 — show where data gets sparse by field and intersectional category; visualize the research gap itself


Dataset 4 — Big Tech Diversity Reports

File: big_tech_diversity.csv (already created)
Companies: Google, Apple, Microsoft, Meta, Amazon
Years: 2014–2025 where available
Key story: Google, Meta, Microsoft confirmed no 2025 DEI reports — data cliff at 2025
Apple and Amazon still reporting
Columns: company, year, women_overall_pct, women_technical_pct, reporting_status, source
Note: Google numbers most reliable (published full historical table); others compiled from annual PDFs — spot-check before submitting


Visualization Plan (Plotly)
ActDatasetChart TypeKey InteractionsAct 1IPEDSChoropleth map + multi-lineYear slider, dropdown by track, zoomAct 2BLSScatter/bubble + barAge bracket filter, highlight by fieldAct 3NSF NCSESFaceted heatmapMissing-data overlay, animated transitionsAct 4Big TechMulti-line with cliffDashed lines where reporting stopped, annotations

Technical Notes

Conda env: plda2
openpyxl required for BLS xlsx reading
Common dtype fix: always load CIPCODE with dtype={"CIPCODE": str} and recompute CIP2 after load
pct_women calculation: use float("nan") not pd.NA for .round(1) compatibility
All scripts run from repo root
IPEDS files stored at repo root; BLS files in /bls_datasets/; BLS outputs in /processed_bls_data/


Report Requirements

15+ pages
Interactive visualizations saved as HTML
YouTube video demo
Python code (.ipynb or .py)
Dataset links
The "real-time data" language in the rubric is motivational framing, not a live API requirement