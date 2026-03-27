"""
RAG and retrieval helpers backed by ChromaDB.
"""

import glob
from pathlib import Path
from typing import Any, Dict, List

import chromadb
import ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter


class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    """Custom embedding function using Ollama embeddings API."""

    def __init__(self, model_name: str = "nomic-embed-text"):
        self.model_name = model_name

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for text in input:
            response = ollama.embeddings(model=self.model_name, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings


def load_documents(data_dir: str) -> Dict[str, str]:
    """Load .txt documents from disk."""
    documents: Dict[str, str] = {}
    for file_path in glob.glob(str(Path(data_dir) / "*.txt")):
        with open(file_path, "r", encoding="utf-8") as file:
            documents[Path(file_path).name] = file.read()
    return documents


def chunk_documents(documents: Dict[str, str], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """Split loaded documents into chunks for indexing."""
    chunked_documents: List[Dict[str, Any]] = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    for doc_name, content in documents.items():
        chunks = splitter.split_text(content)
        for i, chunk in enumerate(chunks):
            chunked_documents.append(
                {
                    "id": f"{doc_name}_chunk_{i}",
                    "text": chunk,
                    "metadata": {"source": doc_name, "chunk": i},
                }
            )

    return chunked_documents


class LoreRetriever:
    """Wrapper around Chroma collection for lore retrieval."""

    def __init__(self, persist_directory: str, collection_name: str, embedding_model: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding = OllamaEmbeddingFunction(model_name=embedding_model)
        self.collection_name = collection_name
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(name=self.collection_name, embedding_function=self.embedding)
        except Exception:
            return self.client.create_collection(name=self.collection_name, embedding_function=self.embedding)

    def rebuild_from_directory(self, data_dir: str) -> int:
        """Recreate the collection from documents in the directory."""
        documents = load_documents(data_dir)
        chunks = chunk_documents(documents)

        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        self.collection = self.client.create_collection(name=self.collection_name, embedding_function=self.embedding)

        if chunks:
            self.collection.add(
                ids=[chunk["id"] for chunk in chunks],
                documents=[chunk["text"] for chunk in chunks],
                metadatas=[chunk["metadata"] for chunk in chunks],
            )

        return len(chunks)

    def query(self, question: str, n_results: int = 3) -> List[str]:
        """Retrieve top-k context chunks for a query."""
        if not question.strip():
            return []

        results = self.collection.query(query_texts=[question], n_results=n_results)
        return results.get("documents", [[]])[0]
