# CareerOS — AI Career Operating System

CareerOS is an AI career intelligence platform built to assess qualifications, compare against actual job specifications, prioritize skill gaps, generate actionable learning missions, and run adaptive interview simulations.

All scores and gap analysis are derived from real candidate data and real job postings using deterministic Python logic, using Groq LLM for language interpretation and structured extraction.

---

## Architecture Overview

- **Backend & Serving**: FastAPI (`api/main.py`) running via Uvicorn.
- **Frontend**: Clean semantic HTML5, CSS design tokens, and modular ES JavaScript served directly by FastAPI. Zero external frontend framework overhead.
- **LLM Provider**: Groq API (`ChatGroq`) for structured resume analysis, mission enrichment, job evaluation, and adaptive interview simulation.
- **Embeddings & Vector Store**: Google Gemini Embeddings (`models/gemini-embedding-001`) with persistent Chroma vector store (`chroma_db/`).
- **Data Persistence**: Atomic JSON persistence (`core/persistence.py`) for Career State, Roadmap Missions, Interview Sessions, and metadata cache.

---

## Key Features

1. **Executive Dashboard**: Calculable metrics (evaluated jobs count, market coverage percentage, active learning missions, interview session history).
2. **Resume Intelligence**: Multi-format ingestion (PDF with PyMuPDF, scanned PDF fallback with Tesseract OCR, images), chunking, and Groq-powered structured extraction into Pydantic models.
3. **Job Market Intelligence**: Paginated browsing, search, and filtering across a curated local sample dataset of 13 job requirement specifications.
4. **Deterministic Matching & Skill Gap Analysis**: Transparent calculations identifying verified candidate skills, missing required skills, missing preferred skills, and recurring market gaps.
5. **Multi-Dimensional Career Readiness**: Transparent scoring formula:
   $$\text{Readiness} = 40\% \times \text{Req} + 15\% \times \text{Pref} + 15\% \times \text{Projects} + 15\% \times \text{Exp} + 15\% \times \text{Interview}$$
   Explicitly documented and disclaimed in the UI as an analytical estimate, not a hiring guarantee.
6. **Learning Roadmap**: Market-frequency prioritized learning missions enriched with practical coding challenges, deliverables, and completion criteria.
7. **Adaptive AI Interview Simulation**: Multi-turn technical and behavioral practice sessions evaluated against a 5-dimension rubric (Technical Correctness, Reasoning, Relevance, Clarity, Practical Application).
8. **Grounded Career Agent**: Conversational advisor grounded strictly in current candidate state and matching data.
9. **Data Privacy & Atomic Purge**: Complete visibility into stored local files with one-click atomic deletion of all vectors, resumes, career state, and interview history.

---

## Quickstart Guide

### 1. Prerequisites
- Windows 10/11 or Linux/macOS
- Python 3.11+
- Virtual environment (`.venv`)

### 2. Environment Setup
Configure your environment variables in a `.env` file at the root:

```env
# Groq LLM Configuration (Chat & Structured Output)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Google Gemini Configuration (Embeddings only)
GOOGLE_API_KEY=your_google_api_key_here

# Job Search APIs (Optional)
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

### 3. Running the Platform
Start the FastAPI server (which serves both the REST API and the Frontend UI):

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start server
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser at:
- **Web Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Liveness & Readiness**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) and [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)

### 4. Running Automated Tests
Execute the comprehensive pytest test suite:

```powershell
python -m pytest
```

---

## Known Limitations

- **Dataset Scale**: The bundled job specifications consist of a curated local dataset of 13 postings used for prototype analysis, not a live global market census.
- **Authentication**: CareerOS operates in single-user mode storing files on your local machine. No remote user authentication or multi-tenant database is implemented.
- **LLM Non-Determinism**: While scoring calculations are deterministic Python logic, textual generation (interview questions, coaching explanations) is powered by Groq and may vary across runs.
- **OCR Quality**: Text extraction accuracy on scanned resumes depends on image resolution and the local Tesseract OCR engine.
