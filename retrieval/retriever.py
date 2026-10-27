from langchain_core.documents import Document


def get_retriever(vector_store):
    """
    Convert the Chroma vector store into a retriever.

    Returns the 5 most relevant resume chunks.
    """

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 5
        }
    )

    return retriever


def retrieve_resume_chunks(
    retriever,
    query: str
) -> list[Document]:
    """
    Retrieve relevant resume chunks and remove
    duplicate content.
    """

    documents = retriever.invoke(query)

    unique_documents = []
    seen_content = set()

    for document in documents:

        content = document.page_content.strip()

        if not content:
            continue

        if content in seen_content:
            continue

        seen_content.add(content)
        unique_documents.append(document)

    return unique_documents