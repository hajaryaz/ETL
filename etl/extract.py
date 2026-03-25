
# etl/extract.py
# ─────────────────────────────────────────────────────────────────
# EXTRACT: Scrapes LinkedIn job listings using session cookies.
#
# How LinkedIn's (unofficial) jobs API works:
#   GET https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
#   Parameters: keywords, location, start (pagination offset)
#   Returns: HTML fragments containing job cards
#
# We parse those cards to get job IDs, then hit the job detail
# endpoint to get full descriptions.
# ─────────────────────────────────────────────────────────────────

import time
import logging
from dataclasses import dataclass, field
from typing import Iterator

import requests
from bs4 import BeautifulSoup

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import LINKEDIN_LI_AT_COOKIE, REQUEST_DELAY_SECONDS, MAX_RETRIES, MAX_JOBS_PER_QUERY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


@dataclass
class RawJob:
    """Raw job data straight off LinkedIn — no cleaning yet."""
    linkedin_id: str
    title: str
    company: str
    location: str
    description: str
    search_query: str


class LinkedInScraper:
    """
    Scrapes LinkedIn job listings using your session cookie.

    LinkedIn has two relevant (unofficial) endpoints:
    1. Job search  → returns job cards (IDs + basic info)
    2. Job detail  → returns full description for one job ID
    """

    SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })
        # The li_at cookie authenticates your session
        self.session.cookies.set("li_at", LINKEDIN_LI_AT_COOKIE, domain=".linkedin.com")

    def _get_with_retry(self, url: str, params: dict = None) -> requests.Response | None:
        """GET with exponential backoff retry."""
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(url, params=params, timeout=15)
                if resp.status_code == 429:
                    wait = 2 ** attempt * 10  # 10s, 20s, 40s
                    log.warning(f"Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                log.error(f"Request failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)
        return None

    def _search_page(self, query: str, location: str, start: int) -> list[str]:
        """
        Fetch one page of job search results.
        Returns a list of LinkedIn job IDs found on that page.
        """
        params = {
            "keywords": query,
            "location": location,
            "start": start,        # pagination: 0, 25, 50, ...
            "count": 25,           # LinkedIn max per page
            "f_TPR": "r86400",     # posted in last 24h (optional filter)
        }
        resp = self._get_with_retry(self.SEARCH_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # Each job card has data-entity-urn="urn:li:jobPosting:XXXXXXXXX"
        job_ids = []
        for card in soup.find_all("div", {"data-entity-urn": True}):
            urn = card["data-entity-urn"]
            if "jobPosting" in urn:
                job_id = urn.split(":")[-1]
                job_ids.append(job_id)

        log.info(f"  Page start={start}: found {len(job_ids)} job IDs")
        return job_ids

    def _get_job_detail(self, job_id: str) -> dict | None:
        """
        Fetch full details (title, company, location, description) for one job.
        Returns a dict or None if it fails.
        """
        url = self.DETAIL_URL.format(job_id=job_id)
        resp = self._get_with_retry(url)
        if not resp:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        def text(selector: str) -> str:
            el = soup.select_one(selector)
            return el.get_text(strip=True) if el else ""

        return {
            "linkedin_id": job_id,
            "title":       text("h2.top-card-layout__title"),
            "company":     text("a.topcard__org-name-link") or text("span.topcard__flavor"),
            "location":    text("span.topcard__flavor--bullet"),
            "description": text("div.description__text"),
        }

    def scrape(self, query: str, location: str) -> Iterator[RawJob]:
        """
        Generator: yields RawJob objects for a given search query + location.
        Paginates up to MAX_JOBS_PER_QUERY total results.
        """
        log.info(f"Scraping: '{query}' in '{location}'")
        collected = 0

        for start in range(0, MAX_JOBS_PER_QUERY, 25):
            job_ids = self._search_page(query, location, start)
            if not job_ids:
                break

            for job_id in job_ids:
                detail = self._get_job_detail(job_id)
                if detail and detail["title"]:
                    yield RawJob(**detail, search_query=query)
                    collected += 1

                time.sleep(REQUEST_DELAY_SECONDS)  # be polite

            if len(job_ids) < 25:
                break  # last page

        log.info(f"  ✓ Collected {collected} jobs for '{query}' in '{location}'")
