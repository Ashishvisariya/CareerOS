from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=[
            "\n\n",
            "\n",
            " ",
            ""
        ]
    )

    chunks = splitter.split_documents(documents)

    return chunks