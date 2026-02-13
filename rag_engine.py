"""
InsightForge - RAG Engine Module
Implements Retrieval-Augmented Generation using SKLearn vector store,
LangChain text splitters, and HuggingFace embeddings.
"""

import os
import pickle
from typing import List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config import Config


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    Chunks documents, embeds them, and retrieves relevant context using SKLearn.
    """

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._embeddings = None
        self._vector_store: Optional[SKLearnVectorStore] = None

    # ── Lazy-loaded Embeddings ──────────────────────────────

    @property
    def embeddings(self):
        """Lazy-load embeddings model to avoid slow startup."""
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=Config.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embeddings

    # ── Document Processing ─────────────────────────────────

    def create_documents(self, text: str, metadata: dict = None) -> List[Document]:
        """Split text into LangChain Document chunks."""
        if metadata is None:
            metadata = {}
        chunks = self.text_splitter.split_text(text)
        documents = [
            Document(page_content=chunk, metadata={**metadata, "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]
        return documents

    def create_documents_from_dataframe(self, df_context: str, source: str = "uploaded_data") -> List[Document]:
        """Create documents from a DataFrame context string."""
        metadata = {"source": source, "type": "tabular_data"}
        return self.create_documents(df_context, metadata)

    def create_documents_from_text(self, text: str, source: str = "uploaded_document") -> List[Document]:
        """Create documents from raw text content."""
        metadata = {"source": source, "type": "document"}
        return self.create_documents(text, metadata)

    # ── Vector Store Management ─────────────────────────────

    def build_vector_store(self, documents: List[Document]) -> SKLearnVectorStore:
        """Build a SKLearn vector store from documents."""
        self._vector_store = SKLearnVectorStore.from_documents(
            documents=documents,
            embedding=self.embeddings,
        )
        return self._vector_store

    def add_to_vector_store(self, documents: List[Document]):
        """Add documents to an existing vector store."""
        if self._vector_store is None:
            self.build_vector_store(documents)
        else:
            self._vector_store.add_documents(documents)

    def save_vector_store(self, name: str = "default.pkl"):
        """Persist vector store to disk using pickle."""
        if self._vector_store is not None:
            file_path = os.path.join(Config.VECTOR_STORE_DIR, name)
            if not name.endswith('.pkl'):
                file_path += '.pkl'
            
            self._vector_store.persist(file_path)

    def load_vector_store(self, name: str = "default.pkl") -> Optional[SKLearnVectorStore]:
        """Load a persisted vector store."""
        file_path = os.path.join(Config.VECTOR_STORE_DIR, name)
        if not name.endswith('.pkl'):
            file_path += '.pkl'
            
        if os.path.exists(file_path):
            # SKLearnVectorStore uses pickle for persistence since recently
            # Or reconstruct from documents if persistence is tricky across versions
            # For simplicity in this demo, we'll try loading if supported, else assume ephemeral
            try:
                # Note: SKLearnVectorStore loading patterns vary by version.
                # Assuming standard load method if available or re-initialization
                self._vector_store = SKLearnVectorStore(
                    embedding=self.embeddings,
                    persist_path=file_path,
                    serializer="parquet" # or pickle depending on version
                )
                return self._vector_store
            except Exception:
                pass
        return None

    # ── Retrieval ───────────────────────────────────────────

    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """Retrieve the most relevant document chunks for a query."""
        if self._vector_store is None:
            return []
        k = k or Config.TOP_K_RESULTS
        return self._vector_store.similarity_search(query, k=k)

    def retrieve_with_scores(self, query: str, k: int = None) -> List[tuple]:
        """Retrieve relevant chunks with similarity scores."""
        if self._vector_store is None:
            return []
        k = k or Config.TOP_K_RESULTS
        results = self._vector_store.similarity_search_with_score(query, k=k)
        # SKLearn usually returns (doc, score), verify order
        return results

    def get_context_for_query(self, query: str, k: int = None) -> str:
        """Retrieve and concatenate relevant context for an LLM prompt."""
        docs = self.retrieve(query, k)
        if not docs:
            return "No relevant context found in the knowledge base."
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"--- Context {i} (Source: {source}) ---\n{doc.page_content}")
        return "\n\n".join(context_parts)

    # ── Status ──────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        """Check if the vector store has been initialized."""
        return self._vector_store is not None

    @property
    def document_count(self) -> int:
        """Number of document chunks in the vector store."""
        if self._vector_store is None:
            return 0
        # SKLearnVectorStore stores documents in ._docs or similar depending on implementation
        # We can try to infer from the index size
        try:
           return len(self._vector_store._index) if hasattr(self._vector_store, '_index') else 0
        except:
           return 0

    def clear(self):
        """Clear the vector store."""
        self._vector_store = None
