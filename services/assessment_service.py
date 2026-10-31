"""
=========================================================
Aid Axis - Cognitive Assessment Service

Defines the "Cognitive Monitoring Questionnaire — Prototype"
specifications, step definitions, input validation, and
transparent, deterministic scoring calculations.

CLINICAL NOTICE:
This instrument is an original prototype designed for
longitudinal cognitive performance tracking and demonstration.
It is explicitly distinct from copyrighted clinical MMSE / MoCA
examinations and does NOT provide a clinical diagnosis of
Alzheimer's disease or any neurological condition.
=========================================================
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime

# Total Maximum Score
MAX_ASSESSMENT_SCORE = 30.0

# Versioning and Metadata
INSTRUMENT_NAME = "Cognitive Monitoring Questionnaire — Prototype"
INSTRUMENT_VERSION = "v1.0-prototype"

# Domain definitions and weights
DOMAINS = [
    {
        "id": "orientation_time",
        "title": "Orientation: Time",
        "icon": "📅",
        "max_score": 5.0,
        "description": "Assesses awareness of temporal parameters (year, season, month, date, day of week)."
    },
    {
        "id": "orientation_place",
        "title": "Orientation: Place",
        "icon": "📍",
        "max_score": 5.0,
        "description": "Assesses geographical and environmental awareness."
    },
    {
        "id": "registration",
        "title": "Immediate Registration",
        "icon": "🎯",
        "max_score": 3.0,
        "description": "Evaluates working memory encoding of 3 stimulus words (Apple, Table, Penny)."
    },
    {
        "id": "attention",
        "title": "Attention & Calculation",
        "icon": "🔢",
        "max_score": 5.0,
        "description": "Evaluates sustained mental concentration through serial subtraction or backward sequencing."
    },
    {
        "id": "delayed_recall",
        "title": "Delayed Recall",
        "icon": "⏳",
        "max_score": 3.0,
        "description": "Tests short-term retrieval of the 3 previously registered stimulus words."
    },
    {
        "id": "language",
        "title": "Language & Naming",
        "icon": "🗣️",
        "max_score": 4.0,
        "description": "Tests object naming, phrase repetition, and categorical fluency."
    },
    {
        "id": "comprehension",
        "title": "Comprehension & Execution",
        "icon": "📋",
        "max_score": 3.0,
        "description": "Assesses multi-step instruction comprehension and task adherence."
    },
    {
        "id": "visuospatial",
        "title": "Visuospatial & Executive",
        "icon": "📐",
        "max_score": 2.0,
        "description": "Evaluates spatial perception, geometric recognition, and visual clock reasoning."
    }
]

# Registration Words Target
TARGET_REGISTRATION_WORDS = ["apple", "table", "penny"]


def get_current_temporal_reference() -> Dict[str, str]:
    """
    Returns current local temporal components for dynamic scoring validation.
    """
    now = datetime.now()
    month_name = now.strftime("%B").lower()
    day_name = now.strftime("%A").lower()
    year_str = str(now.year)
    day_num = str(now.day)
    
    # Determine season (Northern Hemisphere general convention)
    month = now.month
    if month in (12, 1, 2):
        season = "winter"
    elif month in (3, 4, 5):
        season = "spring"
    elif month in (6, 7, 8):
        season = "summer"
    else:
        season = "autumn"
        
    return {
        "year": year_str,
        "season": season,
        "month": month_name,
        "day_name": day_name,
        "day_num": day_num
    }


def validate_step(step_idx: int, responses: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that required fields for the given assessment step have been supplied.
    Returns (is_valid, error_messages).
    """
    errors = []
    
    if step_idx == 0:  # Orientation to Time
        required = ["time_year", "time_season", "time_month", "time_date", "time_day"]
        for key in required:
            val = responses.get(key)
            if val is None or str(val).strip() == "":
                errors.append(f"Please provide an answer for: {key.replace('time_', '').capitalize()}")
                
    elif step_idx == 1:  # Orientation to Place
        required = ["place_country", "place_state", "place_city", "place_setting", "place_room"]
        for key in required:
            val = responses.get(key)
            if val is None or str(val).strip() == "":
                errors.append(f"Please provide an answer for: {key.replace('place_', '').capitalize()}")
                
    elif step_idx == 2:  # Immediate Registration
        words = responses.get("registration_words", [])
        if not words or len(words) == 0:
            errors.append("Please acknowledge or record the 3 presented words to continue.")
            
    elif step_idx == 3:  # Attention & Calculation
        # Needs either serial subtraction entries or backward spelling
        mode = responses.get("attention_mode", "serial7")
        if mode == "serial7":
            subtractions = responses.get("attention_serial7", [])
            if len(subtractions) < 5 or any(s is None or str(s).strip() == "" for s in subtractions):
                errors.append("Please complete all 5 serial subtraction steps (100 minus 7 successively).")
        else:
            letters = responses.get("attention_spelling", [])
            if len(letters) < 5 or any(l is None or str(l).strip() == "" for l in letters):
                errors.append("Please enter all 5 letters for spelling 'WORLD' backwards.")
                
    elif step_idx == 4:  # Delayed Recall
        words = responses.get("recall_words", [])
        if not words or len(words) == 0:
            errors.append("Please attempt to recall the 3 stimulus words (or mark as unable if not recalled).")
            
    elif step_idx == 5:  # Language & Naming
        if not responses.get("lang_naming_1", "").strip():
            errors.append("Please answer the first naming question (wrist device).")
        if not responses.get("lang_naming_2", "").strip():
            errors.append("Please answer the second naming question (ink writing instrument).")
        if not responses.get("lang_repetition", "").strip():
            errors.append("Please enter the phrase repetition response.")
        if not responses.get("lang_fluency", "").strip():
            errors.append("Please provide the category association response.")
            
    elif step_idx == 6:  # Comprehension & Multi-step Execution
        step1 = responses.get("comp_step_1")
        step2 = responses.get("comp_step_2")
        step3 = responses.get("comp_step_3")
        if step1 is None or step2 is None or step3 is None:
            errors.append("Please complete all three procedural comprehension checks.")
            
    elif step_idx == 7:  # Visuospatial & Executive
        if not responses.get("visuo_pentagon"):
            errors.append("Please select the correct intersecting shape pattern.")
        if not responses.get("visuo_clock"):
            errors.append("Please select the clock reading corresponding to '10 minutes past 11'.")

    return (len(errors) == 0, errors)


def calculate_assessment_score(responses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a deterministic, transparent score for the prototype questionnaire.
    
    Scoring Rules:
    1. Orientation Time (5 pts):
       - Year: 1 pt if within 0 years of current local year.
       - Season: 1 pt if matching or adjacent season.
       - Month: 1 pt if exact match to current month.
       - Date: 1 pt if within ±2 days of actual current date.
       - Day of week: 1 pt if exact match.
    2. Orientation Place (5 pts):
       - Country: 1 pt if provided realistic text.
       - State/Province: 1 pt if provided non-empty realistic text.
       - City/Town: 1 pt if provided non-empty realistic text.
       - Setting (e.g. Home, Hospital, Clinic): 1 pt if realistic setting chosen.
       - Room/Floor: 1 pt if valid entry.
    3. Registration (3 pts):
       - 1 pt for each target word correctly repeated in immediate phase (Apple, Table, Penny).
    4. Attention & Calculation (5 pts):
       - Serial 7s from 100: Expected sequence [93, 86, 79, 72, 65]. 1 pt per correct difference.
       - OR Spelling WORLD backwards: Expected ['D', 'L', 'R', 'O', 'W']. 1 pt per matching letter in position.
    5. Delayed Recall (3 pts):
       - 1 pt for each of the 3 target words recalled without prompt (Apple, Table, Penny).
    6. Language (4 pts):
       - Naming 1 (Watch/Wristwatch): 1 pt.
       - Naming 2 (Pen/Ballpoint): 1 pt.
       - Repetition ("No ifs, ands, or buts"): 1 pt.
       - Fluency/Category: 1 pt for valid animal / exemplar entry.
    7. Comprehension & Instruction (3 pts):
       - Step 1 executed: 1 pt.
       - Step 2 executed: 1 pt.
       - Step 3 executed: 1 pt.
    8. Visuospatial & Executive (2 pts):
       - Intersecting shapes correct selection: 1 pt.
       - Clock face reading correct selection: 1 pt.
       
    Total Max: 30.0 pts.
    """
    temporal_ref = get_current_temporal_reference()
    domain_scores: Dict[str, Dict[str, Any]] = {}
    
    # ---------------------------------------------------------
    # 1. Orientation: Time (Max 5.0)
    # ---------------------------------------------------------
    time_score = 0.0
    
    # Year check
    user_year = str(responses.get("time_year", "")).strip()
    if user_year == temporal_ref["year"]:
        time_score += 1.0
        
    # Season check
    user_season = str(responses.get("time_season", "")).strip().lower()
    if user_season == temporal_ref["season"] or user_season in ("fall", "autumn") and temporal_ref["season"] == "autumn":
        time_score += 1.0
        
    # Month check
    user_month = str(responses.get("time_month", "")).strip().lower()
    if user_month == temporal_ref["month"]:
        time_score += 1.0
        
    # Date check (±2 days tolerance for clinical prototype leeway)
    try:
        user_date = int(responses.get("time_date", 0))
        ref_date = int(temporal_ref["day_num"])
        if abs(user_date - ref_date) <= 2:
            time_score += 1.0
    except (ValueError, TypeError):
        pass
        
    # Day of week check
    user_day = str(responses.get("time_day", "")).strip().lower()
    if user_day == temporal_ref["day_name"]:
        time_score += 1.0
        
    domain_scores["orientation_time"] = {
        "title": "Orientation: Time",
        "score": round(time_score, 1),
        "max_score": 5.0,
        "percentage": round((time_score / 5.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # 2. Orientation: Place (Max 5.0)
    # ---------------------------------------------------------
    place_score = 0.0
    place_keys = ["place_country", "place_state", "place_city", "place_setting", "place_room"]
    for key in place_keys:
        val = str(responses.get(key, "")).strip()
        # Non-empty meaningful response (>1 char, not generic placeholder 'none' or 'na')
        if len(val) >= 2 and val.lower() not in ("none", "n/a", "no", "unknown", "idk", "test"):
            place_score += 1.0
            
    domain_scores["orientation_place"] = {
        "title": "Orientation: Place",
        "score": round(place_score, 1),
        "max_score": 5.0,
        "percentage": round((place_score / 5.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # 3. Immediate Registration (Max 3.0)
    # ---------------------------------------------------------
    reg_score = 0.0
    user_reg_words = [str(w).strip().lower() for w in responses.get("registration_words", [])]
    for target in TARGET_REGISTRATION_WORDS:
        if any(target in w for w in user_reg_words):
            reg_score += 1.0
            
    domain_scores["registration"] = {
        "title": "Immediate Registration",
        "score": round(reg_score, 1),
        "max_score": 3.0,
        "percentage": round((reg_score / 3.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # 4. Attention & Calculation (Max 5.0)
    # ---------------------------------------------------------
    att_score = 0.0
    att_mode = responses.get("attention_mode", "serial7")
    
    if att_mode == "serial7":
        expected_seq = [93, 86, 79, 72, 65]
        user_seq = responses.get("attention_serial7", [])
        for i, exp in enumerate(expected_seq):
            if i < len(user_seq):
                try:
                    val = int(user_seq[i])
                    if val == exp:
                        att_score += 1.0
                except (ValueError, TypeError):
                    pass
    else:
        expected_letters = ["D", "L", "R", "O", "W"]
        user_letters = responses.get("attention_spelling", [])
        for i, exp in enumerate(expected_letters):
            if i < len(user_letters):
                val = str(user_letters[i]).strip().upper()
                if val == exp:
                    att_score += 1.0
                    
    domain_scores["attention"] = {
        "title": "Attention & Calculation",
        "score": round(att_score, 1),
        "max_score": 5.0,
        "percentage": round((att_score / 5.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # 5. Delayed Recall (Max 3.0)
    # ---------------------------------------------------------
    recall_score = 0.0
    user_recall_words = [str(w).strip().lower() for w in responses.get("recall_words", [])]
    for target in TARGET_REGISTRATION_WORDS:
        if any(target in w for w in user_recall_words):
            recall_score += 1.0
            
    domain_scores["delayed_recall"] = {
        "title": "Delayed Recall",
        "score": round(recall_score, 1),
        "max_score": 3.0,
        "percentage": round((recall_score / 3.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # 6. Language & Naming (Max 4.0)
    # ---------------------------------------------------------
    lang_score = 0.0
    
    # Naming 1: watch / wristwatch
    n1 = str(responses.get("lang_naming_1", "")).strip().lower()
    if any(k in n1 for k in ["watch", "wristwatch", "clock"]):
        lang_score += 1.0
        
    # Naming 2: pen / ballpoint pen
    n2 = str(responses.get("lang_naming_2", "")).strip().lower()
    if any(k in n2 for k in ["pen", "ballpoint", "ink pen"]):
        lang_score += 1.0
        
    # Repetition: "No ifs, ands, or buts"
    rep = str(responses.get("lang_repetition", "")).strip().lower()
    clean_rep = rep.replace(",", "").replace(".", "").replace("'", "").replace('"', "")
    target_clean = "no ifs ands or buts"
    if clean_rep == target_clean:
        lang_score += 1.0
        
    # Fluency / Category association (e.g. named a valid animal >2 letters)
    fluency = str(responses.get("lang_fluency", "")).strip().lower()
    common_animals = ["cat", "dog", "elephant", "lion", "tiger", "bear", "horse", "cow", "pig", "sheep", "rabbit", "deer", "bird", "wolf", "zebra", "monkey", "giraffe", "fox", "dolphin", "whale"]
    if any(anim in fluency for anim in common_animals) or len(fluency) >= 3:
        lang_score += 1.0
        
    domain_scores["language"] = {
        "title": "Language & Naming",
        "score": round(lang_score, 1),
        "max_score": 4.0,
        "percentage": round((lang_score / 4.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # 7. Comprehension & Following Instructions (Max 3.0)
    # ---------------------------------------------------------
    comp_score = 0.0
    if responses.get("comp_step_1") is True or responses.get("comp_step_1") == "yes":
        comp_score += 1.0
    if responses.get("comp_step_2") is True or responses.get("comp_step_2") == "yes":
        comp_score += 1.0
    if responses.get("comp_step_3") is True or responses.get("comp_step_3") == "yes":
        comp_score += 1.0
        
    domain_scores["comprehension"] = {
        "title": "Comprehension & Execution",
        "score": round(comp_score, 1),
        "max_score": 3.0,
        "percentage": round((comp_score / 3.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # 8. Visuospatial & Executive (Max 2.0)
    # ---------------------------------------------------------
    visuo_score = 0.0
    
    # Intersecting pentagons/shapes pattern choice (Target: "Pattern B: Intersecting 5-sided pentagons with 4-sided intersection")
    pent_choice = str(responses.get("visuo_pentagon", "")).strip()
    if pent_choice.startswith("Option B") or "intersecting" in pent_choice.lower() and "4-sided" in pent_choice.lower():
        visuo_score += 1.0
        
    # Clock face reading for 10 past 11 (Hour hand at 11, minute hand at 2)
    clock_choice = str(responses.get("visuo_clock", "")).strip()
    if clock_choice.startswith("Option A") or "hour hand near 11" in clock_choice.lower():
        visuo_score += 1.0
        
    domain_scores["visuospatial"] = {
        "title": "Visuospatial & Executive",
        "score": round(visuo_score, 1),
        "max_score": 2.0,
        "percentage": round((visuo_score / 2.0) * 100.0, 1)
    }

    # ---------------------------------------------------------
    # Total Score Summary
    # ---------------------------------------------------------
    total_score = sum(d["score"] for d in domain_scores.values())
    total_score = min(total_score, MAX_ASSESSMENT_SCORE)
    percentage = round((total_score / MAX_ASSESSMENT_SCORE) * 100.0, 1)

    return {
        "total_score": round(total_score, 1),
        "max_score": MAX_ASSESSMENT_SCORE,
        "percentage_score": percentage,
        "domain_scores": domain_scores,
        "instrument_name": INSTRUMENT_NAME,
        "instrument_version": INSTRUMENT_VERSION
    }
