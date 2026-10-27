from retrieval.vector_store import load_vector_store
from retrieval.retriever import get_retriever


def main():

    print("Loading vector store...")

    vector_store = load_vector_store()

    retriever = get_retriever(
        vector_store
    )

    query = (
        "What are the candidate's name, skills, "
        "experience, projects, education, and strengths?"
    )

    print("\nRetrieving resume chunks...\n")

    documents = retriever.invoke(query)

    print(f"Retrieved {len(documents)} documents")

    print("\n" + "=" * 60)

    for i, document in enumerate(documents, start=1):

        print(f"\nDOCUMENT {i}")
        print("-" * 60)

        print(document.page_content)

        print("\nMETADATA:")
        print(document.metadata)

        print("=" * 60)


if __name__ == "__main__":
    main()