# Load documents
# Chunk them
# Create embeddings
# Store in FAISS

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

RAG_PATHS = [f"data/data_rag/rag{i}.txt" for i in range(1, 11)]
AGENTIC_PATHS = [f"data/data_agentic/agent{i}.txt" for i in range(1, 11)]


def ingest_paths(
    paths: list[str],
    index_folder: str,
    embeddings: OpenAIEmbeddings | None = None,
) -> None:
    documents = []
    for path in paths:
        documents.extend(TextLoader(path).load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)

    embeddings = embeddings or OpenAIEmbeddings()
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(index_folder)


def ingest_rag(embeddings: OpenAIEmbeddings | None = None) -> None:
    ingest_paths(RAG_PATHS, "db/faiss_index_rag", embeddings)


def ingest_agentic(embeddings: OpenAIEmbeddings | None = None) -> None:
    ingest_paths(AGENTIC_PATHS, "db/faiss_index_agentic", embeddings)


def ingest_all() -> None:
    embeddings = OpenAIEmbeddings()
    ingest_rag(embeddings)
    ingest_agentic(embeddings)


if __name__ == "__main__":
    ingest_all()
