# Tech Skills Demand Analyzer - ETL Project

## Overview

This ETL (Extract, Transform, Load) pipeline scrapes LinkedIn job listings to analyze which tech skills are most in-demand. It extracts job data, identifies skills like Python, AWS, and PyTorch from job descriptions, and visualizes trends in AI, Cloud, and MLOps roles.

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/0e1b934b-a05d-495c-a01d-fa3e73e61af0" />




## Table of Contents
- [Technologies Used](#technologies-used)
- [Project Details](#project-details)
    - [Part 1: Extract Data](#part-1-extract-data)
    - [Part 2: Transform Data](#part-2-transform-data)
    - [Part 3: Load into PostgreSQL](#part-3-load-into-postgresql)
    - [Part 4: Visualize](#part-4-visualize)
- [Results](#results)
- [Quick Start](#quick-start)

---

## Technologies Used
- **Python** - Core programming language
- **Requests** - LinkedIn API calls
- **BeautifulSoup4** - HTML parsing
- **Pandas** - Data manipulation
- **Regex** - Skill pattern matching
- **PostgreSQL** - Data storage
- **psycopg2** - PostgreSQL adapter
- **Matplotlib** - Data visualization

---

## Project Details

### Part 1: Extract Data (Web Scraping)
The pipeline uses `Requests` and `BeautifulSoup` to scrape LinkedIn job listings. It authenticates using your LinkedIn cookie (`li_at`) and fetches job details for multiple titles:
- AI Engineer
- Machine Learning Engineer
- MLOps Engineer
- Data Engineer
- Cloud Engineer
- LLM Engineer
- GenAI Developer

Jobs are scraped from 3 locations: United States, United Kingdom, and Remote.

### Part 2: Transform Data (Skill Extraction)
After extraction, job descriptions are cleaned and scanned for 50+ predefined skills using regex patterns. Skills are categorized into:
- **AI/ML**: PyTorch, TensorFlow, scikit-learn
- **GenAI**: GPT-4, LangChain, OpenAI
- **Cloud**: AWS, Azure, GCP, Docker
- **MLOps**: Kubernetes, Airflow, MLflow
- **Data**: Spark, Kafka, Snowflake
- **Languages**: Python, SQL, Java

### Part 3: Load into PostgreSQL
Clean data is loaded into PostgreSQL using `psycopg2` with:
- **ON CONFLICT** handling to prevent duplicates
- **Bulk inserts** for performance
- **Foreign key relationships** between jobs and skills

### Part 4: Visualize
The dashboard generates 4 charts using `Matplotlib`:
1. **Top 20 Skills** - Horizontal bar chart
2. **Skill Categories** - Donut chart
3. **Skills per Category** - Grouped bar chart
4. **Skills by Job Query** - Heatmap

---

## Results
<img width="1916" height="1079" alt="image" src="https://github.com/user-attachments/assets/e7f4f0f3-d3bb-44c0-bc38-a18e531670c2" />


## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `config.py`
```python
# Add your PostgreSQL password
DB_CONFIG = {
    "password": "your_password"
}

# Add your LinkedIn cookie
LINKEDIN_LI_AT_COOKIE = "your_li_at_cookie"
```
*How to get cookie: LinkedIn → F12 → Application → Cookies → li_at*

### 3. Create Database
```sql
-- Run in pgAdmin or terminal
psql -d tech_skills_db -f db/schema.sql
```

### 4. Run Pipeline
```bash
# Extract, Transform, Load
python etl/pipeline.py

# Generate dashboard
python visualizations/dashboard.py
```

### 5. View Results
- Dashboard saved to: `data/dashboard.png`
- Check your PostgreSQL database for raw data

---

## Project Structure

```
├── etl/
│   ├── extract.py      # LinkedIn scraper
│   ├── transform.py    # Skill extraction logic
│   └── pipeline.py     # Main ETL orchestrator
├── db/
│   ├── schema.sql      # Database tables
│   └── loader.py       # PostgreSQL loader
├── visualizations/
│   └── dashboard.py    # Chart generator
├── data/               # Output dashboard images
├── config.py           # Configuration file
└── requirements.txt    # Python dependencies
```

---

## Customization

**Add New Skills:**
```python
SKILLS = {
    "Category": ["Skill1", "Skill2"]
}
```

**Add Job Titles:**
```python
SEARCH_QUERIES = ["New Job Title"]
```

**Add Locations:**
```python
LOCATIONS = ["New Location"]
```

---

## Troubleshooting


| Problem | Fix |
|---------|-----|
| LinkedIn cookie expired | Get new one: dev tools → Application → Cookies → li_at |
| Database connection | Open pgAdmin, start PostgreSQL server |
| No jobs found | Verify cookie is correct in config.py ||

---

This project demonstrates a complete ETL pipeline from web scraping to visualization, with practical applications in job market analysis and skills tracking.
