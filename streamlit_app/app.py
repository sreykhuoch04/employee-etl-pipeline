# streamlit_app/app.py

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px

# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Employee ETL Dashboard",
    page_icon="👥",
    layout="wide",
)

st.title("👥 Employee Data Pipeline Dashboard")
st.caption("TP-6 | ETL Pipeline with Airflow + MySQL + Streamlit")

# ──────────────────────────────────────────────
# DB connection  ← change host/user/password here
# ──────────────────────────────────────────────
DB_CONFIG = {
    "host": "mysql",        # docker-compose service name
    "port": 3306,
    "user": "etl_user",
    "password": "etl_pass",
    "database": "employee_db",
}


@st.cache_data(ttl=30)
def load_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        df = pd.read_sql("SELECT * FROM employees", conn)
        conn.close()
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


df, err = load_data()

if err:
    st.error(f"❌ Could not connect to MySQL: {err}")
    st.info("Make sure the Airflow DAG has run at least once to populate the table.")
    st.stop()

if df.empty:
    st.warning("No data found. Trigger the Airflow DAG first.")
    st.stop()

# ──────────────────────────────────────────────
# Sidebar – Filters
# ──────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

# Search box
search = st.sidebar.text_input("Search by City or Education", "")

# City filter
cities = ["All"] + sorted(df["city"].dropna().unique().tolist())
selected_city = st.sidebar.selectbox("City", cities)

# Education filter
educations = ["All"] + sorted(df["education"].dropna().unique().tolist())
selected_edu = st.sidebar.selectbox("Education Level", educations)

# Gender filter
genders = ["All"] + sorted(df["gender"].dropna().unique().tolist())
selected_gender = st.sidebar.selectbox("Gender", genders)

# Payment Tier filter
tiers = ["All"] + sorted(df["payment_tier"].dropna().unique().tolist())
selected_tier = st.sidebar.selectbox("Payment Tier", tiers)

# Salary range
min_sal = int(df["salary"].min())
max_sal = int(df["salary"].max())
salary_range = st.sidebar.slider("Salary Range", min_sal, max_sal, (min_sal, max_sal))

# ──────────────────────────────────────────────
# Apply Filters
# ──────────────────────────────────────────────
filtered = df.copy()

if search:
    mask = (
        filtered["city"].str.contains(search, case=False, na=False) |
        filtered["education"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]

if selected_city != "All":
    filtered = filtered[filtered["city"] == selected_city]

if selected_edu != "All":
    filtered = filtered[filtered["education"] == selected_edu]

if selected_gender != "All":
    filtered = filtered[filtered["gender"] == selected_gender]

if selected_tier != "All":
    filtered = filtered[filtered["payment_tier"] == selected_tier]

filtered = filtered[
    (filtered["salary"] >= salary_range[0]) & (filtered["salary"] <= salary_range[1])
]

# ──────────────────────────────────────────────
# KPI Cards
# ──────────────────────────────────────────────
st.subheader("📊 Summary Metrics")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Employees", len(filtered))
k2.metric("Avg Salary", f"${filtered['salary'].mean():,.0f}" if not filtered.empty else "—")
k3.metric("Avg Final Salary", f"${filtered['final_salary'].mean():,.0f}" if not filtered.empty else "—")
k4.metric("Likely to Leave", int(filtered["leave_or_not"].sum()) if not filtered.empty else 0)

st.divider()

# ──────────────────────────────────────────────
# Charts
# ──────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Final Salary by Education")
    if not filtered.empty:
        fig = px.box(
            filtered, x="education", y="final_salary",
            color="education",
            labels={"final_salary": "Final Salary ($)", "education": "Education"},
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🏙️ Employees by City")
    if not filtered.empty:
        city_counts = filtered["city"].value_counts().reset_index()
        city_counts.columns = ["City", "Count"]
        fig2 = px.bar(city_counts, x="City", y="Count", color="City")
        st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("⚖️ Gender Distribution")
    if not filtered.empty:
        fig3 = px.pie(filtered, names="gender", title="Gender Split")
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("📈 Salary vs Experience")
    if not filtered.empty:
        fig4 = px.scatter(
            filtered, x="experience_in_current_domain", y="final_salary",
            color="education", size="age",
            labels={
                "experience_in_current_domain": "Experience (years)",
                "final_salary": "Final Salary ($)",
            },
        )
        st.plotly_chart(fig4, use_container_width=True)

# ──────────────────────────────────────────────
# Data Table
# ──────────────────────────────────────────────
st.divider()
st.subheader("📋 Employee Records")
st.write(f"Showing **{len(filtered)}** of **{len(df)}** records")

display_cols = [
    "id", "education", "joining_year", "city", "payment_tier",
    "age", "gender", "ever_benched", "experience_in_current_domain",
    "leave_or_not", "salary", "bonus_percentage", "final_salary",
]
st.dataframe(
    filtered[display_cols].reset_index(drop=True),
    use_container_width=True,
    height=400,
)

# Download button
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Filtered CSV",
    data=csv,
    file_name="filtered_employees.csv",
    mime="text/csv",
)
