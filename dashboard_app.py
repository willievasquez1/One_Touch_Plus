import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
from urllib.parse import urlparse

DB_PATH = "data/crawler.db"

st.set_page_config(page_title="🧠 One_Touch_Plus Dashboard", layout="wide")
st.title("🧠 One_Touch_Plus Crawl Dashboard")
st.markdown("A real-time view into your crawl performance and data volume.")

@st.cache_data(ttl=60)
def load_data(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM scraped_data", conn)
    conn.close()
    return df

def extract_domain(url):
    try:
        return urlparse(url).netloc
    except:
        return "unknown"

# Load crawl data
try:
    df = load_data(DB_PATH)

    # Convert and add datetime column, converting to native datetime
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], format="%Y%m%d_%H%M%S", errors="coerce")
    # Convert pandas Timestamp to native datetime objects if needed
    df["timestamp_dt"] = df["timestamp_dt"].apply(lambda ts: ts.to_pydatetime() if pd.notnull(ts) else None)
    
    df["domain"] = df["url"].apply(extract_domain)

    # Summary Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(df))
    col2.metric("Unique Domains", df["domain"].nunique())

    latest_ts = df["timestamp_dt"].max()
    if latest_ts:
        latest_str = latest_ts.strftime("%B %d, %Y – %I:%M %p")
    else:
        latest_str = "N/A"
    col3.metric("Latest Crawl", latest_str)

    # Sidebar Filters
    st.sidebar.header("🔎 Filters")

    # Domain filter
    unique_domains = sorted(df["domain"].dropna().unique())
    selected_domains = st.sidebar.multiselect("Filter by Domain", unique_domains, default=unique_domains)

    # Time filter: convert min and max to native datetime objects.
    min_time = df["timestamp_dt"].min()
    max_time = df["timestamp_dt"].max()
    if min_time and max_time:
        min_time = min_time.to_pydatetime() if hasattr(min_time, "to_pydatetime") else min_time
        max_time = max_time.to_pydatetime() if hasattr(max_time, "to_pydatetime") else max_time
    else:
        min_time, max_time = datetime.now(), datetime.now()

    time_range = st.sidebar.slider(
        "Filter by Time Range",
        min_value=min_time,
        max_value=max_time,
        value=(min_time, max_time),
        format="MM/DD/YY – %H:%M"
    )

    # Filter dataset
    filtered_df = df[
        df["domain"].isin(selected_domains) &
        df["timestamp_dt"].between(time_range[0], time_range[1])
    ]

    # Charts
    st.subheader("📊 Records per Domain")
    domain_counts = filtered_df["domain"].value_counts()
    st.bar_chart(domain_counts)

    st.subheader("📈 Crawl Timeline")
    timeline = filtered_df.groupby(filtered_df["timestamp_dt"].dt.floor("min")).size()
    st.line_chart(timeline)

    # Search + Raw Data
    st.subheader("🔍 Search URLs")
    search_term = st.text_input("Enter keyword to filter URLs:")
    if search_term:
        filtered_df = filtered_df[filtered_df["url"].str.contains(search_term, case=False, na=False)]

    st.subheader("📄 Raw Records")
    st.dataframe(
        filtered_df[["url", "title", "timestamp_dt", "domain"]].sort_values("timestamp_dt", ascending=False),
        use_container_width=True
    )

    # Export Button
    csv_export = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download filtered results as CSV",
        data=csv_export,
        file_name="filtered_crawl_data.csv",
        mime="text/csv"
    )

except Exception as e:
    st.error(f"⚠️ Failed to load dashboard: {e}")
