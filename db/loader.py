# db/loader.py
# ─────────────────────────────────────────────────────────────────
# LOAD: Inserts transformed jobs into PostgreSQL.
#
# Key design decisions:
#   - Uses psycopg2 (the standard PostgreSQL adapter for Python)
#   - INSERT ... ON CONFLICT DO NOTHING → idempotent (safe to re-run)
#   - Batch inserts with executemany for performance
#   - Context manager pattern for automatic connection cleanup
# ─────────────────────────────────────────────────────────────────

import logging
from contextlib import contextmanager

import psycopg2
import psycopg2.extras  # for execute_values (fast bulk insert)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DB_CONFIG
from etl.transform import TransformedJob

log = logging.getLogger(__name__)


@contextmanager
def get_connection():
    """
    Context manager for PostgreSQL connections.
    Automatically commits on success, rolls back on error, always closes.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(...)
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_job(conn, job: TransformedJob) -> int | None:
    """
    Insert one job into the jobs table.
    Uses ON CONFLICT DO NOTHING to skip duplicates (by linkedin_id).
    Returns the internal job ID (or None if duplicate was skipped).
    """
    sql = """
        INSERT INTO jobs (linkedin_id, title, company, location, description, search_query)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (linkedin_id) DO NOTHING
        RETURNING id
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            job.linkedin_id,
            job.title,
            job.company,
            job.location,
            job.description,
            job.search_query,
        ))
        row = cur.fetchone()
        return row[0] if row else None


def insert_skills(conn, job_id: int, job: TransformedJob) -> int:
    """
    Bulk insert all skill matches for one job.
    Returns count of rows inserted.
    """
    if not job.skills:
        return 0

    rows = [(job_id, s.skill, s.category) for s in job.skills]

    sql = """
        INSERT INTO job_skills (job_id, skill, category)
        VALUES %s
        ON CONFLICT (job_id, skill) DO NOTHING
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
        return cur.rowcount


def load_jobs(jobs: list[TransformedJob]) -> dict:
    """
    Main load function: inserts a batch of TransformedJobs into PostgreSQL.
    Returns a stats dict: {inserted, skipped, skills_added}.
    """
    stats = {"inserted": 0, "skipped": 0, "skills_added": 0}

    with get_connection() as conn:
        for job in jobs:
            job_id = insert_job(conn, job)

            if job_id is None:
                # Duplicate — already in DB
                stats["skipped"] += 1
                log.debug(f"Skipped duplicate: {job.linkedin_id}")
                continue

            skills_added = insert_skills(conn, job_id, job)
            stats["inserted"] += 1
            stats["skills_added"] += skills_added
            log.debug(f"Inserted job {job_id}: {job.title} @ {job.company} ({skills_added} skills)")

    log.info(
        f"Load complete — "
        f"inserted: {stats['inserted']}, "
        f"skipped: {stats['skipped']}, "
        f"skills: {stats['skills_added']}"
    )
    return stats
