"""
=========================================================
Aid Axis - Cognitive Progression Analytics Service

Provides longitudinal analysis, consecutive score comparisons,
domain-level variance tracking, and cautious, non-diagnostic
clinical narrative generation.

CLINICAL SAFETY PRINCIPLES:
1. No unsupported claims of disease progression or diagnosis.
2. Neutral, descriptive, objective language.
3. Explicit acknowledgment of confounding factors (fatigue,
   stress, medications, acute illness, test variance).
=========================================================
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """
    Safely parses an ISO date/timestamp string into a datetime object.
    """
    if not date_str:
        return None
    try:
        # Handle trailing Z or timezone offsets
        clean_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_str)
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except Exception:
            return None


def compare_consecutive_assessments(
    latest: Dict[str, Any],
    previous: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compares two consecutive assessments to compute absolute change,
    domain-level deltas, and days elapsed between tests.
    """
    latest_score = float(latest.get("total_score", 0.0))
    prev_score = float(previous.get("total_score", 0.0))
    max_score = float(latest.get("max_score", 30.0))
    
    score_diff = round(latest_score - prev_score, 1)
    abs_score_diff = abs(score_diff)
    
    # Date comparison
    date_latest = parse_iso_date(latest.get("assessment_date", ""))
    date_prev = parse_iso_date(previous.get("assessment_date", ""))
    days_elapsed = None
    if date_latest and date_prev:
        days_elapsed = abs((date_latest - date_prev).days)

    # Domain level shifts
    latest_domains = latest.get("domain_scores", {})
    prev_domains = previous.get("domain_scores", {})
    
    domain_deltas = {}
    for dom_id, dom_data in latest_domains.items():
        curr_score = float(dom_data.get("score", 0.0))
        prev_data = prev_domains.get(dom_id, {})
        old_score = float(prev_data.get("score", 0.0)) if prev_data else 0.0
        d_diff = round(curr_score - old_score, 1)
        domain_deltas[dom_id] = {
            "title": dom_data.get("title", dom_id),
            "current_score": curr_score,
            "previous_score": old_score,
            "max_score": dom_data.get("max_score", 0.0),
            "delta": d_diff,
            "status": "stable" if d_diff == 0 else ("higher" if d_diff > 0 else "lower")
        }

    return {
        "latest_score": latest_score,
        "previous_score": prev_score,
        "max_score": max_score,
        "score_diff": score_diff,
        "abs_score_diff": abs_score_diff,
        "days_elapsed": days_elapsed,
        "latest_date": latest.get("assessment_date", ""),
        "previous_date": previous.get("assessment_date", ""),
        "domain_deltas": domain_deltas,
        "is_comparable": latest.get("assessment_type") == previous.get("assessment_type")
    }


def generate_progression_narrative(
    comparison: Optional[Dict[str, Any]],
    total_assessments: int
) -> str:
    """
    Generates a neutral, clinically prudent descriptive narrative
    summarizing recorded score changes.
    """
    if total_assessments == 0:
        return "No cognitive assessments have been recorded yet. Complete an initial assessment to establish a baseline."
        
    if total_assessments == 1:
        return (
            "An initial baseline assessment has been recorded. "
            "A second comparable assessment is required before longitudinal trends "
            "or consecutive changes can be calculated."
        )

    if not comparison:
        return "Insufficient consecutive data available to generate a progression analysis."

    latest = comparison["latest_score"]
    prev = comparison["previous_score"]
    diff = comparison["score_diff"]
    days = comparison.get("days_elapsed")
    
    time_phrase = f" over an interval of {days} days" if days is not None else ""

    if diff == 0.0:
        summary = f"The latest recorded score ({latest:.1f}/{comparison['max_score']:.0f}) is identical to the previous assessment ({prev:.1f}/{comparison['max_score']:.0f}){time_phrase}, reflecting stable short-term performance."
    elif diff > 0.0:
        summary = f"The latest recorded score ({latest:.1f}/{comparison['max_score']:.0f}) is {diff:.1f} points higher than the previous assessment ({prev:.1f}/{comparison['max_score']:.0f}){time_phrase}."
    else:
        summary = f"The latest recorded score ({latest:.1f}/{comparison['max_score']:.0f}) is {abs(diff):.1f} points lower than the previous assessment ({prev:.1f}/{comparison['max_score']:.0f}){time_phrase}."

    # Identify notable domain fluctuations
    notable_lower = []
    notable_higher = []
    for d in comparison.get("domain_deltas", {}).values():
        if d["delta"] <= -1.0:
            notable_lower.append(d["title"])
        elif d["delta"] >= 1.0:
            notable_higher.append(d["title"])

    nuance = []
    if notable_lower:
        nuance.append(f"Recorded lower values were noted in: {', '.join(notable_lower)}.")
    if notable_higher:
        nuance.append(f"Recorded higher values were noted in: {', '.join(notable_higher)}.")

    nuance_str = " " + " ".join(nuance) if nuance else " Domain sub-scores remained largely consistent."

    context = (
        " Note: Minor score fluctuations are common and can be influenced by transient factors "
        "including fatigue, medication changes, acute stress, testing environment, or sleep quality. "
        "This prototype does not provide clinical diagnosis or prognosis."
    )

    return summary + nuance_str + context


def compute_aggregate_overview(assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes summary overview statistics for the patient dashboard.
    """
    count = len(assessments)
    if count == 0:
        return {
            "has_data": False,
            "count": 0,
            "latest_score": None,
            "latest_date": None,
            "prev_score": None,
            "score_change": None,
            "domains_assessed": 0,
            "comparison": None
        }

    # Assessments are assumed chronological ASC
    latest = assessments[-1]
    latest_score = float(latest.get("total_score", 0.0))
    latest_date = latest.get("assessment_date", "")
    domains_count = len(latest.get("domain_scores", {}))

    if count == 1:
        return {
            "has_data": True,
            "count": 1,
            "latest_score": latest_score,
            "latest_date": latest_date,
            "prev_score": None,
            "score_change": None,
            "domains_assessed": domains_count,
            "comparison": None
        }

    previous = assessments[-2]
    comparison = compare_consecutive_assessments(latest, previous)

    return {
        "has_data": True,
        "count": count,
        "latest_score": latest_score,
        "latest_date": latest_date,
        "prev_score": comparison["previous_score"],
        "score_change": comparison["score_diff"],
        "domains_assessed": domains_count,
        "comparison": comparison
    }
