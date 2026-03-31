# TP-6: Employee Data Pipeline

## Project Structure

```
tp6_employee_etl/
├── docker-compose.yml          ← single file that runs everything
├── requirements-airflow.txt    ← (reference only, auto-installed by compose)
│
├── data/
│   └── employees.csv           ← raw dataset (30 rows, all required columns)
│
├── sql/
│   └── init.sql                ← creates employee_db + employees table (auto-run by MySQL)
│
├── dags/
│   └── employee_etl_dag.py     ← Airflow DAG: extract → transform → validate → load
│
└── streamlit_app/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py                  ← Streamlit UI with filters, charts, table
```

---

## What You Need to Change

| File | What to Change | Default Value |
|------|---------------|---------------|
| `docker-compose.yml` | `MYSQL_ROOT_PASSWORD` | `root_pass` |
| `docker-compose.yml` | `MYSQL_USER` + `MYSQL_PASSWORD` | `etl_user` / `etl_pass` |
| `dags/employee_etl_dag.py` | `DB_CONFIG` user/password | `etl_user` / `etl_pass` |
| `streamlit_app/app.py` | `DB_CONFIG` user/password | `etl_user` / `etl_pass` |

> **Rule:** whatever you set in `docker-compose.yml` for MySQL credentials must match exactly in the DAG and Streamlit files.

---

## Quick Start

```bash
# 1. Go into the project folder
cd tp6_employee_etl

# 2. Start all services (first run takes ~3-5 min to download images)
docker compose up --build -d

# 3. Wait ~60 seconds for airflow-init to finish, then open:
#    Airflow UI  → http://localhost:8080   (admin / admin)
#    Streamlit   → http://localhost:8501
#    MySQL port  → localhost:3307          (use MySQL Workbench)
```

---

## Step-by-Step After Starting

### Step 1 – Connect MySQL Workbench
- Host: `localhost`
- Port: `3307`  ← note: 3307 not 3306
- User: `etl_user`
- Password: `etl_pass`
- Database: `employee_db`

### Step 2 – Run the Airflow DAG
1. Open http://localhost:8080
2. Login: `admin` / `admin`
3. Find DAG **`employee_etl_pipeline`**
4. Toggle it **ON** (blue switch)
5. Click ▶️ **Trigger DAG**
6. Watch: extract → transform → validate → load all turn green

### Step 3 – View the Dashboard
1. Open http://localhost:8501
2. Use sidebar filters: City, Education, Gender, Payment Tier, Salary Range
3. Search box filters City and Education simultaneously
4. Download filtered results as CSV

---

## DAG Tasks Explained

```
extract  →  transform  →  validate  →  load
```

| Task | What it does |
|------|-------------|
| `extract` | Reads `employees.csv`, pushes raw JSON to XCom |
| `transform` | Cleans nulls, fixes types, calculates `final_salary = salary + (salary × bonus% / 100)` |
| `validate` | Checks: no nulls in critical columns, salary > 0, final_salary ≥ salary, valid payment_tier |
| `load` | Truncates + inserts all rows into MySQL `employees` table |

---

## Stopping the Project

```bash
docker compose down          # stop containers, keep data volumes
docker compose down -v       # stop + delete all data (full reset)
```

---

## Note About Separate Projects

This project has its **own `docker-compose.yml`** completely independent from any previous project. Each project in its own folder = no conflicts. If you have another project with ports like `8080` or `8501`, either:
- Stop the other project first: `docker compose down` (in that folder)
- Or change the ports in **this** `docker-compose.yml` (e.g., `8082:8080`, `8502:8501`)
