# etl/transform.py
# ─────────────────────────────────────────────────────────────────
# TRANSFORM: Takes raw job data → extracts & normalizes skill keywords.
#
# The core logic:
#   1. Clean the description text (HTML artifacts, whitespace, etc.)
#   2. Scan the text for each skill in our SKILLS dictionary
#   3. Use word-boundary regex to avoid false positives (e.g. "R" in "React")
#   4. Return a structured TransformedJob with a list of matched skills
# ─────────────────────────────────────────────────────────────────

import re
import logging
from dataclasses import dataclass

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SKILLS
from etl.extract import RawJob

log = logging.getLogger(__name__)


@dataclass
class SkillMatch:
    skill: str
    category: str


@dataclass
class TransformedJob:
    linkedin_id: str
    title: str
    company: str
    location: str
    description: str   # cleaned version
    search_query: str
    skills: list[SkillMatch]


def _clean_text(text: str) -> str:
    """
    Remove HTML artifacts and normalize whitespace.
    LinkedIn descriptions sometimes have leftover &amp; entities etc.
    """
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("\u2019", "'").replace("\u2013", "-").replace("\u2022", "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_skill_patterns() -> dict[str, tuple[re.Pattern, str]]:
    """
    Pre-compile regex patterns for each skill.
    Uses word boundaries (\b) to avoid false matches.

    Special case: short skills like "R", "Go", "AWS" need careful patterns
    so we don't match them inside longer words.
    """
    patterns = {}
    for category, skills in SKILLS.items():
        for skill in skills:
            # Escape special regex chars (e.g. "C++")
            escaped = re.escape(skill)
            # \b is word boundary — prevents "RAG" matching inside "DRAG"
            pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            patterns[skill] = (pattern, category)
    return patterns


# Compile once at module load — not every time transform() is called
_SKILL_PATTERNS = _build_skill_patterns()


def extract_skills(text: str) -> list[SkillMatch]:
    """
    Scan text for all skills in our dictionary.
    Returns a deduplicated list of SkillMatch objects.
    """
    found = {}
    for skill, (pattern, category) in _SKILL_PATTERNS.items():
        if pattern.search(text):
            # Use lowercase as key to deduplicate e.g. "python" vs "Python"
            key = skill.lower()
            if key not in found:
                found[key] = SkillMatch(skill=skill, category=category)

    return list(found.values())


def transform(raw_job: RawJob) -> TransformedJob:
    """
    Transform a single RawJob into a TransformedJob with extracted skills.
    """
    cleaned_desc = _clean_text(raw_job.description)
    # We search the full text: title + description combined
    # (some skills appear in the title, e.g. "Senior PyTorch Engineer")
    full_text = f"{raw_job.title} {raw_job.company} {cleaned_desc}"
    skills = extract_skills(full_text)

    if not skills:
        log.debug(f"No skills found for job: {raw_job.title} @ {raw_job.company}")

    return TransformedJob(
        linkedin_id=raw_job.linkedin_id,
        title=raw_job.title,
        company=raw_job.company,
        location=raw_job.location,
        description=cleaned_desc,
        search_query=raw_job.search_query,
        skills=skills,
    )
