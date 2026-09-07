# Generative AI, RAG, and Agentic Orchestration

## Retrieval-Augmented Generation (RAG) Architecture
RAG grounds LLM generation in external, domain-specific knowledge to mitigate hallucinations and provide source citations.
1. Document Ingestion: Documents loaded, cleaned, and partitioned into chunks with metadata (source, topic, chunk_id).
2. Embedding Generation: Chunks converted to dense vector representations using models like all-MiniLM-L6-v2 or text-embedding-3-small.
3. Vector Indexing: Embeddings indexed in vector databases using approximate nearest neighbor algorithms (e.g., FAISS with HNSW or Flat IP).
4. Query & Retrieval: User query embedded; top-K similar chunks retrieved using cosine similarity or inner product.
5. Contextual Generation: Retrieved passages injected into system prompt instructions with ground truth constraints.

## Chunking Strategies
- Fixed-size chunking: Splits at arbitrary character counts (risks breaking semantic context).
- Recursive character splitting: Splits hierarchically by paragraph, newline, and sentence boundaries to preserve cohesive ideas.
- Semantic chunking: Breaks text when embedding distance between consecutive sentences exceeds a similarity threshold.

## LangChain and LangGraph Multi-Agent Workflows
LangChain provides modular components: DocumentLoaders, TextSplitters, VectorStores, Retrievers, PromptTemplates, and Chains.
LangGraph enables stateful multi-agent workflows modeled as directed graphs:
- State: Explicit typed dictionary or Pydantic model passed between nodes.
- Nodes: Python functions or specialized agents performing tasks (e.g., Question Agent, Evaluation Agent).
- Edges & Conditional Routing: Directed transitions determining next node based on state values (e.g., continue interview vs finish).