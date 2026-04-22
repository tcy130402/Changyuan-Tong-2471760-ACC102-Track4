import streamlit as st
import pandas as pd
import wrds
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# 1. Page settings
# ============================================================
st.set_page_config(
    page_title="TCY Data Analysis Assistant",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# 2. Styling
# ============================================================
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 3. WRDS Connection
# ============================================================
@st.cache_resource
def get_conn():
    try:
        conn = wrds.Connection()
        return conn
    except Exception as e:
        st.error(f"WRDS connection failed: {e}")
        return None

conn = get_conn()
if conn is None:
    st.error("Unable to connect to WRDS. Please check your network and account settings.")
    st.stop()

# ============================================================
# 4. Financial Indicator Definitions
# ============================================================
INDICATOR_CATEGORIES = {
    "📊 Profitability": {
        "Revenue (revt)": "revt",
        "Net Income (ni)": "ni",
        "Gross Profit (gp)": "gp",
        "Operating Income (oiadp)": "oiadp",
        "EBITDA (ebitda)": "ebitda",
        "EPS Basic (epspx)": "epspx",
        "EPS Diluted (epsfi)": "epsfi",
    },
    "💰 Balance Sheet": {
        "Total Assets (at)": "at",
        "Total Liabilities (lt)": "lt",
        "Common Equity (ceq)": "ceq",
        "Total Debt (dltt)": "dltt",
        "Current Assets (act)": "act",
        "Current Liabilities (lct)": "lct",
        "Inventory (invt)": "invt",
        "Accounts Receivable (rect)": "rect",
    },
    "💵 Cash Flow": {
        "Operating Cash Flow (oancf)": "oancf",
        "Capital Expenditure (capx)": "capx",
        "Cash & Short-Term Investments (che)": "che",
        "Dividends (dvc)": "dvc",
        "Free Cash Flow (derived)": "free_cash_flow",
    },
    "📈 Growth & Efficiency": {
        "Revenue (revt)": "revt",
        "Total Assets (at)": "at",
        "R&D Expense (xrd)": "xrd",
        "SG&A Expense (xsga)": "xsga",
        "Employees (emp)": "emp",
        "Depreciation (dp)": "dp",
    },
    "🏦 Valuation": {
        "Shares Outstanding (csho)": "csho",
        "Stock Price Close (prcc_f)": "prcc_f",
        "Book Value Per Share (bkvlps)": "bkvlps",
        "Market Value (mkvalt)": "mkvalt",
        "Common Equity (ceq)": "ceq",
    },
}

ALL_FIELDS = set()
for cat in INDICATOR_CATEGORIES.values():
    for field in cat.values():
        if field != "free_cash_flow":
            ALL_FIELDS.add(field)

# ============================================================
# 5. Company Search: Exact Match
# ============================================================
@st.cache_data(ttl=600)
def search_companies(keyword):
    try:
        kw = keyword.replace("'", "''")  # escape single quotes

        sql = f"""
            SELECT DISTINCT gvkey, conm, tic
            FROM comp.funda
            WHERE (
                gvkey::text = '{kw}'
                OR UPPER(conm) = UPPER('{kw}')
                OR UPPER(tic) = UPPER('{kw}')
            )
            ORDER BY conm
            LIMIT 100
        """
        df = conn.raw_sql(sql)

        if df.empty:
            return pd.DataFrame()

        df["gvkey"] = df["gvkey"].astype(str)
        df["conm"] = df["conm"].fillna("NA")
        df["tic"] = df["tic"].fillna("N/A")
        df["display"] = df["tic"] + " — " + df["conm"] + " (" + df["gvkey"] + ")"
        return df

    except Exception as e:
        st.error(f"Search failed: {e}")
        return pd.DataFrame()

# ============================================================
# 6. Query Financial Data by gvkey
# ============================================================
@st.cache_data(ttl=600)
def query_financial_data(selected_gvkey, start_year, end_year, fields):
    try:
        field_str = ", ".join(fields)
        sql = f"""
            SELECT
                fyear AS year,
                gvkey,
                conm AS company_name,
                tic,
                {field_str}
            FROM comp.funda
            WHERE gvkey = '{selected_gvkey}'
              AND fyear BETWEEN {start_year} AND {end_year}
              AND indfmt = 'INDL'
              AND datafmt = 'STD'
              AND popsrc = 'D'
              AND consol = 'C'
            ORDER BY fyear
        """
        df = conn.raw_sql(sql)

        if df.empty:
            return pd.DataFrame()

        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        for f in fields:
            if f in df.columns:
                df[f] = pd.to_numeric(df[f], errors="coerce")

        df = df.dropna(subset=["year"])
        df["year"] = df["year"].astype(int)
        return df

    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()

# ============================================================
# 7. Derived Indicators
# ============================================================
def add_derived_fields(df):
    if "oancf" in df.columns and "capx" in df.columns:
        df["free_cash_flow"] = df["oancf"] - df["capx"].abs()

    if "ni" in df.columns and "at" in df.columns:
        df["roa"] = (df["ni"] / df["at"]).where(df["at"] != 0)

    if "ni" in df.columns and "ceq" in df.columns:
        df["roe"] = (df["ni"] / df["ceq"]).where(df["ceq"] != 0)

    if "gp" in df.columns and "revt" in df.columns:
        df["gross_margin"] = (df["gp"] / df["revt"]).where(df["revt"] != 0)

    if "ni" in df.columns and "revt" in df.columns:
        df["net_margin"] = (df["ni"] / df["revt"]).where(df["revt"] != 0)

    if "act" in df.columns and "lct" in df.columns:
        df["current_ratio"] = (df["act"] / df["lct"]).where(df["lct"] != 0)

    if "revt" in df.columns and "at" in df.columns:
        df["asset_turnover"] = (df["revt"] / df["at"]).where(df["at"] != 0)

    return df

# ============================================================
# 8. Metric Cards
# ============================================================
def show_metric_cards(df, field):
    if field not in df.columns:
        st.info("No data available for this indicator.")
        return

    values = pd.to_numeric(df[field], errors="coerce").dropna()
    if values.empty:
        st.info("No data available for this indicator.")
        return

    latest = values.iloc[-1]
    earliest = values.iloc[0]
    change = ((latest - earliest) / abs(earliest)) * 100 if earliest != 0 else None

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Latest", f"{latest:,.2f}")
    with c2:
        st.metric("Maximum", f"{values.max():,.2f}")
    with c3:
        st.metric("Minimum", f"{values.min():,.2f}")
    with c4:
        st.metric("Average", f"{values.mean():,.2f}")
    with c5:
        st.metric("Total Change", f"{change:,.1f}%" if change is not None else "N/A")

# ============================================================
# 9. Charts
# ============================================================
def show_charts(df, field, display_name, company_name):
    values = df.dropna(subset=[field]) if field in df.columns else pd.DataFrame()
    if values.empty:
        st.info("Not enough data to generate charts.")
        return

    tab1, tab2, tab3 = st.tabs(["📈 Line Chart", "📊 Bar Chart", "📉 Area Chart"])

    with tab1:
        fig = px.line(values, x="year", y=field, markers=True, title=f"{company_name} — {display_name} Trend")
        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.bar(values, x="year", y=field, title=f"{company_name} — {display_name} Bar Chart")
        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = px.area(values, x="year", y=field, title=f"{company_name} — {display_name} Area Chart")
        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 10. Download
# ============================================================
def show_download(df, filename):
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Download data as CSV", data=csv, file_name=filename, mime="text/csv")

# ============================================================
# 11. Title
# ============================================================
st.markdown('<p class="main-title">📊 TCY Data Analysis Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">An interactive company financial data analysis tool based on Compustat</p>', unsafe_allow_html=True)

# ============================================================
# 12. Sidebar
# ============================================================
with st.sidebar:
    st.header("📂 Navigation")
    page = st.radio("Select a section", ["🏠 Home", "🔍 Query by Indicator Category", "📐 Financial Ratio Analysis", "📊 Multi-company Comparison"], index=0)
    st.divider()
    st.markdown("### Data Source")
    st.markdown("Compustat `comp.funda`")
    st.caption("Company search and financial queries are based on `comp.funda`; search uses exact match")

# ============================================================
# 13. Home
# ============================================================
if page == "🏠 Home":
    st.subheader("Welcome to TCY Data Analysis Assistant")
    st.markdown("""
    This is an interactive financial data analysis tool based on **Compustat**.

    How to use:
    1. Enter the exact company name, ticker, or gvkey
    2. Select a company from the search results
    3. Choose a time range
    4. View the data and charts
    """)

    st.info("Recommended input: a full company name, full ticker, or known gvkey")

    for cat_name, indicators in INDICATOR_CATEGORIES.items():
        with st.expander(cat_name):
            for display_name in indicators.keys():
                st.write(f"- {display_name}")

# ============================================================
# 14. Query by Indicator Category
# ============================================================
elif page == "🔍 Query by Indicator Category":
    st.subheader("🔍 Query by Indicator Category")

    category = st.selectbox("Step 1: Select an indicator category", list(INDICATOR_CATEGORIES.keys()))
    indicators = INDICATOR_CATEGORIES[category]

    display_name = st.selectbox("Step 2: Select a specific indicator", list(indicators.keys()))
    field = indicators[display_name]

    st.markdown("#### Step 3: Search for a company")
    keyword = st.text_input("Enter the exact company name, ticker, or gvkey", value="", placeholder="e.g. 001000")

    selected_gvkey = None
    selected_tic = None
    selected_company_name = None

    if keyword:
        with st.spinner("Searching..."):
            results = search_companies(keyword)

        st.write(f"**Number of matched rows: {len(results)}**")

        if results.empty:
            st.warning("No matching company found")
        else:
            st.dataframe(results, use_container_width=True)

            display_list = results["display"].tolist()
            chosen = st.selectbox("Select a company", display_list)
            idx = display_list.index(chosen)

            selected_gvkey = results.iloc[idx]["gvkey"]
            selected_tic = results.iloc[idx]["tic"]
            selected_company_name = results.iloc[idx]["conm"]

            st.success(f"Selected: {selected_tic} — {selected_company_name} ({selected_gvkey})")
            st.code(f"gvkey = {selected_gvkey}")

    st.markdown("#### Step 4: Select a time range")
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start year", min_value=1950, max_value=2030, value=2010)
    with col2:
        end_year = st.number_input("End year", min_value=1950, max_value=2030, value=2023)

    if st.button("🔍 Query"):
        if selected_gvkey is None:
            st.warning("Please search for and select a company first.")
        elif start_year > end_year:
            st.warning("Start year cannot be greater than end year.")
        else:
            with st.spinner(f"Querying financial data for {selected_tic}..."):
                query_fields = list(ALL_FIELDS)
                df = query_financial_data(selected_gvkey, start_year, end_year, query_fields)

            if df is not None and not df.empty:
                df = add_derived_fields(df)

                st.success(f"✅ Successfully retrieved {len(df)} years of data")
                st.write(f"Company: {selected_tic} — {selected_company_name} ({selected_gvkey})")

                if field in df.columns:
                    show_metric_cards(df, field)
                    show_charts(df, field, display_name, selected_company_name)

                    st.subheader("📄 Raw Data")
                    show_cols = ["year", "gvkey", "tic", "company_name", field]
                    show_cols = [c for c in show_cols if c in df.columns]
                    st.dataframe(df[show_cols], use_container_width=True)
                    show_download(df[show_cols], f"{selected_tic}_{field}.csv")
                else:
                    st.error(f"Field {field} is not included in the result.")
            else:
                st.warning("No data found. Please try another company or time range.")

# ============================================================
# 15. Financial Ratio Analysis
# ============================================================
elif page == "📐 Financial Ratio Analysis":
    st.subheader("📐 Financial Ratio Analysis")

    keyword = st.text_input("Enter the exact company name, ticker, or gvkey", value="", placeholder="e.g. 001000")

    selected_gvkey = None
    selected_tic = None
    selected_company_name = None

    if keyword:
        with st.spinner("Searching..."):
            results = search_companies(keyword)

        st.write(f"**Number of matched rows: {len(results)}**")

        if results.empty:
            st.warning("No matching company found")
        else:
            st.dataframe(results, use_container_width=True)

            display_list = results["display"].tolist()
            chosen = st.selectbox("Select a company", display_list, key="ratio_company")
            idx = display_list.index(chosen)

            selected_gvkey = results.iloc[idx]["gvkey"]
            selected_tic = results.iloc[idx]["tic"]
            selected_company_name = results.iloc[idx]["conm"]

    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start year", min_value=1950, max_value=2030, value=2010, key="ratio_start")
    with col2:
        end_year = st.number_input("End year", min_value=1950, max_value=2030, value=2023, key="ratio_end")

    if st.button("🔍 Analyze ratios"):
        if selected_gvkey is None:
            st.warning("Please search for and select a company first.")
        elif start_year > end_year:
            st.warning("Start year cannot be greater than end year.")
        else:
            query_fields = list(ALL_FIELDS)
            df = query_financial_data(selected_gvkey, start_year, end_year, query_fields)

            if df is not None and not df.empty:
                df = add_derived_fields(df)
                st.success(f"✅ Successfully retrieved {len(df)} years of data")
                st.write(f"Company: {selected_tic} — {selected_company_name} ({selected_gvkey})")

                ratio_cols = ["year", "gvkey", "tic", "company_name", "roa", "roe", "gross_margin",
                              "net_margin", "current_ratio", "asset_turnover"]
                available_cols = [c for c in ratio_cols if c in df.columns]

                st.dataframe(df[available_cols], use_container_width=True)
                show_download(df[available_cols], f"{selected_tic}_ratios.csv")
            else:
                st.warning("No data found")

# ============================================================
# 16. Multi-company Comparison
# ============================================================
elif page == "📊 Multi-company Comparison":
    st.subheader("📊 Multi-company Comparison")

    indicator_all = {}
    for cat in INDICATOR_CATEGORIES.values():
        indicator_all.update(cat)

    display_name = st.selectbox("Select an indicator to compare", list(indicator_all.keys()))
    field = indicator_all[display_name]

    keyword = st.text_input("Search for a company (exact match)", value="", placeholder="e.g. 001000")

    if "compare_companies" not in st.session_state:
        st.session_state.compare_companies = []

    if keyword:
        results = search_companies(keyword)
        st.write(f"**Number of matched rows: {len(results)}**")

        if results.empty:
            st.warning("No matching company found")
        else:
            st.dataframe(results, use_container_width=True)

            display_list = results["display"].tolist()
            chosen = st.selectbox("Select a company to add", display_list)
            idx = display_list.index(chosen)

            selected_gvkey = results.iloc[idx]["gvkey"]
            selected_tic = results.iloc[idx]["tic"]
            selected_name = results.iloc[idx]["conm"]

            if st.button("➕ Add this company"):
                if selected_gvkey not in [x["gvkey"] for x in st.session_state.compare_companies]:
                    st.session_state.compare_companies.append({
                        "gvkey": selected_gvkey,
                        "tic": selected_tic,
                        "conm": selected_name
                    })
                    st.success(f"Added {selected_tic} — {selected_name} ({selected_gvkey})")

    if st.session_state.compare_companies:
        st.write("**Selected companies:**")
        for i, c in enumerate(st.session_state.compare_companies):
            st.write(f"{i+1}. {c['tic']} — {c['conm']} ({c['gvkey']})")

    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start year", min_value=1950, max_value=2030, value=2010, key="compare_start")
    with col2:
        end_year = st.number_input("End year", min_value=1950, max_value=2030, value=2023, key="compare_end")

    if st.button("🔍 Start comparison"):
        if len(st.session_state.compare_companies) < 2:
            st.warning("Please add at least 2 companies.")
        elif start_year > end_year:
            st.warning("Start year cannot be greater than end year.")
        else:
            all_data = []

            for c in st.session_state.compare_companies:
                df = query_financial_data(c["gvkey"], start_year, end_year, [field])
                if df is not None and not df.empty:
                    all_data.append(df)

            if all_data:
                combined = pd.concat(all_data, ignore_index=True).dropna(subset=[field])

                fig = px.line(
                    combined,
                    x="year",
                    y=field,
                    color="company_name",
                    markers=True,
                    title=f"{display_name} — Multi-company Comparison"
                )
                fig.update_layout(template="plotly_white", height=500)
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(combined, use_container_width=True)
                show_download(combined, "multi_company_compare.csv")
            else:
                st.warning("No company data found")

# ============================================================
# 17. Footer
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #999; font-size: 0.85rem;">
        TCY Data Analysis Assistant | Built with Python, Streamlit & WRDS<br>
        Data Source: Compustat `comp.funda` | Search: exact match by gvkey / conm / tic
    </div>
    """,
    unsafe_allow_html=True
)