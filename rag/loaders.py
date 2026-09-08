import os
from typing import List, Dict, Any
from langchain_core.documents import Document
from nlp.preprocessing import extract_text_from_file, clean_text


class KnowledgeBaseLoader:
    """Loads documents from files into standardized LangChain Document objects with rich metadata."""

    TOPIC_MAPPINGS = {
        "python": "Python & OOP",
        "oop": "Python & OOP",
        "dsa": "Data Structures & Algorithms",
        "algorithm": "Data Structures & Algorithms",
        "system_design": "System Design",
        "sql": "SQL & DBMS",
        "dbms": "SQL & DBMS",
        "machine_learning": "Machine Learning & AI",
        "genai": "Generative AI & RAG",
        "rag": "Generative AI & RAG",
        "langchain": "Generative AI & RAG",
        "cloud": "Cloud & DevOps",
        "devops": "Cloud & DevOps"
    }

    def load_file(self, file_path: str) -> Document:
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()
        raw_text = extract_text_from_file(file_path)

        topic = self._infer_topic(filename, raw_text)
        metadata = {
            "source": file_path,
            "document_name": filename,
            "topic": topic,
            "document_type": ext.replace(".", ""),
            "character_count": len(raw_text)
        }
        return Document(page_content=raw_text, metadata=metadata)

    def load_directory(self, dir_path: str) -> List[Document]:
        documents = []
        if not os.path.exists(dir_path):
            return []

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.startswith(".") or file == "index.faiss" or file.endswith(".pkl"):
                    continue
                ext = os.path.splitext(file)[1].lower()
                if ext in [".md", ".txt", ".pdf", ".docx"]:
                    full_path = os.path.join(root, file)
                    try:
                        doc = self.load_file(full_path)
                        if doc.page_content.strip():
                            documents.append(doc)
                    except Exception as e:
                        print(f"Error loading document {full_path}: {e}")

        return documents

    def _infer_topic(self, filename: str, text: str) -> str:
        name_lower = filename.lower()
        for key, topic in self.TOPIC_MAPPINGS.items():
            if key in name_lower:
                return topic

        # Fallback to inspecting text content
        text_lower = text[:500].lower()
        for key, topic in self.TOPIC_MAPPINGS.items():
            if key in text_lower:
                return topic

        return "General Technical Knowledge"


kb_loader = KnowledgeBaseLoader()
