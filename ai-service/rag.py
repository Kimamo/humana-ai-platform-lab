from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


KNOWLEDGE_FILE = Path("knowledge/clinical_guidelines.txt")
VECTOR_DB_PATH = "./chroma_db"


def build_vector_store():

    text = KNOWLEDGE_FILE.read_text()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=75,
    )

    chunks = splitter.create_documents([text])

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH,
    )

    return vector_store


def retrieve(question: str, k: int = 3):

    vector_store = build_vector_store()

    results = vector_store.similarity_search(
        question,
        k=k,
    )

    return results


if __name__ == "__main__":

    question = "Can the AI modify a patient's medical record?"

    documents = retrieve(question)

    print("\nQUESTION:")
    print(question)

    print("\nRETRIEVED CONTEXT:")

    for i, document in enumerate(documents, start=1):
        print(f"\n--- RESULT {i} ---")
        print(document.page_content)


def answer_with_rag(question: str) -> str:

    documents = retrieve(question)

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    model = ChatOllama(
        model="qwen3:8b",
        temperature=0,
    )

    prompt = f"""
             You are an AI assistant answering questions using an approved
             organizational knowledge base.

             Answer the question using ONLY the provided context.

             If the context does not contain enough information to answer the
             question, say:

                   "I don't have enough information in the approved knowledge base
                    to answer that question."

             Do not invent policies or facts.

    CONTEXT:
    {context}

    QUESTION:
    {question}
    """

    response = model.invoke(prompt)

    return str(response.content)


if __name__ == "__main__":

         # question = "What is the organization's vacation policy?"
        question = "Can the AI modify a patient's medical record?"

        print("\nQUESTION:")
        print(question)

        print("\nANSWER:")
        print(answer_with_rag(question))
