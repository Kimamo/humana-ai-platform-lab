from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "clinical_guidelines"
EMBEDDING_MODEL = "nomic-embed-text"


embeddings = OllamaEmbeddings(
    model=EMBEDDING_MODEL
)


vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=str(VECTOR_DB_PATH),
    embedding_function=embeddings,
)


def search_clinical_guidance(
    query: str,
    k: int = 3,
) -> list[dict]:
    """
    Search approved clinical guidance.
    """

    results = vector_store.similarity_search_with_relevance_scores(
        query,
        k=k,
    )

    return [
        {
            "content": document.page_content,
            "score": score,
            "source": document.metadata.get("source"),
        }
        for document, score in results
    ]


# ---------------------------------------------------------
# DEVELOPMENT / DIAGNOSTIC TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    questions = [
        "Can AI modify a patient's medical record?",
        "Who can access patient information?",
        "Can the AI prescribe medication?",
        "What is the organization's vacation policy?",
        "Who won the Super Bowl?",
    ]

    for question in questions:

        print("\n" + "=" * 70)
        print("QUESTION:")
        print(question)

        results = search_clinical_guidance(question)

        print(f"\nRetrieved {len(results)} result(s)")

        for index, result in enumerate(results, start=1):

            print(
                f"\n--- RESULT {index} "
                f"(score={result['score']:.3f}) ---"
            )

            print(f"Source: {result['source']}")
            print(result["content"])