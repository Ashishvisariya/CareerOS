# CareerOS — AI Career Operating System

CareerOS is an AI-powered career intelligence project that analyzes a candidate's resume, compares their skills with job requirements, identifies skill gaps, and builds a structured view of career readiness.

> **Project status:** This README documents the architecture and components discussed during development. Some features may still be under development. Verify the current code and configuration in your repository before treating every feature as production-ready.

## Table of contents

- [What CareerOS does](#what-careeros-does)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Technology stack](#technology-stack)
- [How the pipeline works](#how-the-pipeline-works)
- [Local job requirements](#local-job-requirements)
- [Setup](#setup)
- [Environment variables](#environment-variables)
- [Run the project](#run-the-project)
- [Testing](#testing)
- [Roadmap and known limitations](#roadmap-and-known-limitations)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## What CareerOS does

The goal of CareerOS is to connect a candidate's current profile with job-market expectations.

Capabilities built or explored so far include:

- Loading resumes from PDF files and common image formats.
- OCR support for scanned/image resumes when configured.
- Extracting skills, experience, projects, education, and strengths from resume text.
- Collecting jobs through API clients, including Adzuna and Jooble integrations.
- Structuring job requirements such as required and preferred skills.
- Matching candidate skills against job requirements.
- Calculating skill gaps for required and preferred skills.
- Building a Career State profile for a candidate and target roles.
- Loading a local set of job requirement JSON files for repeatable analysis without depending on a live job API.

The longer-term roadmap includes standardized skill taxonomies, learning roadmaps, career-readiness simulation, adaptive interviews, an AI career agent, a professional UI, evaluation, and deployment. These are roadmap goals and may not all be implemented yet.

## Architecture

```text
Resume (PDF / image)
        |
        v
Resume Loader + OCR
        |
        v
Extracted Resume Text
        |
        v
Resume Analysis
(skills, experience, projects, education, strengths)
        |
        +-----------------------------------+
                                            |
Local Job JSONs / Job APIs                  |
        |                                   |
        v                                   |
Job Loading + Job Analysis                  |
        |                                   |
        v                                   |
Required / Preferred Skills                 |
        |                                   |
        +------------------+----------------+
                           |
                           v
                    Skill Gap Engine
                           |
                           v
                 Job Matching / Career State
                           |
                           v
                Career insights and next steps
```

Keep these concepts separate:
- **Resume analysis** describes the candidate.
- **Job analysis** describes what a role asks for.
- **Skill-gap analysis** compares the two.
- **Career State** summarizes the candidate in the context of target roles or a selected set of jobs.

A skill-coverage percentage is meaningful only when calculated against actual required skills. An empty skill-gap object is not a real market score.

## Project structure

This is a representative structure based on the repository layout shared during development. Some files may differ in your checkout.

```text
CareerOS/
├── agents/                  # Agent-related components / planned workflows
├── app/                     # Application or UI components
├── career/
│   ├── resume_analyzer.py   # Resume analysis logic (if used)
│   └── state.py             # Career State construction
├── chains/                  # LLM chains
├── config/                  # Configuration
├── data/
│   ├── resumes/             # Place resume PDF/image files here
│   └── job_requirements/    # Local job requirement JSON files
├── evaluation/              # Evaluation utilities
├── ingestion/
│   └── loaders.py           # Resume loading / OCR
├── intelligence/
│   └── resume_analyzer.py   # Resume analysis
├── jobs/
│   ├── api_client.py        # Adzuna API client
│   ├── fetcher.py           # Job fetching workflow
│   ├── jooble_client.py     # Jooble API client
│   ├── local_job_loader.py  # Local job JSON loader
│   └── storage.py           # Job storage
├── knowledge/               # Knowledge-related components
├── matching/
│   ├── matcher.py           # Resume-to-job matching
│   └── skill_gap.py         # Skill-gap calculations
├── retrieval/               # Retrieval and vector-store logic
├── schemas/
│   └── career_state.py      # Career State schema
├── tests/
│   ├── test_career_state.py
│   ├── test_job_analysis.py
│   ├── test_skill_gap.py
│   └── ...                  # Other tests
├── .env                     # Local secrets; do not commit
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## Technology stack

The repository has used or is configured for these technologies. Exact usage depends on the current modules:

- **Python** — application language.
- **Pydantic** — structured schemas and validation.
- **LangChain** — LLM orchestration and integrations.
- **Google Gemini** — analysis and embeddings, depending on configuration.
- **Chroma** — local vector storage for retrieval.
- **PyMuPDF / pypdf** — PDF extraction.
- **pytesseract + Tesseract OCR + Pillow** — OCR for scanned/image resumes.
- **Adzuna / Jooble APIs** — job-search integrations.
- **pytest or standalone Python scripts** — testing, depending on each test file.

## How the pipeline works

### 1. Resume ingestion

Resume files are read from `data/resumes/`. The loader should support the formats enabled in the current implementation, typically PDF, PNG, JPG, and JPEG.

Scanned PDFs and images may require OCR. Tesseract OCR is a separate system installation; installing the Python package alone may not be enough.

### 2. Resume analysis

Extracted text is sent to the resume analyzer. The expected structured output includes:

- Candidate name
- Skills
- Experience
- Projects
- Education
- Strengths

Review the results for accuracy. Do not assume a skill is verified simply because a model extracted it.

### 3. Job loading and analysis

Jobs may be fetched through configured API clients or loaded from local JSON files. Provider availability, rate limits, location coverage, and description length vary.

A local job JSON could follow this example:

```json
{
  "job_id": "example-ml-engineer-001",
  "title": "Machine Learning Engineer",
  "company": "Example Company",
  "location": "India",
  "required_skills": ["Python", "Machine Learning", "Model Evaluation"],
  "preferred_skills": ["PyTorch", "Docker", "MLOps"],
  "experience_requirements": ["Experience deploying machine learning models"],
  "education_requirements": ["A degree in a related field"],
  "source": "manual"
}
```

This is an illustrative format. Your actual JSON keys must match what `jobs/local_job_loader.py` and the consuming code expect. Inspect an existing JSON file if the keys differ.

### 4. Skill-gap analysis

The skill-gap engine compares candidate skills with a job's required and preferred skills. Typical output fields include:

- `matched_required`
- `missing_required`
- `matched_preferred`
- `missing_preferred`
- `required_skill_coverage`
- `preferred_skill_coverage`

A common required-skill coverage formula is:

```text
matched required skills / total required skills * 100
```

If a job has no required skills, coverage should be treated as unknown/not applicable rather than evidence of full coverage. Check how the current implementation handles empty lists.

Equivalent skill names (for example, `scikit-learn` and `sklearn`) may need an alias map so they are not incorrectly counted as separate skills.

### 5. Career State

`career/state.py` builds a candidate snapshot from resume analysis and the skill-gap information passed to it. `schemas/career_state.py` defines the state fields.

For market-level insights, analyze multiple jobs and aggregate how often each skill appears. Keep these measures separate:
- **Single-job coverage:** skill coverage against one posting.
- **Market coverage:** coverage across a defined collection of jobs.
- **Recurring gap:** a skill missing across multiple selected jobs.

Do not report a meaningful market score if no jobs were loaded or no valid required skills were found.

## Local job requirements

Put manually curated job requirement files in:

```text
data/job_requirements/
```

Example layout:

```text
data/
└── job_requirements/
    ├── internmo_ai_program.json
    ├── ml_engineer_production_001.json
    ├── qualcomm_ai_engineer.json
    └── ... other job JSON files
```

The dataset discussed during development includes AI engineering, machine learning, data science, internships, GenAI/LLM work, and production ML. It is a manually assembled test dataset, not a statistically representative sample of the entire job market.

From the repository root, check whether JSON files are present:

```powershell
Get-ChildItem .\data\job_requirements\*.json
```

Prefer a path anchored to the loader file's location over a path that depends on the terminal's current directory.

## Setup

### 1. Open the project directory

Use your actual repository path. For example:

```powershell
cd C:\Users\ashis\Desktop\Projects\CareerOS
```

### 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is unavailable, call the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe --version
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

If the environment is already set up, you may not need to reinstall packages.

### 4. Configure OCR if needed

Install Tesseract OCR separately if your resume loader uses it for scanned PDFs or images. Confirm the executable path on your machine and configure `pytesseract` accordingly.

## Environment variables

Create or update `.env` in the project root. Example placeholders:

```dotenv
GOOGLE_API_KEY=your_google_api_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
JOOBLE_API_KEY=your_jooble_api_key
```

These names are examples; verify the exact names used by the API client files. Never put real keys in README files, source control, screenshots, or public issue reports.

## Run the project

CareerOS has been run through separate scripts and tests rather than one confirmed `main.py`. Run commands from the repository root.

Examples of test scripts present in the project:

```powershell
python .\tests\test_career_state.py
python .\tests\test_job_analysis.py
python .\tests\test_skill_gap.py
python .\tests\test_matcher.py
```

Some scripts may call an external API or LLM. Check the file before running it.

If the tests are pytest-compatible, you can run:

```powershell
python -m pytest
```

Or run a single module:

```powershell
python -m pytest .\tests\test_career_state.py -v
```

Some `test_*.py` files may be standalone scripts rather than pytest test modules. If a command fails, inspect the traceback and the file contents.

To run a standalone pipeline, use the filename you normally run. If it is in the project root:

```powershell
python .\your_script_name.py
```

Replace the placeholder with the real script name; it is not a runnable filename as written.

## Testing checklist

Validate that:

- Resume loading handles the file types you use.
- Resume analysis returns a structured result with the expected fields.
- The local job loader reads the expected JSON files.
- Skill-gap analysis correctly distinguishes matched and missing skills.
- Career State receives computed skill-gap results instead of a hard-coded empty object.
- Empty job folders or missing skill lists do not produce misleading market coverage.
- Missing experience evidence is not treated as a perfect match.

To count local job files:

```powershell
Get-ChildItem .\data\job_requirements\*.json | Measure-Object
```

## Roadmap and known limitations

Areas to validate or improve:

1. **Career State integration:** pass computed skill gaps instead of placeholder empty values.
2. **Market aggregation:** count skill frequency across jobs and identify recurring gaps.
3. **Skill aliases:** normalize equivalent skill names without merging unrelated concepts.
4. **Experience matching:** represent missing information as unknown/insufficient evidence rather than automatically assigning a perfect score.
5. **Preferred skills:** if a job has no preferred skills, show “not specified” rather than claiming 100% coverage.
6. **Job data quality:** manually curated JSON files may vary in completeness and schema.
7. **API limits:** API responses can contain short descriptions or provider-specific fields.
8. **Evaluation:** add tests based on manually reviewed examples.
9. **Privacy:** protect resumes, credentials, and personally identifying data.
10. **Deployment:** add production-grade logging, configuration validation, error handling, and deployment documentation before public release.

## Troubleshooting

### No resume found

Check that a supported resume file exists in `data/resumes/` and verify its extension and path.

### No local jobs loaded

Check that JSON files exist in `data/job_requirements/`, that the loader points to the right directory, and that the files end with `.json`.

### Skill coverage is 0%

Check that:
- Resume analysis returned a non-empty `skills` list.
- The job JSON contains `required_skills`.
- The skill-gap function receives the candidate's skills and the job's required skills.
- The Career State builder receives the calculated gap.
- Skill normalization handles capitalization and known aliases.

A 0% result can be legitimate for a specific job, but it may also indicate empty inputs.

### Import errors

Run commands from the repository root and use the intended virtual environment. Confirm module names and package structure match the imports in your code.

### API errors

Verify that the required environment variables are configured, credentials are valid, and rate limits have not been exceeded. Never print or share secret values while debugging.

## Security

- Never commit `.env` or API credentials.
- Keep resumes and personal data private.
- Avoid committing real resumes or private application information to a public repository.
- Use `.gitignore` for secrets, local vector databases, caches, and private data as appropriate.
- Review AI-generated outputs before using them for career decisions.

## License

No license is specified in this README. Add a `LICENSE` file and update this section if you intend to publish or distribute CareerOS.
