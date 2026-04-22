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



## 1. Problem & User

The project addresses that problem by providing a user-friendly interface for searching firms and analysing their financial performance over time.

The intended users are:

\- accounting and finance students

\- business researchers

\- anyone who needs quick exploratory analysis of company financial data



## 2. Data

The dataset used in this project comes from the Compustat database accessed through WRDS. 
The main table used is `comp.funda`, which contains annual financial information for publicly listed firms.

The data were accessed on "2026/4/18 -- 2026/4/22".

The key fields used in the project include:

- `gvkey`
- `conm`
- `tic`
- `fyear`
- `revt`
- `ni`
- `at`
- `ceq`
- `lt`
- `oancf`
- `capx`



## 3. Methods

The project was developed using Python and Streamlit. The main steps in the workflow were:

- connecting to WRDS using the `wrds` Python package

- querying Compustat financial data with SQL

- cleaning and preparing the dataset with `pandas`

- creating derived financial metrics such as ROA, ROE, net margin, and free cash flow

- generating charts and summary tables for analysis

- building an interactive Streamlit interface for company search, financial exploration, and comparison



## 4. Key Findings

- The app allows users to quickly search for firms using company name, ticker, or gvkey.

- Users can view annual financial data in a clean and readable format.

- Trend charts help users understand how revenue, income, assets, and cash flow change over time.

- Financial ratios such as ROA and ROE provide more interpretable views of company performance.

- The comparison function makes it easier to compare firms on the same financial metric.



## 5. How to Run


\## 5.1 How to Run Locally

- Clone this repository to your computer

- Open the terminal and navigate to the project folder

- Install dependencies:
    pip install -r requirements.txt

- Run the application:
    streamlit run app.py

- Open the app in your browser
    streamlit will usually open automatically

- Return to the terminal  and enter the WRDS username and password


\## 5.2 Requirement

The project requires the following main Python packages:

streamlit

pandas

wrds

plotly

psycopg2-binary

statsmodels


\## 5.3 How to Use in app

- Open the app in your browser.

- Enter an exact company name, ticker, or gvkey.

- Select a company from the search results.

- Choose a year range.

- View the financial data and charts.

- Download the results if needed



## 6. Demo Link

Demo Product Link:



## 7. Limitations & Next Steps

This project has several limitations.:

- Compustat only includes companies from North America and some data is incomplete. Some indicators cannot accurately reflect the trend.

- The current search interface for companies can only precisely input the company name and other methods. If only part of the company name is entered, the company cannot be found.

- The current website is mainly used for descriptive analysis and cannot predict future financial trends and data.

Possible next steps include:

- Not limited to Compustat, other countries' data such as CSMAR can be added to improve the deficiency of only focusing on companies from North America and improve the logic for handling missing values to make the entire chart more reasonable.

- Add search assistance functions. When entering part of the company name, provide an auxiliary search bar. 

- Incorporate deep algorithms to predict the future trend of the company.







