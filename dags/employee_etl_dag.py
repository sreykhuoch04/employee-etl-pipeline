# dags/employee_etl_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import mysql.connector
import logging

# ──────────────────────────────────────────────
# Default DAG arguments
# ──────────────────────────────────────────────
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# MySQL connection config  ← change if needed
DB_CONFIG = {
    "host": "mysql",        # service name in docker-compose
    "port": 3306,
    "user": "etl_user",
    "password": "etl_pass",
    "database": "employee_db",
}

CSV_PATH = "/opt/airflow/data/employees.csv"


# ──────────────────────────────────────────────
# TASK 1 – EXTRACT
# ──────────────────────────────────────────────
def extract(**context):
    """Read raw CSV and push to XCom."""
    logging.info(f"Reading CSV from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    logging.info(f"Extracted {len(df)} rows, columns: {list(df.columns)}")
    context["ti"].xcom_push(key="raw_data", value=df.to_json(orient="records"))


# Salary base by PaymentTier
SALARY_MAP = {1: 30_000, 2: 55_000, 3: 85_000}
# Bonus base by Education
BONUS_BASE = {"Bachelors": 0.05, "Masters": 0.10, "Phd": 0.15}


# ──────────────────────────────────────────────
# TASK 2 – TRANSFORM
# ──────────────────────────────────────────────
def transform(**context):
    """
    Clean data, generate salary + bonus_percentage from PaymentTier/Education,
    then calculate final_salary = salary + (salary * bonus_percentage).
    Keeps original column names (Education, City, PaymentTier, etc.)
    """
    raw_json = context["ti"].xcom_pull(key="raw_data", task_ids="extract")
    df = pd.read_json(raw_json, orient="records")

    logging.info(f"[TRANSFORM] Shape before cleaning: {df.shape}")

    # ── 1. Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    logging.info(f"[TRANSFORM] Removed {before - len(df)} duplicate rows")

    # ── 2. Drop rows with any null values
    before = len(df)
    df = df.dropna()
    logging.info(f"[TRANSFORM] Removed {before - len(df)} null rows")

    # ── 3. Standardise categorical text
    df["Education"]   = df["Education"].str.strip().str.title()
    df["City"]        = df["City"].str.strip()
    df["Gender"]      = df["Gender"].str.strip().str.capitalize()
    df["EverBenched"] = df["EverBenched"].str.strip().str.capitalize()

    # ── 4. Type coercion
    df["Age"]                       = pd.to_numeric(df["Age"], errors="coerce").fillna(0).astype(int)
    df["JoiningYear"]               = pd.to_numeric(df["JoiningYear"], errors="coerce").fillna(0).astype(int)
    df["PaymentTier"]               = pd.to_numeric(df["PaymentTier"], errors="coerce").fillna(1).astype(int)
    df["ExperienceInCurrentDomain"] = pd.to_numeric(df["ExperienceInCurrentDomain"], errors="coerce").fillna(0).astype(int)
    df["LeaveOrNot"]                = pd.to_numeric(df["LeaveOrNot"], errors="coerce").fillna(0).astype(int)

    # ── 5. Validate ranges
    df = df[df["Age"].between(18, 65)]
    df = df[df["PaymentTier"].isin([1, 2, 3])]
    df = df[df["JoiningYear"].between(2000, 2025)]
    logging.info(f"[TRANSFORM] After range validation: {len(df)} rows")

    # ── 6. Generate salary from PaymentTier (±10% variation)
    def gen_salary(row):
        base = SALARY_MAP.get(row["PaymentTier"], 55_000)
        np.random.seed(int(row.name) % 999)
        variation = np.random.uniform(-0.10, 0.10)
        return round(base * (1 + variation), 2)

    # ── 7. Generate bonus_percentage from Education + Experience
    def gen_bonus(row):
        base = BONUS_BASE.get(row["Education"], 0.05)
        exp_boost = row["ExperienceInCurrentDomain"] * 0.005  # +0.5% per year
        return round(base + exp_boost, 4)

    df["salary"]           = df.apply(gen_salary, axis=1)
    df["bonus_percentage"] = df.apply(gen_bonus, axis=1)

    # ── 8. Calculate final_salary
    df["final_salary"] = df["salary"] + (df["salary"] * df["bonus_percentage"])
    df["final_salary"] = df["final_salary"].round(2)

    # ── 9. Helper columns
    df["years_at_company"] = 2024 - df["JoiningYear"]
    df["seniority"]        = df["PaymentTier"].map({1: "Junior", 2: "Mid", 3: "Senior"})

    logging.info(f"[TRANSFORM] Finished. Shape: {df.shape}")
    logging.info(f"[TRANSFORM] Sample:\n{df[['Education','PaymentTier','salary','bonus_percentage','final_salary']].head()}")

    context["ti"].xcom_push(key="clean_data", value=df.to_json(orient="records"))


# ──────────────────────────────────────────────
# TASK 3 – VALIDATE
# ──────────────────────────────────────────────
def validate(**context):
    """Data quality gate — raises ValueError if any check fails."""
    clean_json = context["ti"].xcom_pull(key="clean_data", task_ids="transform")
    df = pd.read_json(clean_json, orient="records")

    errors = []

    # Check 1 – no nulls in critical columns
    critical_cols = ["salary", "bonus_percentage", "final_salary",
                     "Age", "Education", "City", "PaymentTier"]
    for col in critical_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            errors.append(f"NULL values in '{col}': {null_count} rows")

    # Check 2 – salary > 0
    neg = (df["salary"] <= 0).sum()
    if neg > 0:
        errors.append(f"Non-positive salary in {neg} rows")

    # Check 3 – final_salary >= salary
    bad = (df["final_salary"] < df["salary"]).sum()
    if bad > 0:
        errors.append(f"final_salary < salary in {bad} rows")

    # Check 4 – valid PaymentTier
    invalid_tier = (~df["PaymentTier"].isin([1, 2, 3])).sum()
    if invalid_tier > 0:
        errors.append(f"Invalid PaymentTier in {invalid_tier} rows")

    # Check 5 – minimum row count
    if len(df) < 5:
        errors.append(f"Too few rows after cleaning: {len(df)}")

    if errors:
        raise ValueError("❌ Validation failed:\n" + "\n".join(errors))

    logging.info(f"✅ Validation passed — {len(df)} rows ready to load.")


# ──────────────────────────────────────────────
# TASK 4 – LOAD
# ──────────────────────────────────────────────
def load(**context):
    """Insert cleaned rows into MySQL employees table."""
    clean_json = context["ti"].xcom_pull(key="clean_data", task_ids="transform")
    df = pd.read_json(clean_json, orient="records")

    conn   = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Truncate for idempotent re-runs
    cursor.execute("TRUNCATE TABLE employees")

    insert_sql = """
        INSERT INTO employees (
            education, joining_year, city, payment_tier, age, gender,
            ever_benched, experience_in_current_domain, leave_or_not,
            salary, bonus_percentage, final_salary,
            years_at_company, seniority
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    rows = [
        (
            row["Education"],
            int(row["JoiningYear"]),
            row["City"],
            int(row["PaymentTier"]),
            int(row["Age"]),
            row["Gender"],
            row["EverBenched"],
            int(row["ExperienceInCurrentDomain"]),
            int(row["LeaveOrNot"]),
            float(row["salary"]),
            float(row["bonus_percentage"]),
            float(row["final_salary"]),
            int(row["years_at_company"]),
            row["seniority"],
        )
        for _, row in df.iterrows()
    ]

    cursor.executemany(insert_sql, rows)
    conn.commit()
    logging.info(f"✅ Loaded {cursor.rowcount} rows into MySQL.")
    cursor.close()
    conn.close()


# ──────────────────────────────────────────────
# DAG DEFINITION
# ──────────────────────────────────────────────
with DAG(
    dag_id="employee_etl_pipeline",
    default_args=default_args,
    description="Employee ETL: Extract → Transform → Validate → Load",
    schedule_interval="@daily",
    catchup=False,
    tags=["etl", "employee"],
) as dag:

    t_extract = PythonOperator(
        task_id="extract",
        python_callable=extract,
    )

    t_transform = PythonOperator(
        task_id="transform",
        python_callable=transform,
    )

    t_validate = PythonOperator(
        task_id="validate",
        python_callable=validate,
    )

    t_load = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    # Pipeline order
    t_extract >> t_transform >> t_validate >> t_load