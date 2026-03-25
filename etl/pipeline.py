# etl/pipeline.py
# ─────────────────────────────────────────────────────────────────
# ORCHESTRATOR: Ties Extract → Transform → Load together.
#
# Run this file to execute the full pipeline:
#   python etl/pipeline.py
#
# Flow:
#   For each (query, location) combination in config:
#     1. Extract: scrape LinkedIn job listings
#     2. Transform: extract skill keywords from each job
#     3. Load: insert into PostgreSQL in batches
# ─────────────────────────────────────────────────────────────────

import logging
import time
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import SEARCH_QUERIES, LOCATIONS
from etl.extract import LinkedInScraper
from etl.transform import transform, TransformedJob
from db.loader import load_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),                    # console
        logging.FileHandler("pipeline.log"),        # file
    ]
)
log = logging.getLogger(__name__)

BATCH_SIZE = 20  # Insert to DB every N jobs (balance memory vs DB round-trips)


def run_pipeline():
    """Full ETL pipeline — runs all query/location combinations."""
    start_time = datetime.now()
    log.info("=" * 60)
    log.info(f"Pipeline started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"Queries: {SEARCH_QUERIES}")
    log.info(f"Locations: {LOCATIONS}")
    log.info("=" * 60)

    scraper = LinkedInScraper()
    total_stats = {"inserted": 0, "skipped": 0, "skills_added": 0}

    for query in SEARCH_QUERIES:
        for location in LOCATIONS:
            log.info(f"\n▶ Processing: '{query}' | '{location}'")
            batch: list[TransformedJob] = []

            # ── EXTRACT + TRANSFORM (streaming) ──────────────────
            for raw_job in scraper.scrape(query, location):
                transformed = transform(raw_job)
                batch.append(transformed)

                # ── LOAD (in batches) ─────────────────────────────
                if len(batch) >= BATCH_SIZE:
                    stats = load_jobs(batch)
                    for k in total_stats:
                        total_stats[k] += stats[k]
                    batch.clear()

            # Flush remaining jobs in the last partial batch
            if batch:
                stats = load_jobs(batch)
                for k in total_stats:
                    total_stats[k] += stats[k]

    # ── Summary ──────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    log.info("\n" + "=" * 60)
    log.info(f"Pipeline complete in {elapsed}s")
    log.info(f"  Jobs inserted : {total_stats['inserted']}")
    log.info(f"  Jobs skipped  : {total_stats['skipped']} (duplicates)")
    log.info(f"  Skills added  : {total_stats['skills_added']}")
    log.info("=" * 60)

    return total_stats


if __name__ == "__main__":
    run_pipeline()
