import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.evaluator import rag_evaluator


def main():
    print("=" * 65)
    print("AI INTERVIEW COACH - RAG RETRIEVAL BENCHMARK EVALUATION")
    print("=" * 65)
    metrics = rag_evaluator.evaluate_benchmark(top_k=3)

    print(f"\nBenchmark Summary ({metrics['total_benchmark_queries']} queries):")
    print(f"Top-1 Topic Accuracy:   {metrics['top1_topic_accuracy'] * 100:.1f}%")
    print(f"Mean Precision@3:       {metrics['mean_precision_at_k'] * 100:.1f}%")
    print(f"Mean Keyword Recall@3:  {metrics['mean_recall_at_k'] * 100:.1f}%")
    print(f"Mean Reciprocal Rank:   {metrics['mean_reciprocal_rank_mrr']:.4f}")
    print(f"Mean Top Confidence:    {metrics['mean_top_confidence'] * 100:.1f}%")
    print(f"Evaluation Runtime:     {metrics['evaluation_time_seconds']}s")
    print("\nDetailed Per-Query Results:")
    for idx, r in enumerate(metrics["detailed_query_results"], 1):
        status = "HIT" if r["topic_correct"] else "MISS"
        print(f" [{idx}] [{status}] Query: {r['query'][:55]}...")
        print(f"     Expected: {r['expected_topic']} | Top Retrieved: {r['top_topic']} (Conf: {r['top_score']})")
        print(f"     Recall: {r['keyword_recall']*100:.0f}% | Precision@3: {r['precision_at_k']*100:.0f}% | MRR: {r['mrr']:.2f}")
    print("=" * 65)


if __name__ == "__main__":
    main()
