# Aid Axis — Cognitive Health & NeuroVision AI Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An integrated healthcare platform combining deep learning brain MRI analysis, longitudinal cognitive health tracking, conversational memory assistance, secure medical document archiving, and remote caregiver monitoring.

---

## 🌟 Key Modules & Capabilities

### 1. 🧠 NeuroVision AI (Brain MRI Analysis & Grad-CAM)
- **Deep Residual Network (ResNet-50)** fine-tuned for 4-class dementia classification:
  - *Non Demented*, *Very Mild Demented*, *Mild Demented*, *Moderate Demented*.
- **Explainable AI (Grad-CAM)**: Generates gradient-weighted class activation heatmaps overlaying the anatomical regions influencing classification decisions.
- Softmax probability distributions and confidence scores.

### 2. 📋 Cognitive Health Engine
- **Cognitive Monitoring Questionnaire (Prototype v1.0)**: A 30-point, 8-domain deterministic cognitive performance tracking instrument:
  - *Orientation (Time & Place)*
  - *Immediate Registration & Delayed Recall*
  - *Attention & Calculation (Serial 7s / Backward Spelling)*
  - *Language, Comprehension & Visuospatial Executive Functions*
- **Longitudinal Analytics & Progress Dashboard**: Interactive Plotly score trajectories, comparative delta analytics, and domain radar signatures.
- **Cognitive Digital Twin**: Polar performance fingerprint synthesizing historical assessment data across all 8 validated domains.

### 3. 🗓️ Memory Intelligence Hub
- **Conversational Memory Companion**: Powered by Groq LLM (`openai/gpt-oss-20b`) with native function/tool calling.
- **Autonomous Schedule Management**:
  - `create_event`, `get_events`, `update_event`, `mark_event_completed`, `cancel_event`.
- Natural language relative date & time parsing with timezone support (`Asia/Kolkata`).
- Synchronized dual-panel daily routine schedule.

### 4. 🗂️ Medical Document Vault
- Dual-layer storage: local filesystem persistence + SQLite metadata indexing.
- In-browser document previewer (Base64 PDF iframe & direct image viewer).
- Categorized management: *Medical Reports*, *Prescriptions*, *Laboratory Reports*, *Clinical Summaries*, *Other Documents*.
- Soft-delete auditing and search/filter.

### 5. 👩‍⚕️ Caregiver Dashboard
- Multi-patient cohort switcher with seeded longitudinal clinical profiles.
- Comprehensive patient overview, cognitive progress audits, and read-only medical document access.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PyTorch 2.0+
- (Optional) CUDA-compatible GPU for accelerated MRI inference.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chandraprakashmanikandan/Alzheimer.git
   cd Alzheimer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Secrets & API Keys:**
   Copy the example secrets file and insert your Groq API key:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   Edit `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   GROQ_MODEL = "openai/gpt-oss-20b"
   DEFAULT_TIMEZONE = "Asia/Kolkata"
   ```

4. **Run the Streamlit Application:**
   ```bash
   streamlit run app/streamlit_app.py
   ```

---

## 🧪 Running Tests

The test suite validates cognitive scoring, analytics logic, database transactions, datetime parsing, and Groq tool execution:

```bash
python -m unittest discover tests
```

---

## 🔒 Security & Privacy Notice

- **Confidentiality**: API keys and secrets are strictly excluded from version control via `.gitignore`.
- **Database**: Parameterized SQLite transactions with WAL mode prevent SQL injection vulnerabilities.
- **Clinical Notice**: Aid Axis is designed for observational and investigational research. It is not an FDA/CE-cleared diagnostic device.

