from pathlib import Path

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex


class StudyKnowledgeBase:
    def __init__(self, docs_dir: str) -> None:
        self._docs_dir = Path(docs_dir)
        self._query_engine = None

    def _ensure_engine(self) -> None:
        if self._query_engine is not None:
            return

        if self._docs_dir.exists() and any(self._docs_dir.glob("*.md")):
            docs = SimpleDirectoryReader(input_dir=str(self._docs_dir)).load_data()
            index = VectorStoreIndex.from_documents(docs)
            self._query_engine = index.as_query_engine(similarity_top_k=4)
            return

        self._query_engine = None

    def search(self, query: str) -> list[str]:
        self._ensure_engine()
        if self._query_engine is None:
            return [
                "No local study notes found yet. "
                "Add markdown files under evaluations/prompts/notes.",
            ]

        result = self._query_engine.query(query)
        text = str(result)
        chunks = [chunk.strip() for chunk in text.split("\n") if chunk.strip()]
        return chunks[:4] if chunks else [text]
