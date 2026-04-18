import streamlit as st
import pandas as pd
import wrds
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# 1. 页面设置
# ============================================================
st.set_page_config(
    page_title="TCY 数据分析助手",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# 2. 样式
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
# 3. WRDS 连接
# ============================================================
@st.cache_resource
def get_conn():
    try:
        conn = wrds.Connection()
        return conn
    except Exception as e:
        st.error(f"WRDS 连接失败：{e}")
        return None

conn = get_conn()
if conn is None:
    st.error("无法连接 WRDS，请检查网络和账号配置。")
    st.stop()

# ============================================================
# 4. 财务指标定义
# ============================================================
INDICATOR_CATEGORIES = {
    "📊 盈利能力 (Profitability)": {
        "Revenue (revt)": "revt",
        "Net Income (ni)": "ni",
        "Gross Profit (gp)": "gp",
        "Operating Income (oiadp)": "oiadp",
        "EBITDA (ebitda)": "ebitda",
        "EPS Basic (epspx)": "epspx",
        "EPS Diluted (epsfi)": "epsfi",
    },
    "💰 资产负债 (Balance Sheet)": {
        "Total Assets (at)": "at",
        "Total Liabilities (lt)": "lt",
        "Common Equity (ceq)": "ceq",
        "Total Debt (dltt)": "dltt",
        "Current Assets (act)": "act",
        "Current Liabilities (lct)": "lct",
        "Inventory (invt)": "invt",
        "Accounts Receivable (rect)": "rect",
    },
    "💵 现金流 (Cash Flow)": {
        "Operating Cash Flow (oancf)": "oancf",
        "Capital Expenditure (capx)": "capx",
        "Cash & Short-Term Inv (che)": "che",
        "Dividends (dvc)": "dvc",
        "Free Cash Flow (derived)": "free_cash_flow",
    },
    "📈 增长与效率 (Growth & Efficiency)": {
        "Revenue (revt)": "revt",
        "Total Assets (at)": "at",
        "R&D Expense (xrd)": "xrd",
        "SG&A Expense (xsga)": "xsga",
        "Employees (emp)": "emp",
        "Depreciation (dp)": "dp",
    },
    "🏦 估值相关 (Valuation)": {
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
# 5. 公司搜索：精确匹配（已替换）
# ============================================================
@st.cache_data(ttl=600)
def search_companies(keyword):
    try:
        kw = keyword.replace("'", "''")  # 转义单引号

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
        st.error(f"搜索失败：{e}")
        return pd.DataFrame()

# ============================================================
# 6. 查询财务数据：用 gvkey
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
        st.error(f"查询失败：{e}")
        return pd.DataFrame()

# ============================================================
# 7. 派生指标
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
# 8. 统计卡片
# ============================================================
def show_metric_cards(df, field):
    if field not in df.columns:
        st.info("该指标没有可用数据")
        return

    values = pd.to_numeric(df[field], errors="coerce").dropna()
    if values.empty:
        st.info("该指标没有可用数据")
        return

    latest = values.iloc[-1]
    earliest = values.iloc[0]
    change = ((latest - earliest) / abs(earliest)) * 100 if earliest != 0 else None

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("最新值", f"{latest:,.2f}")
    with c2:
        st.metric("最大值", f"{values.max():,.2f}")
    with c3:
        st.metric("最小值", f"{values.min():,.2f}")
    with c4:
        st.metric("平均值", f"{values.mean():,.2f}")
    with c5:
        st.metric("累计变化", f"{change:,.1f}%" if change is not None else "N/A")

# ============================================================
# 9. 图表
# ============================================================
def show_charts(df, field, display_name, company_name):
    values = df.dropna(subset=[field]) if field in df.columns else pd.DataFrame()
    if values.empty:
        st.info("没有足够数据生成图表")
        return

    tab1, tab2, tab3 = st.tabs(["📈 折线图", "📊 柱状图", "📉 面积图"])

    with tab1:
        fig = px.line(values, x="year", y=field, markers=True, title=f"{company_name} — {display_name} 趋势")
        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = px.bar(values, x="year", y=field, title=f"{company_name} — {display_name} 柱状图")
        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = px.area(values, x="year", y=field, title=f"{company_name} — {display_name} 面积图")
        fig.update_layout(template="plotly_white", height=450)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 10. 下载
# ============================================================
def show_download(df, filename):
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 下载数据为 CSV", data=csv, file_name=filename, mime="text/csv")

# ============================================================
# 11. 标题
# ============================================================
st.markdown('<p class="main-title">📊 TCY 数据分析助手</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">基于 Compustat 的交互式公司财务数据分析工具</p>', unsafe_allow_html=True)

# ============================================================
# 12. 侧边栏
# ============================================================
with st.sidebar:
    st.header("📂 功能导航")
    page = st.radio("选择板块", ["🏠 主页", "🔍 按指标类别查询", "📐 财务比率分析", "📊 多公司对比"], index=0)
    st.divider()
    st.markdown("### 数据来源")
    st.markdown("Compustat `comp.funda`")
    st.caption("公司搜索和财务查询都基于 `comp.funda`，搜索为精确匹配")

# ============================================================
# 13. 主页
# ============================================================
if page == "🏠 主页":
    st.subheader("欢迎使用 TCY 数据分析助手")
    st.markdown("""
    这是一个基于 **Compustat** 的交互式财务数据分析工具。

    使用方式：
    1. 输入准确的公司名、ticker 或 gvkey
    2. 从搜索结果中选择公司
    3. 选择时间范围
    4. 查看数据和图表
    """)

    st.info("建议输入完整值：例如完整公司名、完整 ticker 或已知 gvkey")

    for cat_name, indicators in INDICATOR_CATEGORIES.items():
        with st.expander(cat_name):
            for display_name in indicators.keys():
                st.write(f"- {display_name}")

# ============================================================
# 14. 按指标类别查询
# ============================================================
elif page == "🔍 按指标类别查询":
    st.subheader("🔍 按指标类别查询")

    category = st.selectbox("Step 1: 选择指标类别", list(INDICATOR_CATEGORIES.keys()))
    indicators = INDICATOR_CATEGORIES[category]

    display_name = st.selectbox("Step 2: 选择具体指标", list(indicators.keys()))
    field = indicators[display_name]

    st.markdown("#### Step 3: 搜索公司")
    keyword = st.text_input("输入准确的公司名称、ticker 或 gvkey", value="", placeholder="例如: 001000")

    selected_gvkey = None
    selected_tic = None
    selected_company_name = None

    if keyword:
        with st.spinner("搜索中..."):
            results = search_companies(keyword)

        st.write(f"**搜索返回行数：{len(results)}**")

        if results.empty:
            st.warning("没有找到匹配的公司")
        else:
            st.dataframe(results, use_container_width=True)

            display_list = results["display"].tolist()
            chosen = st.selectbox("选择公司", display_list)
            idx = display_list.index(chosen)

            selected_gvkey = results.iloc[idx]["gvkey"]
            selected_tic = results.iloc[idx]["tic"]
            selected_company_name = results.iloc[idx]["conm"]

            st.success(f"已选择：{selected_tic} — {selected_company_name} ({selected_gvkey})")
            st.code(f"gvkey = {selected_gvkey}")

    st.markdown("#### Step 4: 选择时间范围")
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("开始年份", min_value=1950, max_value=2030, value=2010)
    with col2:
        end_year = st.number_input("结束年份", min_value=1950, max_value=2030, value=2023)

    if st.button("🔍 查询"):
        if selected_gvkey is None:
            st.warning("请先搜索并选择公司")
        elif start_year > end_year:
            st.warning("开始年份不能大于结束年份")
        else:
            with st.spinner(f"正在查询 {selected_tic} 的财务数据..."):
                query_fields = list(ALL_FIELDS)
                df = query_financial_data(selected_gvkey, start_year, end_year, query_fields)

            if df is not None and not df.empty:
                df = add_derived_fields(df)

                st.success(f"✅ 成功获取 {len(df)} 年数据")
                st.write(f"公司：{selected_tic} — {selected_company_name} ({selected_gvkey})")

                if field in df.columns:
                    show_metric_cards(df, field)
                    show_charts(df, field, display_name, selected_company_name)

                    st.subheader("📄 原始数据")
                    show_cols = ["year", "gvkey", "tic", "company_name", field]
                    show_cols = [c for c in show_cols if c in df.columns]
                    st.dataframe(df[show_cols], use_container_width=True)
                    show_download(df[show_cols], f"{selected_tic}_{field}.csv")
                else:
                    st.error(f"字段 {field} 不在结果中")
            else:
                st.warning("未查到数据，请尝试其他公司或时间范围")

# ============================================================
# 15. 财务比率分析
# ============================================================
elif page == "📐 财务比率分析":
    st.subheader("📐 财务比率分析")

    keyword = st.text_input("输入准确的公司名称、ticker 或 gvkey", value="", placeholder="例如: 001000")

    selected_gvkey = None
    selected_tic = None
    selected_company_name = None

    if keyword:
        with st.spinner("搜索中..."):
            results = search_companies(keyword)

        st.write(f"**搜索返回行数：{len(results)}**")

        if results.empty:
            st.warning("没有找到匹配的公司")
        else:
            st.dataframe(results, use_container_width=True)

            display_list = results["display"].tolist()
            chosen = st.selectbox("选择公司", display_list, key="ratio_company")
            idx = display_list.index(chosen)

            selected_gvkey = results.iloc[idx]["gvkey"]
            selected_tic = results.iloc[idx]["tic"]
            selected_company_name = results.iloc[idx]["conm"]

    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("开始年份", min_value=1950, max_value=2030, value=2010, key="ratio_start")
    with col2:
        end_year = st.number_input("结束年份", min_value=1950, max_value=2030, value=2023, key="ratio_end")

    if st.button("🔍 分析财务比率"):
        if selected_gvkey is None:
            st.warning("请先搜索并选择公司")
        elif start_year > end_year:
            st.warning("开始年份不能大于结束年份")
        else:
            query_fields = list(ALL_FIELDS)
            df = query_financial_data(selected_gvkey, start_year, end_year, query_fields)

            if df is not None and not df.empty:
                df = add_derived_fields(df)
                st.success(f"✅ 成功获取 {len(df)} 年数据")
                st.write(f"公司：{selected_tic} — {selected_company_name} ({selected_gvkey})")

                ratio_cols = ["year", "gvkey", "tic", "company_name", "roa", "roe", "gross_margin",
                              "net_margin", "current_ratio", "asset_turnover"]
                available_cols = [c for c in ratio_cols if c in df.columns]

                st.dataframe(df[available_cols], use_container_width=True)
                show_download(df[available_cols], f"{selected_tic}_ratios.csv")
            else:
                st.warning("未查到数据")

# ============================================================
# 16. 多公司对比
# ============================================================
elif page == "📊 多公司对比":
    st.subheader("📊 多公司对比")

    indicator_all = {}
    for cat in INDICATOR_CATEGORIES.values():
        indicator_all.update(cat)

    display_name = st.selectbox("选择要对比的指标", list(indicator_all.keys()))
    field = indicator_all[display_name]

    keyword = st.text_input("搜索公司（精确匹配）", value="", placeholder="例如: 001000")

    if "compare_companies" not in st.session_state:
        st.session_state.compare_companies = []

    if keyword:
        results = search_companies(keyword)
        st.write(f"**搜索返回行数：{len(results)}**")

        if results.empty:
            st.warning("没有找到匹配公司")
        else:
            st.dataframe(results, use_container_width=True)

            display_list = results["display"].tolist()
            chosen = st.selectbox("选择要添加的公司", display_list)
            idx = display_list.index(chosen)

            selected_gvkey = results.iloc[idx]["gvkey"]
            selected_tic = results.iloc[idx]["tic"]
            selected_name = results.iloc[idx]["conm"]

            if st.button("➕ 添加此公司"):
                if selected_gvkey not in [x["gvkey"] for x in st.session_state.compare_companies]:
                    st.session_state.compare_companies.append({
                        "gvkey": selected_gvkey,
                        "tic": selected_tic,
                        "conm": selected_name
                    })
                    st.success(f"已添加 {selected_tic} — {selected_name} ({selected_gvkey})")

    if st.session_state.compare_companies:
        st.write("**已选公司：**")
        for i, c in enumerate(st.session_state.compare_companies):
            st.write(f"{i+1}. {c['tic']} — {c['conm']} ({c['gvkey']})")

    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("开始年份", min_value=1950, max_value=2030, value=2010, key="compare_start")
    with col2:
        end_year = st.number_input("结束年份", min_value=1950, max_value=2030, value=2023, key="compare_end")

    if st.button("🔍 开始对比"):
        if len(st.session_state.compare_companies) < 2:
            st.warning("请至少添加 2 家公司")
        elif start_year > end_year:
            st.warning("开始年份不能大于结束年份")
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
                    title=f"{display_name} — 多公司对比"
                )
                fig.update_layout(template="plotly_white", height=500)
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(combined, use_container_width=True)
                show_download(combined, "multi_company_compare.csv")
            else:
                st.warning("没有查到任何公司的数据")

# ============================================================
# 17. Footer
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #999; font-size: 0.85rem;">
        TCY 数据调查助手 | Built with Python, Streamlit & WRDS<br>
        Data Source: Compustat `comp.funda` | Search: exact match by gvkey / conm / tic
    </div>
    """,
    unsafe_allow_html=True
)