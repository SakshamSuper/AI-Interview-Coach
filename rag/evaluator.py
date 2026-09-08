import time
from typing import List, Dict, Any
from rag.retriever import InterviewRAGRetriever

# Standard technical benchmark queries with expected ground-truth annotations
RAG_BENCHMARK_CASES = [
    {
        "query": "Explain the CAP theorem and the difference between CP and AP distributed databases.",
        "expected_topic": "System Design",
        "expected_keywords": ["cap theorem", "consistency", "availability", "partition tolerance"]
    },
    {
        "query": "How does Python GIL affect multithreading in CPython and how do you achieve true parallelism?",
        "expected_topic": "Python & OOP",
        "expected_keywords": ["gil", "global interpreter lock", "multiprocessing", "cpython"]
    },
    {
        "query": "What are the ACID properties of database transactions and transaction isolation levels?",
        "expected_topic": "SQL & DBMS",
        "expected_keywords": ["acid", "atomicity", "isolation", "consistency", "durability"]
    },
    {
        "query": "What is the bias-variance tradeoff and how do Bagging and Boosting differ?",
        "expected_topic": "Machine Learning & AI",
        "expected_keywords": ["bias", "variance", "bagging", "boosting", "random forest"]
    },
    {
        "query": "How does Retrieval-Augmented Generation (RAG) ground LLMs and mitigate hallucinations?",
        "expected_topic": "Generative AI & RAG",
        "expected_keywords": ["rag", "retrieval", "embeddings", "vector", "hallucination"]
    },
    {
        "query": "What is a Kubernetes Pod and how does it relate to Docker containers?",
        "expected_topic": "Cloud & DevOps",
        "expected_keywords": ["kubernetes", "pod", "docker", "container"]
    }
]


class RAGEvaluator:
    def __init__(self, retriever: InterviewRAGRetriever = None):
        self.retriever = retriever or InterviewRAGRetriever()

    def evaluate_benchmark(self, top_k: int = 3, threshold: float = 0.40) -> Dict[str, Any]:
        """
        Executes benchmark queries against the live FAISS retriever and calculates real measured metrics.
        No fabricated numbers.
        """
        start_time = time.time()
        results = []
        topic_hits = 0
        total_precision_scores = []
        total_recall_scores = []
        reciprocal_ranks = []
        all_confidences = []

        for case in RAG_BENCHMARK_CASES:
            query = case["query"]
            expected_topic = case["expected_topic"]
            expected_keywords = case["expected_keywords"]

            retrieval_res = self.retriever.retrieve(query, top_k=top_k, threshold=threshold)
            docs = [doc for doc, _ in retrieval_res]
            scores = [score for _, score in retrieval_res]

            if scores:
                all_confidences.append(scores[0])

            # 1. Topic Hit & MRR
            case_mrr = 0.0
            top_hit = False
            for rank, doc in enumerate(docs, start=1):
                doc_topic = doc.metadata.get("topic", "")
                if doc_topic.lower() == expected_topic.lower():
                    if rank == 1:
                        top_hit = True
                    if case_mrr == 0.0:
                        case_mrr = 1.0 / rank

            if top_hit:
                topic_hits += 1
            reciprocal_ranks.append(case_mrr)

            # 2. Keyword Coverage & Relevance
            combined_context = " ".join([d.page_content.lower() for d in docs])
            matched_keywords = [kw for kw in expected_keywords if kw in combined_context]
            recall = len(matched_keywords) / len(expected_keywords) if expected_keywords else 1.0
            total_recall_scores.append(recall)

            # Precision: chunk relevance (fraction of chunks containing at least one expected keyword)
            relevant_chunks = sum(
                1 for d in docs if any(kw in d.page_content.lower() for kw in expected_keywords)
            )
            precision = (relevant_chunks / len(docs)) if docs else 0.0
            total_precision_scores.append(precision)

            results.append({
                "query": query,
                "expected_topic": expected_topic,
                "retrieved_count": len(docs),
                "top_score": round(scores[0], 4) if scores else 0.0,
                "top_topic": docs[0].metadata.get("topic", "None") if docs else "None",
                "topic_correct": top_hit,
                "keyword_recall": round(recall, 4),
                "precision_at_k": round(precision, 4),
                "mrr": round(case_mrr, 4)
            })

        total_queries = len(RAG_BENCHMARK_CASES)
        mean_topic_acc = topic_hits / total_queries
        mean_precision = sum(total_precision_scores) / total_queries
        mean_recall = sum(total_recall_scores) / total_queries
        mean_mrr = sum(reciprocal_ranks) / total_queries
        mean_confidence = (sum(all_confidences) / len(all_confidences)) if all_confidences else 0.0
        elapsed = round(time.time() - start_time, 3)

        return {
            "total_benchmark_queries": total_queries,
            "top1_topic_accuracy": round(mean_topic_acc, 4),
            "mean_precision_at_k": round(mean_precision, 4),
            "mean_recall_at_k": round(mean_recall, 4),
            "mean_reciprocal_rank_mrr": round(mean_mrr, 4),
            "mean_top_confidence": round(mean_confidence, 4),
            "evaluation_time_seconds": elapsed,
            "detailed_query_results": results
        }


rag_evaluator = RAGEvaluator()
