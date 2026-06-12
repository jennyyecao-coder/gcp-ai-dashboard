import streamlit as st
import pandas as pd
from google.cloud import bigquery

st.set_page_config(page_title="Online Retail Dashboard", layout="wide", page_icon="🛒")

TABLE = "jennys-first-project.sales_data.online_retail"

@st.cache_data(ttl=600, show_spinner="Loading data from BigQuery...")
def load_data() -> pd.DataFrame:
    client = bigquery.Client(project="jennys-first-project")
    query = f"""
        SELECT
            InvoiceNo,
            StockCode,
            Description,
            Quantity,
            InvoiceDate,
            UnitPrice,
            CustomerID,
            Country
        FROM `{TABLE}`
        WHERE Quantity > 0
          AND UnitPrice > 0
          AND CustomerID IS NOT NULL
    """
    df = client.query(query).to_dataframe()
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    return df


def kpi_row(df: pd.DataFrame):
    total_revenue = df["Revenue"].sum()
    total_orders = df["InvoiceNo"].nunique()
    total_customers = df["CustomerID"].nunique()
    total_products = df["StockCode"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"£{total_revenue:,.0f}")
    c2.metric("Total Orders", f"{total_orders:,}")
    c3.metric("Unique Customers", f"{total_customers:,}")
    c4.metric("Unique Products", f"{total_products:,}")


def customer_tab(df: pd.DataFrame):
    st.subheader("Top Customers by Revenue")
    top_n = st.slider("Number of customers", 5, 30, 10, key="cust_slider")
    top_customers = (
        df.groupby("CustomerID")["Revenue"]
        .sum()
        .nlargest(top_n)
        .reset_index()
        .rename(columns={"Revenue": "Total Revenue (£)"})
    )
    top_customers["CustomerID"] = top_customers["CustomerID"].astype(str)
    st.bar_chart(top_customers.set_index("CustomerID")["Total Revenue (£)"])

    st.subheader("Customer Distribution by Country")
    country_customers = (
        df.groupby("Country")["CustomerID"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"CustomerID": "Unique Customers"})
    )
    top_cc = st.slider("Countries to show", 5, 20, 10, key="cc_slider")
    st.bar_chart(
        country_customers.head(top_cc).set_index("Country")["Unique Customers"]
    )

    st.subheader("Revenue Over Time")
    monthly = (
        df.groupby("YearMonth")["Revenue"].sum().reset_index()
        .rename(columns={"Revenue": "Monthly Revenue (£)"})
        .sort_values("YearMonth")
    )
    st.line_chart(monthly.set_index("YearMonth")["Monthly Revenue (£)"])


def product_tab(df: pd.DataFrame):
    st.subheader("Top Products by Revenue")
    top_n = st.slider("Number of products", 5, 30, 10, key="prod_rev_slider")
    top_rev = (
        df.groupby("Description")["Revenue"]
        .sum()
        .nlargest(top_n)
        .reset_index()
        .rename(columns={"Revenue": "Total Revenue (£)"})
    )
    st.bar_chart(top_rev.set_index("Description")["Total Revenue (£)"])

    st.subheader("Top Products by Units Sold")
    top_qty = (
        df.groupby("Description")["Quantity"]
        .sum()
        .nlargest(top_n)
        .reset_index()
        .rename(columns={"Quantity": "Units Sold"})
    )
    st.bar_chart(top_qty.set_index("Description")["Units Sold"])

    st.subheader("Product Search")
    search = st.text_input("Search product description", "")
    if search:
        results = df[df["Description"].str.contains(search, case=False, na=False)]
        product_summary = (
            results.groupby("Description")
            .agg(
                Revenue=("Revenue", "sum"),
                Units_Sold=("Quantity", "sum"),
                Avg_Price=("UnitPrice", "mean"),
                Orders=("InvoiceNo", "nunique"),
            )
            .sort_values("Revenue", ascending=False)
            .reset_index()
        )
        st.dataframe(product_summary, use_container_width=True)


def market_tab(df: pd.DataFrame):
    st.subheader("Revenue by Country")
    top_n = st.slider("Countries to show", 5, 20, 10, key="mkt_slider")
    country_rev = (
        df.groupby("Country")["Revenue"]
        .sum()
        .nlargest(top_n)
        .reset_index()
        .rename(columns={"Revenue": "Total Revenue (£)"})
    )
    st.bar_chart(country_rev.set_index("Country")["Total Revenue (£)"])

    st.subheader("Orders by Country")
    country_orders = (
        df.groupby("Country")["InvoiceNo"]
        .nunique()
        .nlargest(top_n)
        .reset_index()
        .rename(columns={"InvoiceNo": "Orders"})
    )
    st.bar_chart(country_orders.set_index("Country")["Orders"])

    st.subheader("Average Order Value by Country")
    aov = (
        df.groupby(["Country", "InvoiceNo"])["Revenue"]
        .sum()
        .reset_index()
        .groupby("Country")["Revenue"]
        .mean()
        .nlargest(top_n)
        .reset_index()
        .rename(columns={"Revenue": "Avg Order Value (£)"})
    )
    st.bar_chart(aov.set_index("Country")["Avg Order Value (£)"])

    st.subheader("Country Summary Table")
    country_summary = (
        df.groupby("Country")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
            Units_Sold=("Quantity", "sum"),
        )
        .sort_values("Revenue", ascending=False)
        .reset_index()
    )
    st.dataframe(country_summary, use_container_width=True)


def main():
    st.title("🛒 Online Retail Dashboard")
    st.caption(f"Source: `{TABLE}`")

    try:
        df = load_data()
    except Exception as e:
        st.error(f"Failed to load data from BigQuery: {e}")
        st.info(
            "Make sure you have run `gcloud auth application-default login` "
            "and have access to the BigQuery dataset."
        )
        st.stop()

    # Global date filter
    min_date = df["InvoiceDate"].min().date()
    max_date = df["InvoiceDate"].max().date()
    st.sidebar.header("Filters")
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = date_range
        df = df[
            (df["InvoiceDate"].dt.date >= start)
            & (df["InvoiceDate"].dt.date <= end)
        ]

    countries = sorted(df["Country"].unique())
    selected_countries = st.sidebar.multiselect(
        "Countries", countries, default=[]
    )
    if selected_countries:
        df = df[df["Country"].isin(selected_countries)]

    st.sidebar.markdown("---")
    st.sidebar.metric("Filtered rows", f"{len(df):,}")

    st.markdown("---")
    kpi_row(df)
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["👤 Customer Insights", "📦 Product Insights", "🌍 Market Insights"])
    with tab1:
        customer_tab(df)
    with tab2:
        product_tab(df)
    with tab3:
        market_tab(df)


if __name__ == "__main__":
    main()
