from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import get_settings

settings = get_settings()


class KnowledgeBaseSplitter:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Splits a list of documents into cohesive chunks with augmented metadata."""
        split_docs = []
        for doc in documents:
            chunks = self.splitter.split_text(doc.page_content)
            doc_name = doc.metadata.get("document_name", "unknown")
            topic = doc.metadata.get("topic", "General")

            for idx, chunk_text in enumerate(chunks):
                chunk_meta = dict(doc.metadata)
                chunk_meta["chunk_id"] = f"{doc_name}_chunk_{idx}"
                chunk_meta["chunk_index"] = idx
                chunk_meta["total_chunks_in_doc"] = len(chunks)
                chunk_meta["topic"] = topic

                split_docs.append(Document(page_content=chunk_text, metadata=chunk_meta))

        return split_docs


kb_splitter = KnowledgeBaseSplitter()
