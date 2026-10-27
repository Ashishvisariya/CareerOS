from ingestion.loaders import load_resume
from ingestion.splitter import split_documents
from retrieval.vector_store import create_vector_store
from retrieval.retriever import get_retriever
# python test_resume_pipeline.py

from pathlib import Path

# 1. Load resume
resume_dir = Path("data/resumes")
resume_files = [f for f in resume_dir.iterdir() if f.suffix.lower() in [".pdf", ".png", ".jpg", ".jpeg"]]
resume_path = resume_files[0] if resume_files else Path("data/resumes/resume.pdf")

print(f"Loading resume from: {resume_path}")
documents = load_resume(str(resume_path))

print("Pages:", len(documents))


# 2. Split resume
chunks = split_documents(documents)

print("Chunks:", len(chunks))


# 3. Create vector store
vector_store = create_vector_store(chunks)

print("Vector store created!")


# 4. Create retriever
retriever = get_retriever(vector_store)


# 5. Search resume
results = retriever.invoke(
    "What technical skills does the candidate have?"
)


# 6. Print results
for i, doc in enumerate(results):

    print("\n--- RESULT", i + 1, "---")

    print(doc.page_content)