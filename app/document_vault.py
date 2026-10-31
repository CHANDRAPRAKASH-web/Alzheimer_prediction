"""
=========================================================
Aid Axis - Medical Document Vault

Secure patient-facing interface for uploading, viewing,
previewing, and downloading personal medical documents.

Documents are persisted to disk under outputs/documents/
and indexed in SQLite via DocumentRepository.
=========================================================
"""

import html as _html
import base64
import streamlit as st
from datetime import datetime
from typing import Optional

from database.document_repository import (
    DocumentRepository,
    DOCUMENT_CATEGORIES,
    ALLOWED_EXTENSIONS,
    MAX_FILE_BYTES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _s(value) -> str:
    """HTML-escape a value for safe embedding in st.markdown HTML."""
    return _html.escape(str(value)) if value is not None else ""


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024 * 1024):.2f} MB"


def _fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y  %I:%M %p")
    except Exception:
        return iso


def _category_icon(cat: str) -> str:
    icons = {
        "Medical Reports": "🏥",
        "Prescriptions": "💊",
        "Laboratory Reports": "🔬",
        "Clinical Summaries": "📋",
        "Other Documents": "📂",
    }
    return icons.get(cat, "📄")


def _file_icon(file_type: str) -> str:
    ft = file_type.lower()
    if "pdf" in ft:
        return "📕"
    if "image" in ft or ft in {"jpg", "jpeg", "png"}:
        return "🖼️"
    return "📄"


def _mime_for_download(file_type: str, original_filename: str) -> str:
    ext = original_filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return "application/pdf"
    if ext in ("jpg", "jpeg"):
        return "image/jpeg"
    if ext == "png":
        return "image/png"
    return "application/octet-stream"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _init_vault_state():
    if "vault_filter_cat" not in st.session_state:
        st.session_state["vault_filter_cat"] = "All Categories"
    if "vault_search" not in st.session_state:
        st.session_state["vault_search"] = ""
    if "vault_preview_doc_id" not in st.session_state:
        st.session_state["vault_preview_doc_id"] = None
    if "vault_delete_confirm_id" not in st.session_state:
        st.session_state["vault_delete_confirm_id"] = None


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_document_vault(patient_id: str, repository: DocumentRepository):
    """
    Main entry point for the Medical Document Vault module.
    """
    _init_vault_state()

    # Header
    st.markdown("## 🗂️ Medical Document Vault")
    st.markdown(
        "<p style='color:#94A3B8;font-size:1.05rem;margin-top:-0.5rem;'>"
        "Securely upload, organise, and access your personal medical documents."
        "</p>",
        unsafe_allow_html=True,
    )

    # Patient badge + quick stats
    doc_count = repository.count_documents(patient_id)
    cat_counts = repository.get_categories_with_counts(patient_id)

    st.markdown(
        f"""
        <div style="display:flex;gap:0.75rem;align-items:center;margin-bottom:1.25rem;flex-wrap:wrap;">
            <span class="aidaxis-badge aidaxis-badge-violet">Patient: {_s(patient_id)}</span>
            <span class="aidaxis-badge aidaxis-badge-teal">{doc_count} document{'s' if doc_count != 1 else ''} stored</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_library, tab_upload = st.tabs(["📚 My Documents", "⬆️ Upload New Document"])

    with tab_upload:
        _render_upload_form(patient_id, repository)

    with tab_library:
        _render_library(patient_id, repository)


# ---------------------------------------------------------------------------
# Upload form
# ---------------------------------------------------------------------------

def _render_upload_form(patient_id: str, repository: DocumentRepository):
    st.markdown(
        """
        <div class="aidaxis-card aidaxis-card-accent"
             style="padding:1rem 1.25rem;margin-bottom:1rem;">
            <h4 style="margin:0;color:#F8FAFC;">⬆️ Upload Medical Document</h4>
            <div style="font-size:0.8rem;color:#94A3B8;margin-top:0.2rem;">
                Supported formats: PDF, JPG, JPEG, PNG &nbsp;·&nbsp; Max size: 20 MB
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("vault_upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Select File *",
            type=["pdf", "jpg", "jpeg", "png"],
            help="PDF, JPG/JPEG, or PNG — max 20 MB",
        )

        title = st.text_input(
            "Document Title *",
            placeholder="e.g., Blood Test Report — Oct 2026",
            max_chars=200,
        )

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category *", DOCUMENT_CATEGORIES)
        with col2:
            doc_date = st.date_input("Document Date (if known)", value=None)

        description = st.text_area(
            "Description (Optional)",
            placeholder="e.g., Fasting lipid panel, referred by Dr. Sharma",
            height=80,
            max_chars=500,
        )

        submitted = st.form_submit_button(
            "⬆️ Upload & Save Document", type="primary", use_container_width=True
        )

        if submitted:
            errors = []
            if not uploaded_file:
                errors.append("Please select a file to upload.")
            if not title.strip():
                errors.append("Document title is required.")
            if uploaded_file and uploaded_file.size > MAX_FILE_BYTES:
                errors.append(
                    f"File is too large ({_fmt_bytes(uploaded_file.size)}). "
                    f"Maximum allowed is {MAX_FILE_BYTES // (1024*1024)} MB."
                )

            if errors:
                for e in errors:
                    st.error(e)
            else:
                file_bytes = uploaded_file.read()
                doc_date_str = doc_date.isoformat() if doc_date else None
                try:
                    rec = repository.save_document(
                        patient_id=patient_id,
                        title=title.strip(),
                        category=category,
                        original_filename=uploaded_file.name,
                        file_bytes=file_bytes,
                        file_type=uploaded_file.type or "application/octet-stream",
                        document_date=doc_date_str,
                        description=description.strip(),
                    )
                    st.success(
                        f"✅ '{rec['title']}' uploaded successfully "
                        f"({_fmt_bytes(rec['file_size_bytes'])})."
                    )
                    st.rerun()
                except (ValueError, RuntimeError) as exc:
                    st.error(f"Upload failed: {exc}")

    # Clinical disclaimer
    st.markdown(
        """
        <div class="aidaxis-disclaimer">
            <strong>Privacy Notice:</strong> Documents are stored locally on this device
            and are never transmitted to external servers. Only you and authorised caregivers
            can access your records.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Document library
# ---------------------------------------------------------------------------

def _render_library(patient_id: str, repository: DocumentRepository):
    st.markdown(
        """
        <div class="aidaxis-card aidaxis-card-teal"
             style="padding:1rem 1.25rem;margin-bottom:1rem;">
            <h4 style="margin:0;color:#F8FAFC;">📚 My Document Library</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filter bar
    filter_col1, filter_col2 = st.columns([2, 3])
    with filter_col1:
        all_cats = ["All Categories"] + DOCUMENT_CATEGORIES
        sel_cat = st.selectbox(
            "Filter by Category",
            all_cats,
            index=all_cats.index(st.session_state["vault_filter_cat"])
            if st.session_state["vault_filter_cat"] in all_cats
            else 0,
            key="vault_cat_selector",
        )
        st.session_state["vault_filter_cat"] = sel_cat
    with filter_col2:
        search = st.text_input(
            "Search documents",
            value=st.session_state["vault_search"],
            placeholder="Search by title or description…",
            key="vault_search_input",
        )
        st.session_state["vault_search"] = search

    docs = repository.get_documents(patient_id, category=sel_cat, search=search)

    if not docs:
        st.markdown(
            f"""
            <div class="aidaxis-card" style="text-align:center;padding:2.5rem 1.5rem;">
                <div style="font-size:2.5rem;margin-bottom:0.75rem;">🗂️</div>
                <div style="color:#F8FAFC;font-weight:600;font-size:1.1rem;">
                    No documents found
                </div>
                <div style="color:#94A3B8;font-size:0.88rem;margin-top:0.4rem;">
                    {"Try a different search term or category." if search or sel_cat != "All Categories"
                     else "Upload your first medical document using the Upload tab."}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Category summary pills
    cat_counts = repository.get_categories_with_counts(patient_id)
    pills_html = "".join(
        f'<span class="aidaxis-badge aidaxis-badge-violet" style="margin-right:0.4rem;">'
        f'{_category_icon(cat)} {_s(cat)}: {cnt}</span>'
        for cat, cnt in cat_counts.items()
    )
    st.markdown(
        f'<div style="margin-bottom:1rem;display:flex;flex-wrap:wrap;gap:0.3rem;">{pills_html}</div>',
        unsafe_allow_html=True,
    )

    # Document cards
    preview_id = st.session_state.get("vault_preview_doc_id")
    delete_confirm_id = st.session_state.get("vault_delete_confirm_id")

    for doc in docs:
        _render_doc_card(
            doc,
            patient_id,
            repository,
            show_preview=preview_id == doc["doc_id"],
            show_delete_confirm=delete_confirm_id == doc["doc_id"],
        )


def _render_doc_card(
    doc: dict,
    patient_id: str,
    repository: DocumentRepository,
    show_preview: bool = False,
    show_delete_confirm: bool = False,
):
    """Renders a single document card with action buttons."""
    doc_id = doc["doc_id"]
    cat_icon = _category_icon(doc["category"])
    file_icon = _file_icon(doc["file_type"])
    doc_date_str = (
        f"Doc date: {doc['document_date']}" if doc.get("document_date") else ""
    )
    desc_html = (
        f'<div style="font-size:0.8rem;color:#A78BFA;margin-top:0.15rem;">📝 {_s(doc["description"])}</div>'
        if doc.get("description")
        else ""
    )

    card_html = (
        f'<div class="aidaxis-card aidaxis-card-accent"'
        f' style="margin-bottom:0.5rem;padding:0.9rem 1.1rem;">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="font-size:1rem;font-weight:600;color:#F8FAFC;">'
        f'{file_icon} {_s(doc["title"])}</div>'
        f'<div style="font-size:0.82rem;color:#94A3B8;margin:0.18rem 0;">'
        f'{cat_icon} {_s(doc["category"])} &nbsp;·&nbsp; '
        f'{_fmt_bytes(doc["file_size_bytes"])} &nbsp;·&nbsp; '
        f'Uploaded {_fmt_ts(doc["upload_timestamp"])}'
        f'</div>'
        + (f'<div style="font-size:0.8rem;color:#64748B;">{_s(doc_date_str)}</div>' if doc_date_str else "")
        + desc_html
        + f'</div>'
        f'<div style="margin-left:0.75rem;white-space:nowrap;">'
        f'<span class="aidaxis-badge aidaxis-badge-violet">{_s(doc["file_type"].split("/")[-1].upper())}</span>'
        f'</div>'
        f'</div></div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    # Action buttons
    c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
    with c1:
        lbl = "🔒 Close" if show_preview else "👁️ Preview"
        if st.button(lbl, key=f"vault_prev_{doc_id}", use_container_width=True):
            st.session_state["vault_preview_doc_id"] = (
                None if show_preview else doc_id
            )
            st.rerun()
    with c2:
        file_bytes = repository.get_file_bytes(doc_id, patient_id)
        if file_bytes:
            mime = _mime_for_download(doc["file_type"], doc["original_filename"])
            st.download_button(
                "⬇️ Download",
                data=file_bytes,
                file_name=doc["original_filename"],
                mime=mime,
                key=f"vault_dl_{doc_id}",
                use_container_width=True,
            )
        else:
            st.button(
                "⬇️ Download",
                key=f"vault_dl_na_{doc_id}",
                disabled=True,
                use_container_width=True,
                help="File not found on disk.",
            )
    with c3:
        if st.button("🗑️ Delete", key=f"vault_del_{doc_id}", use_container_width=True):
            st.session_state["vault_delete_confirm_id"] = doc_id
            st.rerun()

    # Inline preview
    if show_preview:
        _render_preview(doc, patient_id, repository)

    # Delete confirmation
    if show_delete_confirm:
        st.markdown(
            f"""
            <div style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.35);
                        border-radius:10px;padding:0.65rem 0.9rem;margin-bottom:0.4rem;">
                <div style="color:#FCA5A5;font-size:0.9rem;font-weight:600;margin-bottom:0.3rem;">
                    ⚠️ Delete &quot;{_s(doc['title'])}&quot;?
                </div>
                <div style="color:#94A3B8;font-size:0.8rem;">
                    This action permanently removes the document and cannot be undone.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cy, cn = st.columns(2)
        with cy:
            if st.button(
                "Yes, Delete",
                key=f"vault_del_yes_{doc_id}",
                type="primary",
                use_container_width=True,
            ):
                repository.delete_document(doc_id, patient_id)
                st.session_state["vault_delete_confirm_id"] = None
                st.success("Document deleted.")
                st.rerun()
        with cn:
            if st.button(
                "No, Keep It",
                key=f"vault_del_no_{doc_id}",
                use_container_width=True,
            ):
                st.session_state["vault_delete_confirm_id"] = None
                st.rerun()


def _render_preview(doc: dict, patient_id: str, repository: DocumentRepository):
    """Renders an inline preview for image and PDF files."""
    ext = doc["original_filename"].rsplit(".", 1)[-1].lower()
    file_bytes = repository.get_file_bytes(doc["doc_id"], patient_id)

    if not file_bytes:
        st.warning("⚠️ File could not be located on disk.")
        return

    with st.container():
        st.markdown(
            f"""
            <div style="background:#0F172A;border:1px solid #233148;border-radius:10px;
                        padding:1rem;margin-bottom:0.75rem;">
                <div style="color:#94A3B8;font-size:0.8rem;margin-bottom:0.5rem;">
                    Preview: <strong style="color:#F8FAFC;">{_s(doc['title'])}</strong>
                </div>
            """,
            unsafe_allow_html=True,
        )
        if ext in ("jpg", "jpeg", "png"):
            st.image(file_bytes, use_container_width=True)
        elif ext == "pdf":
            b64 = base64.b64encode(file_bytes).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="520px" style="border:none;border-radius:6px;"></iframe>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Preview not available for this file type. Use Download instead.")
        st.markdown("</div>", unsafe_allow_html=True)
