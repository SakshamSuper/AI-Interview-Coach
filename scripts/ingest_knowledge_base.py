import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.ingestion import ingest_knowledge_base


def main():
    print("=" * 60)
    print("AI INTERVIEW COACH - KNOWLEDGE BASE INGESTION")
    print("=" * 60)
    result = ingest_knowledge_base()
    print("\nIngestion Summary:")
    print(f"Status: {result['status']}")
    print(f"Documents Ingested: {result.get('total_documents', 0)}")
    print(f"Total Chunks: {result.get('total_chunks', 0)}")
    print(f"Topics: {result.get('topics', [])}")
    print(f"Output Directory: {result.get('output_dir', '')}")
    print(f"Elapsed Time: {result.get('elapsed_seconds', 0)} seconds")
    print("=" * 60)


if __name__ == "__main__":
    main()
