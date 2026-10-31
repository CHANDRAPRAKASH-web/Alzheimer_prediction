"""
=========================================================
Aid Axis - Medical Document Repository

Manages metadata and file-storage for patient-uploaded
medical documents. Shared by:
  - Medical Document Vault  (patient upload & library)
  - Caregiver Dashboard     (read-only patient record access)

Storage layout:
  outputs/documents/<patient_id>/<doc_id>_<safe_filename>

Metadata persisted in the existing SQLite database.
=========================================================
"""

import uuid
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from database.connection import get_db_connection, get_db_path

logger = logging.getLogger(__name__)

# --- Document categories ---
DOCUMENT_CATEGORIES = [
    "Medical Reports",
    "Prescriptions",
    "Laboratory Reports",
    "Clinical Summaries",
    "Other Documents",
]

# --- Allowed MIME / extension mapping ---
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

# Max file size: 20 MB
MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB


def _doc_storage_root() -> Path:
    db_dir = get_db_path().parent
    root = db_dir / "documents"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _patient_storage_dir(patient_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in patient_id)
    d = _doc_storage_root() / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


class DocumentRepository:
    """
    Repository providing parameterized CRUD operations for medical documents.
    Patients own documents; caregivers have read-only access.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """Creates medical_documents table and indexes if they don't exist."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS medical_documents (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id          TEXT UNIQUE NOT NULL,
            patient_id      TEXT NOT NULL,
            title           TEXT NOT NULL,
            category        TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_type       TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL DEFAULT 0,
            upload_timestamp TEXT NOT NULL,
            document_date   TEXT,
            description     TEXT,
            is_deleted      INTEGER NOT NULL DEFAULT 0
        );
        """
        idx1 = """
        CREATE INDEX IF NOT EXISTS idx_docs_patient
        ON medical_documents(patient_id, upload_timestamp DESC);
        """
        idx2 = """
        CREATE INDEX IF NOT EXISTS idx_docs_category
        ON medical_documents(patient_id, category);
        """
        with get_db_connection(self.db_path) as conn:
            conn.execute(create_sql)
            conn.execute(idx1)
            conn.execute(idx2)

    # ------------------------------------------------------------------
    # Write operations (patient-facing)
    # ------------------------------------------------------------------

    def save_document(
        self,
        patient_id: str,
        title: str,
        category: str,
        original_filename: str,
        file_bytes: bytes,
        file_type: str,
        document_date: Optional[str] = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Persists a document file to disk and its metadata to SQLite.

        Returns the saved document record dict.
        Raises ValueError for validation failures.
        Raises RuntimeError if the file cannot be written.
        """
        # Validate
        if not title.strip():
            raise ValueError("Document title is required.")
        if category not in DOCUMENT_CATEGORIES:
            raise ValueError(f"Invalid category: {category}")
        ext = Path(original_filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"File type '{ext}' is not supported. Allowed: PDF, JPG, JPEG, PNG."
            )
        if len(file_bytes) == 0:
            raise ValueError("Uploaded file is empty.")
        if len(file_bytes) > MAX_FILE_BYTES:
            raise ValueError(
                f"File size exceeds {MAX_FILE_BYTES // (1024*1024)} MB limit."
            )

        doc_id = "DOC-" + uuid.uuid4().hex[:12].upper()
        safe_name = "".join(
            c if c.isalnum() or c in "._-" else "_"
            for c in Path(original_filename).name
        )
        stored_filename = f"{doc_id}_{safe_name}"

        # Write file to disk
        patient_dir = _patient_storage_dir(patient_id)
        file_path = patient_dir / stored_filename
        try:
            file_path.write_bytes(file_bytes)
        except OSError as exc:
            raise RuntimeError(f"Could not write document to disk: {exc}") from exc

        now_iso = datetime.now(timezone.utc).isoformat()

        insert_sql = """
        INSERT INTO medical_documents (
            doc_id, patient_id, title, category,
            original_filename, stored_filename, file_type,
            file_size_bytes, upload_timestamp, document_date, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with get_db_connection(self.db_path) as conn:
                conn.execute(
                    insert_sql,
                    (
                        doc_id,
                        patient_id,
                        title.strip(),
                        category,
                        original_filename,
                        stored_filename,
                        file_type,
                        len(file_bytes),
                        now_iso,
                        document_date or None,
                        description.strip() or None,
                    ),
                )
        except Exception as exc:
            # Rollback disk write if DB insert fails
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise RuntimeError(f"Database insert failed: {exc}") from exc

        logger.info(
            "Document %s saved for patient %s (%s bytes)",
            doc_id,
            patient_id,
            len(file_bytes),
        )
        return self.get_document_by_id(doc_id, patient_id)  # type: ignore[return-value]

    def delete_document(self, doc_id: str, patient_id: str) -> bool:
        """
        Soft-deletes a document record and removes the physical file.
        Verifies patient ownership before deletion.
        Returns True if deleted, False if not found or ownership mismatch.
        """
        rec = self.get_document_by_id(doc_id, patient_id)
        if not rec:
            return False

        # Remove physical file
        file_path = _patient_storage_dir(patient_id) / rec["stored_filename"]
        try:
            file_path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", file_path, exc)

        # Soft-delete in DB
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE medical_documents SET is_deleted = 1 WHERE doc_id = ? AND patient_id = ?",
                (doc_id, patient_id),
            )
        logger.info("Document %s deleted by patient %s", doc_id, patient_id)
        return True

    # ------------------------------------------------------------------
    # Read operations (shared patient + caregiver)
    # ------------------------------------------------------------------

    def get_documents(
        self,
        patient_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns non-deleted document records for a patient,
        optionally filtered by category and/or title search term.
        """
        conditions = ["patient_id = ?", "is_deleted = 0"]
        params: list = [patient_id]

        if category and category != "All Categories":
            conditions.append("category = ?")
            params.append(category)
        if search and search.strip():
            conditions.append("(title LIKE ? OR description LIKE ?)")
            term = f"%{search.strip()}%"
            params.extend([term, term])

        where = " AND ".join(conditions)
        query = f"""
        SELECT
            doc_id, patient_id, title, category,
            original_filename, stored_filename, file_type,
            file_size_bytes, upload_timestamp, document_date, description
        FROM medical_documents
        WHERE {where}
        ORDER BY upload_timestamp DESC
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_document_by_id(
        self, doc_id: str, patient_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches a single document record. Optionally checks patient ownership.
        Returns None if not found, deleted, or patient mismatch.
        """
        query = """
        SELECT
            doc_id, patient_id, title, category,
            original_filename, stored_filename, file_type,
            file_size_bytes, upload_timestamp, document_date, description
        FROM medical_documents
        WHERE doc_id = ? AND is_deleted = 0
        """
        params: list = [doc_id]
        if patient_id:
            query += " AND patient_id = ?"
            params.append(patient_id)

        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def count_documents(self, patient_id: str) -> int:
        """Returns count of non-deleted documents for a patient."""
        with get_db_connection(self.db_path) as conn:
            cur = conn.execute(
                "SELECT COUNT(*) as cnt FROM medical_documents WHERE patient_id = ? AND is_deleted = 0",
                (patient_id,),
            )
            row = cur.fetchone()
            return int(row["cnt"]) if row else 0

    def get_file_bytes(self, doc_id: str, patient_id: str) -> Optional[bytes]:
        """
        Reads and returns the raw bytes of a stored document file.
        Returns None if record not found, file missing, or ownership fails.
        """
        rec = self.get_document_by_id(doc_id, patient_id)
        if not rec:
            return None
        file_path = _patient_storage_dir(patient_id) / rec["stored_filename"]
        if not file_path.exists():
            logger.warning("Physical file missing for doc %s: %s", doc_id, file_path)
            return None
        return file_path.read_bytes()

    def get_categories_with_counts(self, patient_id: str) -> Dict[str, int]:
        """Returns {category: count} for all non-deleted documents of a patient."""
        query = """
        SELECT category, COUNT(*) as cnt
        FROM medical_documents
        WHERE patient_id = ? AND is_deleted = 0
        GROUP BY category
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(query, (patient_id,))
            return {row["category"]: row["cnt"] for row in cursor.fetchall()}
