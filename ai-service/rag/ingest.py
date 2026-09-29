from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_FILE = BASE_DIR / "knowledge" / "clinical_guidelines.txt"
VECTOR_DB_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "clinical_guidelines"
EMBEDDING_MODEL = "nomic-embed-text"


def build_vector_store():
    """
    Read approved clinical guidance, split it into chunks,
    generate embeddings, and persist them in Chroma.
    """

    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError(
            f"Knowledge file not found: {KNOWLEDGE_FILE}"
        )

    text = KNOWLEDGE_FILE.read_text(encoding="utf-8")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=75,
    )

    documents = splitter.create_documents(
        [text],
        metadatas=[
            {
                "source": "clinical_guidelines.txt",
                "type": "approved_clinical_guidance",
            }
        ],
    )

    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DB_PATH),
    )

    # Development strategy: rebuild this collection from the approved source.
    vector_store.delete_collection()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DB_PATH),
    )

    vector_store.add_documents(documents)

    print(f"Ingested {len(documents)} document chunks.")
    print(f"Vector database: {VECTOR_DB_PATH}")

    return vector_store


if __name__ == "__main__":
    build_vector_store()