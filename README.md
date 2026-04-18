\# Changyuan Tong\_2471760 ACC102 Track4 README 



\## Overview



TCY Data Analysis Assistant is an interactive Python-based data analysis tool built with \*\*Streamlit\*\*.  

It is designed to help users explore company financial performance using \*\*Compustat data from WRDS\*\*.



The tool lets users:

\- search for companies by exact gvkey, company name, or ticker

\- retrieve financial data for a selected company

\- view trends in key financial indicators

\- calculate and analyse common financial ratios

\- compare multiple companies

\- download query results as CSV files



This project was developed for the ACC102 Mini Assignment under Track 4: Interactive Data Analysis Tool.



\---



\## Analytical Problem



Many users need a simple and interactive way to explore company-level financial data without manually writing SQL or Python code.  

This tool addresses that problem by providing a user-friendly interface for searching firms and analysing their financial performance over time.



The intended users are:

\- accounting and finance students

\- business researchers

\- anyone who needs quick exploratory analysis of company financial data



\---



\## Data Source



The project uses \*\*Compustat data accessed through WRDS\*\*, specifically the `comp.funda` table.



\### Main fields used include:

\- `gvkey`

\- `conm`

\- `tic`

\- `fyear`

\- `revt`

\- `ni`

\- `at`

\- `ceq`

\- `lt`

\- `oancf`

\- `capx`

\- and other related financial variables



\### Data access date:

\- 2026/4/18



\### Notes:

\- Company search uses \*\*exact matching\*\* on `gvkey`, `conm`, and `tic`

\- Financial data are filtered by standard Compustat conditions where appropriate

\- Some variables may be missing for certain firms or years



\---



\## How to Run Locally



&#x20;### 1. Clone this repository to your computer



&#x20;### 2. Open the terminal and navigate to the project folder



&#x20;### 3. Install dependencies:

&#x20;   pip install -r requirements.txt



\###  4. Run the application:

&#x20;   streamlit run app.py



\### 5. Open the app in your browser

&#x20;  streamlit will usually open automatically



\### 6. Return to the terminal  and enter the WRDS username and password

&#x20;

###### \---



\## Requirement



The project requires the following main Python packages:



streamlit

pandas

wrds

plotly

psycopg2-binary

statsmodels



###### \---



\## How to Use



\### 1.Open the app in your browser.



\### 2.Enter an exact company name, ticker, or gvkey.



\### 3.Select a company from the search results.



\### 4.Choose a year range.



\### 5.View the financial data and charts.



\### 6.Download the results if needed.



\---



\## Features



\### 1. Company Search

\- Search for companies using exact `gvkey`, `conm`, or `tic`

\- Select a company from the returned search results



\### 2. Financial Data Query

\- Retrieve annual financial data for a selected company

\- Choose a custom year range



\### 3. Indicator-Based Analysis

\- Explore variables grouped by category:

&#x20; - Profitability

&#x20; - Balance Sheet

&#x20; - Cash Flow

&#x20; - Growth and Efficiency

&#x20; - Valuation



\### 4. Ratio Analysis

\- Automatically calculate selected financial ratios, such as: 

&#x20; - ROA

&#x20; - ROE

&#x20; - Gross Margin

&#x20; - Net Margin

&#x20; - Current Ratio

&#x20; - Asset Turnover



\### 5. Visualisation

\- Display line charts, bar charts, and area charts

\- Provide clear trend analysis over time



\### 6. Multi-Company Comparison

\- Compare selected companies on one financial metric

\- Visualise differences across firms



\### 7. Data Export

\- All results can be downloaded as CSV files for further analysis.



\---



