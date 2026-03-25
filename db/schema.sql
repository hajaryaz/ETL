-- db/schema.sql
-- Run this once to set up your PostgreSQL database:
--   psql -d tech_skills_db -f db/schema.sql

-- ─────────────────────────────────────────
-- Jobs table: one row per job listing
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jobs (
    id              SERIAL PRIMARY KEY,
    linkedin_id     TEXT UNIQUE NOT NULL,       -- LinkedIn's own job ID (prevents duplicates)
    title           TEXT NOT NULL,
    company         TEXT,
    location        TEXT,
    description     TEXT,
    search_query    TEXT,                       -- which query found this job
    scraped_at      TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- Skills table: one row per skill mention
-- (a job with 5 skills = 5 rows here)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_skills (
    id          SERIAL PRIMARY KEY,
    job_id      INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    skill       TEXT NOT NULL,
    category    TEXT NOT NULL,                  -- e.g. "Cloud", "AI/ML"
    UNIQUE(job_id, skill)                       -- no duplicate skill per job
);

-- ─────────────────────────────────────────
-- Indexes for fast querying
-- ─────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_job_skills_skill    ON job_skills(skill);
CREATE INDEX IF NOT EXISTS idx_job_skills_category ON job_skills(category);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at     ON jobs(scraped_at);

-- ─────────────────────────────────────────
-- Useful views (pre-built queries)
-- ─────────────────────────────────────────

-- Top skills overall
CREATE OR REPLACE VIEW top_skills AS
SELECT
    skill,
    category,
    COUNT(*) AS mention_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM jobs), 2) AS pct_of_jobs
FROM job_skills
GROUP BY skill, category
ORDER BY mention_count DESC;

-- Top skills per category
CREATE OR REPLACE VIEW top_skills_by_category AS
SELECT
    category,
    skill,
    COUNT(*) AS mention_count
FROM job_skills
GROUP BY category, skill
ORDER BY category, mention_count DESC;

-- Skill trends over time (by day)
CREATE OR REPLACE VIEW skill_trends AS
SELECT
    DATE(j.scraped_at) AS date,
    js.skill,
    js.category,
    COUNT(*) AS mention_count
FROM job_skills js
JOIN jobs j ON j.id = js.job_id
GROUP BY DATE(j.scraped_at), js.skill, js.category
ORDER BY date, mention_count DESC;
