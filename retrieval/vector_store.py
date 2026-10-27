from langchain_chroma import Chroma

from ingestion.embeddings import get_embeddings


def create_vector_store(documents):
    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="career_resume",
        persist_directory="chroma_db"
    )

    return vector_store


def load_vector_store():
    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name="career_resume",
        embedding_function=embeddings,
        persist_directory="chroma_db"
    )

    return vector_store