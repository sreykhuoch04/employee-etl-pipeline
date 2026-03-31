# Employee ETL Pipeline

End-to-end data pipeline for processing employee data using Apache Airflow, Docker, MySQL, and Streamlit.

---

## 📌 Overview

This project demonstrates a complete ETL (Extract, Transform, Load) pipeline for employee data.
The system automates data ingestion, transformation, validation, and storage, and provides an interactive dashboard for data visualization.

## 📸 Screenshots

### Airflow Pipeline
![Airflow]()

### 📊 Dashboard UI
![Dashboard](<img width="1280" height="744" alt="image" src="https://github.com/user-attachments/assets/4b2e61a1-8827-4a08-9297-c834aeb9ab76" />)
### 🔄 Pipeline Flow

```
Extract → Transform → Validate → Load
```

---

## 🛠 Tech Stack

* **Python** – data processing and pipeline logic
* **Apache Airflow** – workflow orchestration
* **Docker & Docker Compose** – containerized environment
* **MySQL** – data storage
* **Streamlit** – interactive dashboard

---

## 📁 Project Structure

```
employee-etl-pipeline/
├── docker-compose.yml          # Run all services (Airflow, MySQL, Streamlit)
├── data/
│   └── employees.csv           # Raw dataset
├── sql/
│   └── init.sql                # Database initialization
├── dags/
│   └── employee_etl_dag.py     # Airflow DAG (ETL pipeline)
├── streamlit_app/
│   ├── app.py                  # Dashboard application
│   └── requirements.txt
└── README.md
```

---

## ⚙️ Features

* Automated ETL pipeline using Airflow
* Data cleaning and transformation
* Data validation (null checks, constraints, consistency)
* MySQL database integration
* Interactive dashboard with filters and charts
* Fully containerized using Docker

---

## 🚀 How to Run the Project

### 1. Clone the repository

```bash
git clone https://github.com/sreykhuoch04/employee-etl-pipeline.git
cd employee-etl-pipeline
```

---

### 2. Start all services

```bash
docker compose up --build -d
```

---

### 3. Access services

* **Airflow UI** → http://localhost:8080

  * Username: `admin`
  * Password: `admin`

* **Streamlit Dashboard** → http://localhost:8501

* **MySQL**

  * Host: `localhost`
  * Port: `3307`
  * Database: `employee_db`

---

## ▶️ Running the ETL Pipeline

1. Open Airflow UI
2. Find DAG: `employee_etl_pipeline`
3. Turn it ON
4. Click **Trigger DAG**
5. Monitor tasks:

   * extract
   * transform
   * validate
   * load

---

## 🔍 DAG Tasks Explanation

| Task          | Description                               |
| ------------- | ----------------------------------------- |
| **extract**   | Reads employee data from CSV              |
| **transform** | Cleans data and calculates derived fields |
| **validate**  | Ensures data quality and consistency      |
| **load**      | Inserts processed data into MySQL         |

---

## 📊 Dashboard Features

* Filter by:

  * City
  * Gender
  * Education
  * Payment Tier
  * Salary range
* Search functionality
* Interactive charts
* Export filtered data as CSV

---

## 🧠 Learning Outcomes

* Building end-to-end ETL pipelines
* Workflow orchestration using Airflow
* Data validation and transformation techniques
* Docker-based system deployment
* Data visualization with Streamlit

---

## 🛑 Stopping the Project

```bash
docker compose down
```

To remove all data:

```bash
docker compose down -v
```

---

## 📌 Notes

* Ensure MySQL credentials in `docker-compose.yml` match configuration in DAG and Streamlit files
* Each project should run in its own environment to avoid port conflicts

---

## 👤 Author

**YORY Sreykhuoch**
Data Science Student | ETL & Data Engineering
