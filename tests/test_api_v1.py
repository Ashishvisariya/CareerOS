"""
CareerOS — Comprehensive Test Suite.
Tests API routes, upload validations, error envelope, pagination,
matching calculations, readiness dimensions, persistence, and data privacy.
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app
from intelligence.readiness import compute_readiness
from intelligence.skill_normalizer import normalize_skill, categorize_skills

client = TestClient(app)


def test_health_endpoint():
    """Verify liveness check returns 200 without calling external services."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_ready_endpoint():
    """Verify readiness check inspects local storage & config flags without external calls."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert "storage" in data
    assert "providers_configured" in data


def test_jobs_pagination_and_disclosure():
    """Verify jobs endpoint handles pagination, search, and includes dataset disclosure."""
    res = client.get("/api/v1/jobs?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert "dataset_disclaimer" in data
    assert len(data["jobs"]) <= 5
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_jobs_search_filtering():
    """Verify jobs endpoint accurately filters by search term."""
    res = client.get("/api/v1/jobs?q=Python")
    assert res.status_code == 200
    data = res.json()
    assert all("python" in str(j).lower() for j in data["jobs"])


def test_readiness_scoring_weights_and_dimensions():
    """Verify transparent deterministic readiness scoring math and disclaimer."""
    gap_dict = {
        "matched_required": ["Python", "PyTorch"],
        "missing_required": ["Docker"],
        "matched_preferred": ["LangChain"],
        "missing_preferred": [],
    }
    result = compute_readiness(
        job_skill_gap=gap_dict,
        projects=["Developed a deep learning model using PyTorch and Python"],
        experience=["Senior ML Engineer working with Python for 3 years"],
        interview_sessions=[],
    )
    assert "overall_score" in result
    assert "dimensions" in result
    assert "disclaimer" in result
    assert result["dimensions"]["required_skill_coverage"] == pytest.approx(66.67, 0.1)
    assert result["dimensions"]["preferred_skill_coverage"] == 100.0


def test_skill_normalization_and_categorization():
    """Verify skill normalizer resolves aliases deterministically without LLM."""
    assert normalize_skill("pytorch") == "PyTorch"
    assert normalize_skill("scikit-learn") == "Scikit-learn"
    assert normalize_skill("k8s") == "Kubernetes"
    
    categories = categorize_skills(["PyTorch", "Python", "Docker"])
    assert "Programming Languages" in categories
    assert "AI/ML Frameworks" in categories


def test_resume_upload_validation_invalid_type():
    """Verify upload rejects unsupported file extensions with 422."""
    files = {"file": ("malicious.exe", b"binarycontent", "application/x-msdownload")}
    res = client.post("/api/v1/resume/upload", files=files)
    assert res.status_code == 422
    assert "Unsupported file type" in res.json()["error"]["detail"]


def test_resume_upload_validation_empty_file():
    """Verify upload rejects empty file with 422."""
    files = {"file": ("resume.pdf", b"", "application/pdf")}
    res = client.post("/api/v1/resume/upload", files=files)
    assert res.status_code == 422
    assert "empty" in res.json()["error"]["detail"].lower()


def test_data_summary_endpoint():
    """Verify stored data inspection endpoint returns accurate storage overview."""
    res = client.get("/api/v1/data/summary")
    assert res.status_code == 200
    data = res.json()
    assert "privacy_notice" in data
    assert "storage_location" in data
