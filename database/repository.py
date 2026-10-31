"""
=========================================================
Aid Axis - Assessment Repository

Data access layer providing parameterized CRUD operations
for cognitive assessment records. Strictly avoids raw string
formatting to prevent SQL injection vulnerabilities and
enforces idempotency to avoid duplicate submissions.
=========================================================
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from database.connection import get_db_connection

logger = logging.getLogger(__name__)


class AssessmentRepository:
    """
    Repository handling persistence and retrieval of cognitive assessment records.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """
        Initializes the database schema if tables do not exist,
        and seeds demo patient profiles if needed.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cognitive_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            assessment_type TEXT NOT NULL,
            assessment_version TEXT NOT NULL,
            assessment_date TEXT NOT NULL,
            total_score REAL NOT NULL,
            max_score REAL NOT NULL,
            percentage_score REAL NOT NULL,
            domain_scores TEXT NOT NULL,
            responses TEXT NOT NULL,
            notes TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL
        );
        """
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_patient_date 
        ON cognitive_assessments(patient_id, assessment_date DESC);
        """

        with get_db_connection(self.db_path) as conn:
            conn.execute(create_table_sql)
            conn.execute(create_index_sql)

        # Seed realistic demonstration records for multiple patient profiles
        self.seed_demo_patients_if_needed()

    def seed_demo_patients_if_needed(self) -> None:
        """
        Seeds realistic historical cognitive assessment records for demonstration
        patient profiles (PATIENT-002, PATIENT-003, PATIENT-004) if not already present.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) as cnt FROM cognitive_assessments WHERE patient_id = 'PATIENT-002'"
                )
                row = cursor.fetchone()
                if row and row["cnt"] > 0:
                    return
        except Exception:
            return

        now = datetime.now(timezone.utc)

        # -----------------------------------------------------
        # PATIENT-002 (Arthur Pendelton, 76yo) - Progressive Mild Decline
        # -----------------------------------------------------
        p2_records = [
            {
                "assessment_id": "COG-P002-M01",
                "patient_id": "PATIENT-002",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=60)).isoformat(),
                "total_score": 27.0,
                "max_score": 30.0,
                "percentage_score": 90.0,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 4.0, "max_score": 5.0, "percentage": 80.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 1.0, "max_score": 2.0, "percentage": 50.0}
                },
                "responses": {"summary": "Initial intake evaluation"},
                "notes": "Patient accompanied by spouse. Alert, fully oriented, minor hesitation on serial 7s step 4.",
                "metadata": {"clinician": "Dr. Sarah Lin, MD", "cohort": "Observational Longitudinal"}
            },
            {
                "assessment_id": "COG-P002-M02",
                "patient_id": "PATIENT-002",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=30)).isoformat(),
                "total_score": 24.0,
                "max_score": 30.0,
                "percentage_score": 80.0,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 4.0, "max_score": 5.0, "percentage": 80.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 3.0, "max_score": 5.0, "percentage": 60.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 1.0, "max_score": 2.0, "percentage": 50.0}
                },
                "responses": {"summary": "Month 1 follow-up"},
                "notes": "Mild difficulty recalling exact date (-2 days). Recalled 2/3 target words after delay.",
                "metadata": {"clinician": "Dr. Sarah Lin, MD", "cohort": "Observational Longitudinal"}
            },
            {
                "assessment_id": "COG-P002-M03",
                "patient_id": "PATIENT-002",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=5)).isoformat(),
                "total_score": 22.0,
                "max_score": 30.0,
                "percentage_score": 73.3,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 3.0, "max_score": 5.0, "percentage": 60.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 4.0, "max_score": 5.0, "percentage": 80.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 3.0, "max_score": 5.0, "percentage": 60.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 1.0, "max_score": 3.0, "percentage": 33.3},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 2.0, "max_score": 2.0, "percentage": 100.0}
                },
                "responses": {"summary": "Month 2 follow-up"},
                "notes": "Patient reported sleep disruption and fatigue. Noted delayed recall of only 1 item (Penny). Recommended clinical consultation.",
                "metadata": {"clinician": "Dr. Sarah Lin, MD", "cohort": "Observational Longitudinal"}
            }
        ]

        # -----------------------------------------------------
        # PATIENT-003 (Margaret Chen, 68yo) - Post-Therapy Improvement
        # -----------------------------------------------------
        p3_records = [
            {
                "assessment_id": "COG-P003-M01",
                "patient_id": "PATIENT-003",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=45)).isoformat(),
                "total_score": 21.0,
                "max_score": 30.0,
                "percentage_score": 70.0,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 3.0, "max_score": 5.0, "percentage": 60.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 4.0, "max_score": 5.0, "percentage": 80.0},
                    "registration": {"title": "Immediate Registration", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "attention": {"title": "Attention & Calculation", "score": 3.0, "max_score": 5.0, "percentage": 60.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 1.0, "max_score": 3.0, "percentage": 33.3},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 2.0, "max_score": 2.0, "percentage": 100.0}
                },
                "responses": {"summary": "Post-hospitalization baseline"},
                "notes": "Baseline conducted following metabolic stabilization. Patient fatigued but highly cooperative.",
                "metadata": {"clinician": "Dr. Robert Vance, MD", "protocol": "Rehab Monitoring"}
            },
            {
                "assessment_id": "COG-P003-M02",
                "patient_id": "PATIENT-003",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=20)).isoformat(),
                "total_score": 25.0,
                "max_score": 30.0,
                "percentage_score": 83.3,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 4.0, "max_score": 5.0, "percentage": 80.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 4.0, "max_score": 5.0, "percentage": 80.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 1.0, "max_score": 2.0, "percentage": 50.0}
                },
                "responses": {"summary": "Mid-therapy assessment"},
                "notes": "Demonstrates notable recovery in attention and immediate encoding. Sleep quality reported improved.",
                "metadata": {"clinician": "Dr. Robert Vance, MD", "protocol": "Rehab Monitoring"}
            },
            {
                "assessment_id": "COG-P003-M03",
                "patient_id": "PATIENT-003",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=2)).isoformat(),
                "total_score": 28.0,
                "max_score": 30.0,
                "percentage_score": 93.3,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 1.0, "max_score": 2.0, "percentage": 50.0}
                },
                "responses": {"summary": "6-week review"},
                "notes": "Excellent recovery. Full 3-word recall achieved. Attention task executed with no errors.",
                "metadata": {"clinician": "Dr. Robert Vance, MD", "protocol": "Rehab Monitoring"}
            }
        ]

        # -----------------------------------------------------
        # PATIENT-004 (Robert Thorne, 81yo) - Stable High Performance
        # -----------------------------------------------------
        p4_records = [
            {
                "assessment_id": "COG-P004-M01",
                "patient_id": "PATIENT-004",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=90)).isoformat(),
                "total_score": 29.0,
                "max_score": 30.0,
                "percentage_score": 96.7,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 2.0, "max_score": 2.0, "percentage": 100.0}
                },
                "responses": {"summary": "Quarterly healthy aging check"},
                "notes": "Highly engaged, fluent, active community volunteer.",
                "metadata": {"clinician": "Dr. Sarah Lin, MD", "protocol": "Healthy Longevity Cohort"}
            },
            {
                "assessment_id": "COG-P004-M02",
                "patient_id": "PATIENT-004",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=45)).isoformat(),
                "total_score": 29.0,
                "max_score": 30.0,
                "percentage_score": 96.7,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 2.0, "max_score": 2.0, "percentage": 100.0}
                },
                "responses": {"summary": "Follow-up screening"},
                "notes": "Score identical to prior session. No memory complaints.",
                "metadata": {"clinician": "Dr. Sarah Lin, MD", "protocol": "Healthy Longevity Cohort"}
            },
            {
                "assessment_id": "COG-P004-M03",
                "patient_id": "PATIENT-004",
                "assessment_type": "Cognitive Monitoring Questionnaire — Prototype",
                "assessment_version": "v1.0-prototype",
                "assessment_date": (now - timedelta(days=7)).isoformat(),
                "total_score": 28.0,
                "max_score": 30.0,
                "percentage_score": 93.3,
                "domain_scores": {
                    "orientation_time": {"title": "Orientation: Time", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "orientation_place": {"title": "Orientation: Place", "score": 5.0, "max_score": 5.0, "percentage": 100.0},
                    "registration": {"title": "Immediate Registration", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "attention": {"title": "Attention & Calculation", "score": 4.0, "max_score": 5.0, "percentage": 80.0},
                    "delayed_recall": {"title": "Delayed Recall", "score": 3.0, "max_score": 3.0, "percentage": 100.0},
                    "language": {"title": "Language & Naming", "score": 4.0, "max_score": 4.0, "percentage": 100.0},
                    "comprehension": {"title": "Comprehension & Execution", "score": 2.0, "max_score": 3.0, "percentage": 66.7},
                    "visuospatial": {"title": "Visuospatial & Executive", "score": 2.0, "max_score": 2.0, "percentage": 100.0}
                },
                "responses": {"summary": "Quarterly evaluation"},
                "notes": "Minor calculation slip on serial 7s. Overall cognitive reserve remains robust.",
                "metadata": {"clinician": "Dr. Sarah Lin, MD", "protocol": "Healthy Longevity Cohort"}
            }
        ]

        for rec in p2_records + p3_records + p4_records:
            self.save_assessment(rec)

    def save_assessment(self, record: Dict[str, Any]) -> bool:
        """
        Inserts a completed cognitive assessment into the database.
        
        Guards:
        - Parameterized query
        - Prevents duplicate assessment_id insertions
        - Enforces non-overwrite policy
        
        Returns:
            True if inserted, False if assessment_id already exists.
        """
        assessment_id = record.get("assessment_id")
        if not assessment_id:
            raise ValueError("assessment_id is required.")

        patient_id = record.get("patient_id", "ANONYMOUS").strip() or "ANONYMOUS"
        assessment_type = record.get("assessment_type", "Cognitive Monitoring Questionnaire — Prototype")
        assessment_version = record.get("assessment_version", "v1.0-prototype")
        
        # Ensure timestamp is ISO formatted
        assessment_date = record.get("assessment_date")
        if not assessment_date:
            assessment_date = datetime.now(timezone.utc).isoformat()

        total_score = float(record.get("total_score", 0.0))
        max_score = float(record.get("max_score", 30.0))
        percentage_score = float(record.get("percentage_score", (total_score / max_score) * 100.0 if max_score > 0 else 0.0))
        
        domain_scores = record.get("domain_scores", {})
        if not isinstance(domain_scores, str):
            domain_scores = json.dumps(domain_scores)
            
        responses = record.get("responses", {})
        if not isinstance(responses, str):
            responses = json.dumps(responses)
            
        notes = record.get("notes", "")
        
        meta = record.get("metadata", {})
        if not isinstance(meta, str):
            meta = json.dumps(meta)

        created_at = datetime.now(timezone.utc).isoformat()

        insert_sql = """
        INSERT INTO cognitive_assessments (
            assessment_id,
            patient_id,
            assessment_type,
            assessment_version,
            assessment_date,
            total_score,
            max_score,
            percentage_score,
            domain_scores,
            responses,
            notes,
            metadata,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with get_db_connection(self.db_path) as conn:
            # Check for existing assessment_id to prevent duplicates
            cursor = conn.execute(
                "SELECT 1 FROM cognitive_assessments WHERE assessment_id = ?",
                (assessment_id,)
            )
            if cursor.fetchone() is not None:
                logger.warning("Assessment %s already exists. Duplicate submission prevented.", assessment_id)
                return False

            conn.execute(
                insert_sql,
                (
                    assessment_id,
                    patient_id,
                    assessment_type,
                    assessment_version,
                    assessment_date,
                    total_score,
                    max_score,
                    percentage_score,
                    domain_scores,
                    responses,
                    notes,
                    meta,
                    created_at,
                )
            )
            logger.info("Successfully persisted assessment %s for patient %s", assessment_id, patient_id)
            return True

    def get_assessments_by_patient(
        self,
        patient_id: str,
        order_asc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all assessment records for a specific patient.
        Default order is chronological (ASC) for time-series charting.
        """
        direction = "ASC" if order_asc else "DESC"
        query = f"""
        SELECT 
            assessment_id,
            patient_id,
            assessment_type,
            assessment_version,
            assessment_date,
            total_score,
            max_score,
            percentage_score,
            domain_scores,
            responses,
            notes,
            metadata,
            created_at
        FROM cognitive_assessments
        WHERE patient_id = ?
        ORDER BY assessment_date {direction}
        """

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, (patient_id,))
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

    def get_assessment_by_id(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single assessment by its unique assessment_id.
        """
        query = """
        SELECT 
            assessment_id,
            patient_id,
            assessment_type,
            assessment_version,
            assessment_date,
            total_score,
            max_score,
            percentage_score,
            domain_scores,
            responses,
            notes,
            metadata,
            created_at
        FROM cognitive_assessments
        WHERE assessment_id = ?
        """

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, (assessment_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def get_latest_assessment(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches the most recent assessment for the given patient.
        """
        query = """
        SELECT 
            assessment_id,
            patient_id,
            assessment_type,
            assessment_version,
            assessment_date,
            total_score,
            max_score,
            percentage_score,
            domain_scores,
            responses,
            notes,
            metadata,
            created_at
        FROM cognitive_assessments
        WHERE patient_id = ?
        ORDER BY assessment_date DESC
        LIMIT 1
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, (patient_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def get_all_patients(self) -> List[str]:
        """
        Returns a list of distinct patient IDs stored in the database.
        """
        query = "SELECT DISTINCT patient_id FROM cognitive_assessments ORDER BY patient_id ASC"
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query)
            return [row["patient_id"] for row in cursor.fetchall()]

    def count_assessments(self, patient_id: Optional[str] = None) -> int:
        """
        Returns count of assessments, optionally filtered by patient.
        """
        if patient_id:
            query = "SELECT COUNT(*) as cnt FROM cognitive_assessments WHERE patient_id = ?"
            params = (patient_id,)
        else:
            query = "SELECT COUNT(*) as cnt FROM cognitive_assessments"
            params = ()

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return int(row["cnt"]) if row else 0

    @staticmethod
    def _row_to_dict(row: Any) -> Dict[str, Any]:
        """
        Converts SQLite Row into a parsed Python dictionary.
        """
        d = dict(row)
        try:
            d["domain_scores"] = json.loads(d["domain_scores"])
        except (TypeError, json.JSONDecodeError):
            d["domain_scores"] = {}

        try:
            d["responses"] = json.loads(d["responses"])
        except (TypeError, json.JSONDecodeError):
            d["responses"] = {}

        try:
            d["metadata"] = json.loads(d["metadata"])
        except (TypeError, json.JSONDecodeError):
            d["metadata"] = {}

        return d
