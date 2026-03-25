# config.py — Central configuration for the entire pipeline
# Edit this file before running anything else.

# ─────────────────────────────────────────
# PostgreSQL Connection
# ─────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "tech_skills_db",
    "user": "postgres",        
    "password": "admin123", 
}

# ─────────────────────────────────────────
# LinkedIn Authentication
# Get this from Chrome DevTools → Application → Cookies → www.linkedin.com
# Copy the value of the "li_at" cookie
# ─────────────────────────────────────────
LINKEDIN_LI_AT_COOKIE = "AQEDAUXzOpcDcJmwAAABnSWM4d4AAAGdSZll3k4As_iTDoVUx74EblZkNObe6AXtkkeGM5mG7YVQZ9LhgHhmEUcd7ORiVyuF_J-2MhKWLzKhtgcaCamfYDouyKnnHuCFf6mL9RDPB4d_hMlMSMLf3xYH"  

# ─────────────────────────────────────────
# Job Search Parameters
# ─────────────────────────────────────────
SEARCH_QUERIES = [
    "AI Engineer",
    "Machine Learning Engineer",
    "MLOps Engineer",
    "Data Engineer",
    "Cloud Engineer",
    "LLM Engineer",
    "GenAI Developer",
]

LOCATIONS = [
    "United States",
    "United Kingdom",
    "Remote",
]

MAX_JOBS_PER_QUERY = 50  # LinkedIn returns max 25 per page, we paginate

# ─────────────────────────────────────────
# Skills Dictionary
# These are the keywords we scan for in job descriptions.
# Add/remove as needed — organized by category.
# ─────────────────────────────────────────
SKILLS = {
    # AI / ML Frameworks
    "AI/ML": [
        "PyTorch", "TensorFlow", "Keras", "scikit-learn", "XGBoost",
        "LightGBM", "Hugging Face", "LangChain", "LlamaIndex",
        "RAG", "fine-tuning", "RLHF", "LoRA", "vLLM",
    ],
    # LLMs & GenAI
    "GenAI": [
        "GPT-4", "Claude", "Gemini", "Llama", "Mistral",
        "OpenAI", "Anthropic", "prompt engineering", "embeddings",
        "vector database", "Pinecone", "Weaviate", "Chroma",
    ],
    # Cloud Platforms
    "Cloud": [
        "AWS", "GCP", "Azure", "SageMaker", "Vertex AI",
        "Bedrock", "Lambda", "S3", "BigQuery", "Databricks",
        "Snowflake", "Redshift",
    ],
    # MLOps & Infrastructure
    "MLOps": [
        "MLflow", "Kubeflow", "Airflow", "Prefect", "Docker",
        "Kubernetes", "Terraform", "CI/CD", "GitHub Actions",
        "FastAPI", "Ray",
    ],
    # Programming Languages
    "Languages": [
        "Python", "SQL", "Scala", "Rust", "Go", "Java", "R",
    ],
    # Data Engineering
    "Data": [
        "Spark", "Kafka", "dbt", "Pandas", "Polars",
        "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
    ],
}

# Flat list of all skills (used by transform.py)
ALL_SKILLS = [skill for skills in SKILLS.values() for skill in skills]

# ─────────────────────────────────────────
# Scraping Settings
# ─────────────────────────────────────────
REQUEST_DELAY_SECONDS = 2   # Be polite — don't hammer LinkedIn
MAX_RETRIES = 3
