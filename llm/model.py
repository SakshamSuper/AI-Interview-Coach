import os
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from config.settings import get_settings
from config.logger import logger
from llm.structured_output import (
    InterviewQuestion, AnswerEvaluation, RecommendationOutput, parse_and_repair_json
)
from llm.prompts import (
    QUESTION_GENERATION_PROMPT, FOLLOW_UP_QUESTION_PROMPT,
    ANSWER_EVALUATION_PROMPT, RECOMMENDATION_PROMPT
)

settings = get_settings()


class BaseLLMClient(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass


class GroqClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = None):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model = model or settings.LLM_MODEL or "llama-3.3-70b-versatile"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        models_to_try = [self.model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        seen = set()
        last_err = None
        for m in models_to_try:
            if not m or m in seen:
                continue
            seen.add(m)
            try:
                response = self.client.chat.completions.create(
                    model=m,
                    messages=messages,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    response_format={"type": "json_object"}
                )
                self.model = m
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq model '{m}' call failed: {e}. Attempting next model...")
                last_err = e
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    time.sleep(4)
        if last_err:
            raise last_err
        raise RuntimeError("No Groq models could be executed.")


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model or "gpt-4o-mini"

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content


def _extract_previous_questions(prompt_lower: str) -> list[str]:
    prev_questions = []
    if "previously asked questions" in prompt_lower:
        pq_block = prompt_lower.split("previously asked questions")[1].split("\n\n")[0]
        for line in pq_block.split("\n"):
            line = line.strip().lstrip("-* ").strip()
            if line and line != "none" and not line.startswith("(") and not line.startswith("do not repeat"):
                prev_questions.append(line.lower())
    if "previous question:" in prompt_lower:
        pq_part = prompt_lower.split("previous question:")[1].split("\n")[0].strip(' "\'')
        if pq_part and pq_part != "none":
            prev_questions.append(pq_part.lower())
    return prev_questions


def _is_duplicate(cand_q: str, asked_questions: list[str]) -> bool:
    cand_norm = cand_q.strip().lower()
    for pq in asked_questions:
        pq_norm = pq.strip().lower()
        if not pq_norm:
            continue
        if cand_norm == pq_norm:
            return True
        if len(pq_norm) > 25 and (pq_norm in cand_norm or cand_norm in pq_norm):
            return True
    return False


ROLE_QUESTION_BANK: Dict[str, list[Dict[str, Any]]] = {
    "ml_ai": [
        {
            "topic": "Deep Learning & Optimization",
            "Easy": {
                "question": "Explain the difference between L1 (Lasso) and L2 (Ridge) regularization, and how each penalty mathematically affects weight updates and model sparsity.",
                "concepts": ["L1 Lasso sparsity", "L2 Ridge weight decay", "Loss function penalties", "Overfitting prevention"]
            },
            "Medium": {
                "question": "How do you detect and mitigate vanishing and exploding gradients when training deep neural networks, and how do residual connections and layer normalization help?",
                "concepts": ["Vanishing gradients", "Exploding gradients", "Residual skip connections", "Layer normalization", "Gradient clipping"]
            },
            "Hard": {
                "question": "Analyze the convergence dynamics of AdamW versus SGD with Nesterov momentum, focusing on how decoupled weight decay fixes L2 regularization in adaptive gradient methods.",
                "concepts": ["AdamW decoupled weight decay", "Nesterov momentum", "Adaptive learning rates", "Second-moment tracking", "Generalization gap"]
            }
        },
        {
            "topic": "Model Serving & Inference",
            "Easy": {
                "question": "What is the primary difference between batch inference and real-time streaming inference for machine learning models in terms of latency and compute utilization?",
                "concepts": ["Batch vs Real-time", "Latency SLAs", "Compute utilization", "Throughput optimization"]
            },
            "Medium": {
                "question": "How do you optimize large language model (LLM) inference latency using KV caching, continuous batching (vLLM), and post-training quantization?",
                "concepts": ["KV Caching", "Continuous batching", "PagedAttention", "Quantization (FP8/INT4)", "TTFT and TPOT"]
            },
            "Hard": {
                "question": "Design a high-throughput GPU serving cluster using Triton Inference Server with dynamic tensor parallelism, pipeline parallelism, and speculative decoding for a 70B parameter model.",
                "concepts": ["Tensor parallelism", "Pipeline parallelism", "Triton dynamic batching", "Speculative decoding", "GPU memory bandwidth limits"]
            }
        },
        {
            "topic": "Generative AI & RAG",
            "Easy": {
                "question": "What is Retrieval-Augmented Generation (RAG), and why is grounding context in an external vector store more reliable than fine-tuning for dynamic domain facts?",
                "concepts": ["Vector database retrieval", "Grounding context", "Parametric vs Non-parametric memory", "Hallucination reduction"]
            },
            "Medium": {
                "question": "Explain how hybrid search combines dense vector embeddings with sparse lexical search (BM25), and why reciprocal rank fusion (RRF) is used to blend results.",
                "concepts": ["Dense embeddings", "BM25 sparse search", "Reciprocal Rank Fusion (RRF)", "Out-of-vocabulary terms", "Semantic similarity"]
            },
            "Hard": {
                "question": "Architect an enterprise multi-hop RAG pipeline incorporating HyDE query expansion, semantic chunking, cross-encoder re-ranking, and self-reflective hallucination guardrails.",
                "concepts": ["HyDE query expansion", "Cross-encoder re-ranking", "Semantic boundary chunking", "Self-RAG reflection tokens", "Hallucination mitigation"]
            }
        },
        {
            "topic": "ML Evaluation & Data Drift",
            "Easy": {
                "question": "Explain the trade-off between precision and recall, and explain which metric you would prioritize when building a disease diagnosis or fraud detection model.",
                "concepts": ["Precision", "Recall", "False Positives vs False Negatives", "F1-score"]
            },
            "Medium": {
                "question": "How do you evaluate model performance on an imbalanced dataset (e.g., 99.5% negative class), and why is accuracy a misleading metric compared to PR-AUC or cost-sensitive matrices?",
                "concepts": ["Class imbalance", "PR-AUC curve", "Cost-sensitive matrix", "Focal loss", "Stratified sampling"]
            },
            "Hard": {
                "question": "Design a real-time statistical monitoring system to detect covariate shift versus concept drift on streaming inference features using Kolmogorov-Smirnov tests and PSI.",
                "concepts": ["Covariate shift", "Concept drift", "Population Stability Index (PSI)", "Two-sample Kolmogorov-Smirnov test", "Automated retraining triggers"]
            }
        }
    ],
    "data_science": [
        {
            "topic": "Experimentation & A/B Testing",
            "Easy": {
                "question": "What does a p-value represent in hypothesis testing, and what are the standard interpretations of Type I and Type II errors?",
                "concepts": ["p-value definition", "Null hypothesis", "Type I alpha error", "Type II beta error"]
            },
            "Medium": {
                "question": "How do you calculate statistical power and required sample size for an A/B test given a baseline conversion rate, minimum detectable effect (MDE), and variance?",
                "concepts": ["Statistical power (1 - beta)", "Minimum Detectable Effect (MDE)", "Sample size formula", "Variance reduction"]
            },
            "Hard": {
                "question": "How do you design an A/B experimentation platform that prevents peeking bias (p-hacking) using sequential probability ratio testing (SPRT) and handles two-sided marketplace network spillover?",
                "concepts": ["Sequential testing / SPRT", "Alpha spending functions", "Cluster-randomization", "Network spillover / SUTVA violation", "Cuped variance reduction"]
            }
        },
        {
            "topic": "Predictive Modeling & Feature Engineering",
            "Easy": {
                "question": "Why is k-fold cross-validation superior to a single train-test split, and what constitutes data leakage during feature preprocessing?",
                "concepts": ["K-fold cross-validation", "Data leakage", "Out-of-sample generalization", "Fit on train only"]
            },
            "Medium": {
                "question": "How do gradient boosted decision trees (like XGBoost or LightGBM) handle high-cardinality categorical features and missing values during split finding?",
                "concepts": ["Histogram-based split finding", "Target encoding", "Sparsity-aware splitting", "Regularization (L1/L2 on leaf weights)"]
            },
            "Hard": {
                "question": "Explain the mathematical formulation of SHAP (Shapley Additive Explanations) values based on cooperative game theory, and how TreeSHAP achieves polynomial-time feature attribution.",
                "concepts": ["Shapley values axioms", "Marginal contributions", "TreeSHAP algorithm", "Feature interaction effects", "Local vs Global interpretability"]
            }
        },
        {
            "topic": "Statistical Foundations & Distributions",
            "Easy": {
                "question": "What does the Central Limit Theorem state, and why is it foundational when estimating confidence intervals from non-normally distributed populations?",
                "concepts": ["Central Limit Theorem", "Sampling distribution of the mean", "Confidence intervals", "Standard error"]
            },
            "Medium": {
                "question": "Explain how multicollinearity affects regression coefficients, how to diagnose it using Variance Inflation Factor (VIF), and two methods to resolve it.",
                "concepts": ["Multicollinearity", "Variance Inflation Factor (VIF)", "Principal Component Analysis", "Ridge regression stabilization"]
            },
            "Hard": {
                "question": "Compare Maximum Likelihood Estimation (MLE) and Maximum A Posteriori (MAP) estimation, proving mathematically how MAP with a Gaussian prior is equivalent to L2 regularization.",
                "concepts": ["Log-likelihood optimization", "Bayesian prior", "Gaussian prior to L2 equivalence", "Posterior distribution", "Laplace prior to L1"]
            }
        }
    ],
    "data_engineering": [
        {
            "topic": "Distributed Data Processing",
            "Easy": {
                "question": "What is the difference between batch data processing and streaming data processing, and what are the typical latency requirements of each?",
                "concepts": ["Batch vs Stream", "Latency thresholds", "Throughput economics", "Scheduled vs Event-driven"]
            },
            "Medium": {
                "question": "In Apache Spark, explain the difference between narrow and wide transformations, and how shuffle operations cause network I/O and potential disk spilling.",
                "concepts": ["Narrow vs Wide transformations", "Spark Shuffle", "Partition repartitioning", "Out-of-memory disk spill"]
            },
            "Hard": {
                "question": "How do you diagnose and resolve severe data skew in an Apache Spark distributed join using salting keys, adaptive query execution (AQE), and broadcast hash joins?",
                "concepts": ["Data skew symptoms", "Key salting", "Adaptive Query Execution (AQE)", "Broadcast join thresholds", "Skewed partition splitting"]
            }
        },
        {
            "topic": "Real-time Streaming & Ingestion",
            "Easy": {
                "question": "What is the purpose of partitions in Apache Kafka, and how do they enable horizontal scalability and consumer parallelism?",
                "concepts": ["Kafka partitions", "Consumer groups", "Parallel consumption", "Partition key ordering"]
            },
            "Medium": {
                "question": "How do you achieve exactly-once processing (EOS) semantics in a streaming pipeline utilizing Kafka transactional producers and idempotent consumer patterns?",
                "concepts": ["Kafka transactions", "Idempotent producer", "Two-phase commit", "Consumer offset management"]
            },
            "Hard": {
                "question": "Design an end-to-end streaming ingestion architecture using Kafka and Apache Flink that handles out-of-order event arrivals with watermarks and sliding window aggregations.",
                "concepts": ["Event time vs Processing time", "Watermarks heuristics", "Allowed lateness", "Sliding window state backend (RocksDB)", "Checkpointing"]
            }
        },
        {
            "topic": "Data Warehousing & Lakehouse Architecture",
            "Easy": {
                "question": "Explain the difference between a Star Schema and a Snowflake Schema in data warehousing, and why denormalization is preferred for analytical OLAP queries.",
                "concepts": ["Star schema", "Snowflake schema", "Fact vs Dimension tables", "OLAP read performance"]
            },
            "Medium": {
                "question": "Compare row-oriented storage formats (e.g., Avro, CSV) with columnar formats (e.g., Parquet, ORC) regarding compression ratios and column-pruning performance.",
                "concepts": ["Parquet columnar layout", "Snappy/ZSTD compression", "Column projection / pruning", "Predicate pushdown"]
            },
            "Hard": {
                "question": "Analyze modern open table formats (Apache Iceberg vs Delta Lake vs Apache Hudi), focusing on metadata hierarchical manifests, ACID guarantees, and copy-on-write vs merge-on-read.",
                "concepts": ["Iceberg metadata snapshot tree", "ACID transactional commits", "Merge-on-read vs Copy-on-write", "Partition evolution", "Time-travel queries"]
            }
        }
    ],
    "backend_systems": [
        {
            "topic": "Distributed Systems & Consensus",
            "Easy": {
                "question": "What is the difference between synchronous HTTP/REST communication and asynchronous message-driven communication using message brokers?",
                "concepts": ["REST vs Queues", "Temporal decoupling", "Backpressure buffering", "Failure isolation"]
            },
            "Medium": {
                "question": "Explain the CAP Theorem and explain why modern distributed datastores are classified under the PACELC theorem to describe latency vs consistency during normal operations.",
                "concepts": ["CAP Theorem", "PACELC theorem", "Partition tolerance", "Eventual consistency vs Strong consistency"]
            },
            "Hard": {
                "question": "Explain the Raft consensus algorithm, detailing leader election state transitions, log replication safety invariants, and how network partitions are handled without split-brain.",
                "concepts": ["Raft consensus", "Leader election terms", "Log matching property", "Majority quorums", "Split-brain prevention"]
            }
        },
        {
            "topic": "Concurrency & Transaction Management",
            "Easy": {
                "question": "What is a database transaction, and what does each letter of ACID stand for in relational database management systems?",
                "concepts": ["Atomicity", "Consistency", "Isolation", "Durability"]
            },
            "Medium": {
                "question": "How do you prevent lost updates and race conditions in concurrent web services using optimistic locking (version column) versus pessimistic locking (SELECT FOR UPDATE)?",
                "concepts": ["Optimistic locking versioning", "Pessimistic SELECT FOR UPDATE", "Deadlock risks", "Throughput trade-offs"]
            },
            "Hard": {
                "question": "Explain Write-Ahead Logging (WAL) and PostgreSQL Multi-Version Concurrency Control (MVCC) internals, explaining write amplification, tuple bloat, and autovacuum tuning.",
                "concepts": ["WAL durability", "MVCC transaction snapshots", "XMIN / XMAX tuple headers", "Table and index bloat", "Autovacuum worker tuning"]
            }
        },
        {
            "topic": "High Availability & Caching Architecture",
            "Easy": {
                "question": "What is the purpose of an in-memory cache like Redis, and how does cache-aside differ from a direct database read?",
                "concepts": ["Redis in-memory store", "Cache-aside pattern", "Sub-millisecond latency", "Read replica offloading"]
            },
            "Medium": {
                "question": "Compare cache-aside, read-through, write-through, and write-behind (write-back) caching strategies, focusing on data consistency and crash durability.",
                "concepts": ["Cache-aside", "Write-through", "Write-behind buffer", "Cache invalidation", "Eventual consistency"]
            },
            "Hard": {
                "question": "Design a high-throughput distributed caching tier that mitigates cache stampedes (dog-piling), cache penetration via Bloom filters, and cache breakdown under thundering herd spikes.",
                "concepts": ["Cache stampede single-flight", "Distributed mutex / Redlock", "Bloom filters for missing keys", "Probabilistic early expiration (XFetch)", "Thundering herd mitigation"]
            }
        }
    ],
    "software_engineering": [
        {
            "topic": "Data Structures & Algorithms",
            "Easy": {
                "question": "What is the difference between an Array and a Singly-Linked List in terms of memory layout, random access, and insertion/deletion time complexity?",
                "concepts": ["Contiguous memory", "O(1) random access", "O(n) search", "Pointer overhead", "Insertion complexity"]
            },
            "Medium": {
                "question": "Explain the internal mechanics of a Hash Table, comparing collision resolution via separate chaining versus open addressing, and how load factor governs resizing.",
                "concepts": ["Hash function distribution", "Separate chaining", "Open addressing (linear probing)", "Load factor threshold", "Amortized O(1) resizing"]
            },
            "Hard": {
                "question": "Design an LRU-K Cache eviction policy that tracks the last K references to prevent cache pollution from one-off sequential scans, analyzing time and space complexity.",
                "concepts": ["LRU-K eviction algorithm", "Hash map + doubly-linked list", "History queue vs Cache queue", "Cache pollution prevention", "O(1) amortized access"]
            }
        },
        {
            "topic": "System Architecture & Scalability",
            "Easy": {
                "question": "What is the difference between vertical scaling and horizontal scaling, and what is the role of a reverse proxy like Nginx in front of application servers?",
                "concepts": ["Vertical vs Horizontal scaling", "Single Point of Failure", "Reverse proxy", "Load balancing", "SSL termination"]
            },
            "Medium": {
                "question": "How do you design a distributed rate-limiter for a public API using Token Bucket versus Sliding Window Log algorithms with Redis atomic scripts?",
                "concepts": ["Token bucket algorithm", "Sliding window log", "Redis Lua script atomicity", "HTTP 429 Too Many Requests", "Race condition prevention"]
            },
            "Hard": {
                "question": "Design a globally distributed unique ID generator (like Twitter Snowflake) that generates 64-bit strictly monotonic or k-sorted IDs without a centralized coordinator database.",
                "concepts": ["Snowflake ID bit structure (timestamp, datacenter, worker, sequence)", "Clock skew / NTP drift handling", "K-sorted properties", "Throughput scaling (4M IDs/sec)"]
            }
        },
        {
            "topic": "Concurrency & Thread Safety",
            "Easy": {
                "question": "What is the fundamental difference between a process and a thread regarding address space, memory sharing, and context switching overhead?",
                "concepts": ["Process memory isolation", "Shared thread memory", "Context switch overhead", "IPC mechanisms"]
            },
            "Medium": {
                "question": "How do deadlocks occur in concurrent programming, what are the four Coffman conditions, and how can lock ordering prevent them?",
                "concepts": ["Mutual exclusion", "Hold and wait", "No preemption", "Circular wait", "Global lock ordering"]
            },
            "Hard": {
                "question": "Explain lock-free concurrent data structures using atomic Compare-And-Swap (CAS) primitives, describing how to detect and resolve the ABA problem with tagged pointers.",
                "concepts": ["Compare-And-Swap (CAS)", "ABA problem", "Tagged pointers / version stamping", "Memory barriers / fences", "Lock-free stack (Treiber stack)"]
            }
        }
    ]
}


class LocalMockLLMClient(BaseLLMClient):
    """
    Offline development & testing provider that deterministically generates structured responses
    using role-aware question banks and duplicate question exclusion when API keys are not supplied.
    """
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        prompt_lower = prompt.lower()

        # 1. Recommendation Prompt
        if "recommendation" in prompt_lower or "overall_summary" in prompt_lower:
            return json.dumps({
                "overall_summary": "Candidate demonstrated solid engineering fundamentals with strong technical communication and clarity. Recommended for further practice on distributed consistency and production monitoring.",
                "strong_areas": ["System Architecture", "Python Fundamentals", "API Design"],
                "weak_areas": ["Distributed Transaction Isolation", "Container Orchestration Scaling"],
                "learning_priorities": [
                    "Priority 1: Distributed consistency models and CAP theorem trade-offs",
                    "Priority 2: Deep dive into B+ Tree index optimization in PostgreSQL",
                    "Priority 3: Advanced RAG retrieval and reranking pipelines"
                ],
                "practice_questions": [
                    "How would you design a distributed rate limiter in Redis?",
                    "Explain the difference between Read Committed and Serializable isolation levels.",
                    "How do you monitor and resolve memory leaks in a Python service?"
                ]
            })

        # 2. Follow-up Question Prompt
        elif "follow-up" in prompt_lower or "adaptive follow-up" in prompt_lower or "missing concepts:" in prompt_lower:
            missing_text = "core architectural trade-offs"
            if "missing concepts:" in prompt_lower:
                extracted = prompt_lower.split("missing concepts:")[1].split("\n")[0].strip()
                if extracted and extracted != "none":
                    missing_text = extracted

            diff = "Easy" if "target difficulty: easy" in prompt_lower or "difficulty: easy" in prompt_lower else (
                "Hard" if "target difficulty: hard" in prompt_lower or "difficulty: hard" in prompt_lower else "Medium"
            )

            current_topic = "System Design & Optimization"
            if "target topic:" in prompt_lower:
                extracted_topic = prompt_lower.split("target topic:")[1].split("\n")[0].strip()
                if extracted_topic and extracted_topic != "none":
                    current_topic = extracted_topic

            prev_questions = _extract_previous_questions(prompt_lower)

            follow_up_stems = [
                f"In your previous response regarding {current_topic}, you touched on the high level but did not fully address {missing_text}. Could you walk me step-by-step through how you would implement this in a production system?",
                f"Building on your explanation, let's explore {missing_text}. How would you architect this to handle operational edge cases and fault tolerance?",
                f"Regarding {current_topic}: can you dive deeper into {missing_text}, specifically analyzing the latency trade-offs and failure recovery modes?",
                f"To follow up on your response: what specific patterns or metrics would you use to operationalize and monitor {missing_text} under high load?"
            ]

            chosen_q = follow_up_stems[0]
            for stem in follow_up_stems:
                if not _is_duplicate(stem, prev_questions):
                    chosen_q = stem
                    break

            return json.dumps({
                "question": chosen_q,
                "topic": current_topic,
                "difficulty": diff,
                "question_type": "Technical Follow-Up",
                "reason": f"Adaptive remedial follow-up targeting candidate's identified gap: {missing_text}",
                "expected_concepts": [c.strip().title() for c in missing_text.split(",") if c.strip()] or ["Architecture", "Production Reliability"],
                "source_context": "Knowledge base grounding on targeted remediation."
            })

        # 3. Answer Evaluation Prompt
        elif "evaluate" in prompt_lower or "evaluate_answer" in prompt_lower:
            cand_ans = ""
            if 'candidate answer:\n"' in prompt_lower:
                cand_ans = prompt_lower.split('candidate answer:\n"')[1].split('"')[0]
            elif 'candidate answer:' in prompt_lower:
                cand_ans = prompt_lower.split('candidate answer:')[1][:200]

            ans_len = len(cand_ans.split())
            if ans_len > 30:
                score = 84.0
                next_diff = "Hard"
                feedback = "Thorough and articulate response covering the core architecture and practical trade-offs well."
                weaknesses = ["Could delve deeper into failure recovery modes."]
                missing = ["Specific recovery metrics like MTTR/RTO."]
            elif ans_len > 10:
                score = 72.0
                next_diff = "Medium"
                feedback = "Solid foundational concepts identified. Expanding on production edge cases would elevate your answer."
                weaknesses = ["Limited discussion of scaling and monitoring."]
                missing = ["Monitoring telemetry", "Dead letter queues"]
            else:
                score = 48.0
                next_diff = "Easy"
                feedback = "Brief response. Needs more technical detail and explicit architectural principles."
                weaknesses = ["Answer was too concise to evaluate complete depth."]
                missing = ["Architectural patterns", "Trade-offs", "Core implementation details"]

            return json.dumps({
                "technical_accuracy": score,
                "relevance": min(100.0, score + 4.0),
                "completeness": max(40.0, score - 6.0),
                "clarity": score,
                "communication": score + 2.0,
                "overall_score": score,
                "strengths": ["Clear communication", "Identified core engineering principles"],
                "weaknesses": weaknesses,
                "missing_concepts": missing,
                "feedback": feedback,
                "recommended_topics": ["Distributed Systems", "Production Monitoring"],
                "next_difficulty": next_diff
            })

        # 4. Standard Role-Aware Question Generation
        else:
            diff = "Hard" if "current difficulty: hard" in prompt_lower or "target difficulty: hard" in prompt_lower or "difficulty: hard" in prompt_lower else (
                "Easy" if "current difficulty: easy" in prompt_lower or "target difficulty: easy" in prompt_lower or "difficulty: easy" in prompt_lower else "Medium"
            )

            # Extract target role
            target_role = "Software Engineer"
            if "target role:" in prompt_lower:
                target_role = prompt_lower.split("target role:")[1].split("\n")[0].strip()
            elif "role of " in prompt_lower:
                target_role = prompt_lower.split("role of ")[1].split("\n")[0].split(".")[0].strip()

            # Extract target topic
            target_topic = ""
            if "target topic:" in prompt_lower:
                target_topic = prompt_lower.split("target topic:")[1].split("\n")[0].strip()

            prev_questions = _extract_previous_questions(prompt_lower)

            # Determine role archetype
            role_lower = target_role.lower()
            if any(k in role_lower for k in ["data scientist", "data science", "analytics", "statistic", "quantitative"]):
                role_key = "data_science"
            elif any(k in role_lower for k in ["machine learning", "ml engineer", "ml/", "ai engineer", "deep learning", "nlp", "computer vision", "llm", "ai "]):
                role_key = "ml_ai"
            elif any(k in role_lower for k in ["data engineer", "big data", "etl", "data platform", "pipeline"]):
                role_key = "data_engineering"
            elif any(k in role_lower for k in ["backend", "distributed", "cloud", "devops", "sre", "platform engineer", "infrastructure", "systems"]):
                role_key = "backend_systems"
            else:
                role_key = "software_engineering"

            role_bank = ROLE_QUESTION_BANK.get(role_key, ROLE_QUESTION_BANK["software_engineering"])

            # 1. Match by target topic in role bank
            selected_entry = None
            if target_topic:
                for topic_entry in role_bank:
                    if target_topic.lower() in topic_entry["topic"].lower() or topic_entry["topic"].lower() in target_topic.lower():
                        q_data = topic_entry.get(diff, topic_entry["Medium"])
                        if not _is_duplicate(q_data["question"], prev_questions):
                            selected_entry = (q_data, topic_entry["topic"])
                            break

            # 2. Scan all topics in role bank for an unasked question at this difficulty
            if not selected_entry:
                for topic_entry in role_bank:
                    q_data = topic_entry.get(diff, topic_entry["Medium"])
                    if not _is_duplicate(q_data["question"], prev_questions):
                        selected_entry = (q_data, topic_entry["topic"])
                        break

            # 3. Check other difficulties in this role bank
            if not selected_entry:
                for topic_entry in role_bank:
                    for alt_diff in ["Medium", "Hard", "Easy"]:
                        q_data = topic_entry.get(alt_diff)
                        if q_data and not _is_duplicate(q_data["question"], prev_questions):
                            selected_entry = (q_data, topic_entry["topic"])
                            break
                    if selected_entry:
                        break

            # 4. Fallback across other role banks if all questions exhausted
            if not selected_entry:
                for other_key, other_bank in ROLE_QUESTION_BANK.items():
                    for topic_entry in other_bank:
                        q_data = topic_entry.get(diff, topic_entry["Medium"])
                        if not _is_duplicate(q_data["question"], prev_questions):
                            selected_entry = (q_data, topic_entry["topic"])
                            break
                    if selected_entry:
                        break

            if selected_entry:
                q_data, final_topic = selected_entry
                q_text = q_data["question"]
                concepts = q_data["concepts"]
            else:
                final_topic = target_topic or "System Architecture"
                q_text = f"Analyze the core engineering trade-offs and architectural decisions involved in {final_topic} for a {target_role} role."
                concepts = ["Architecture", "Production Reliability", "Scalability"]

            return json.dumps({
                "question": q_text,
                "topic": final_topic,
                "difficulty": diff,
                "question_type": "Technical",
                "reason": f"Targeting {final_topic} at {diff} difficulty aligned with {target_role}.",
                "expected_concepts": concepts,
                "source_context": "Knowledge base grounding on core engineering architecture."
            })


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.client = self._init_client()

    def _init_client(self) -> BaseLLMClient:
        if self.provider == "groq" and settings.GROQ_API_KEY:
            logger.info("Using Groq LLM provider.")
            return GroqClient(api_key=settings.GROQ_API_KEY)
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            logger.info("Using OpenAI LLM provider.")
            return OpenAIClient(api_key=settings.OPENAI_API_KEY)
        else:
            logger.info("Using LocalMockLLMClient (API key not configured or offline mode).")
            return LocalMockLLMClient()

    def generate_question(self, **kwargs) -> InterviewQuestion:
        defaults = {
            "candidate_name": "Candidate",
            "candidate_skills": "General Programming",
            "candidate_projects": "None",
            "experience_summary": "Software Engineer",
            "target_role": "Software Engineer",
            "current_difficulty": "Medium",
            "target_topic": "System Design & Architecture",
            "skill_gaps": "General Architecture",
            "job_required_skills": "General Engineering",
            "question_number": 1,
            "total_questions": 5,
            "previous_topics": "None",
            "previous_questions": "None",
            "rag_context": "Knowledge base reference."
        }
        merged = {**defaults, **kwargs}
        prompt = QUESTION_GENERATION_PROMPT.format(**merged)
        raw = self.client.generate_text(prompt, system_prompt="You are an expert technical interviewer.")
        data = parse_and_repair_json(raw)
        return InterviewQuestion(**data)

    def generate_follow_up(self, **kwargs) -> InterviewQuestion:
        defaults = {
            "target_role": "Software Engineer",
            "previous_question": "Technical question",
            "previous_answer": "Candidate answer",
            "technical_accuracy": 50.0,
            "missing_concepts": "Core trade-offs",
            "weaknesses": "Depth",
            "current_topic": "System Architecture",
            "current_difficulty": "Medium",
            "previous_questions": "None",
            "rag_context": "Knowledge base reference."
        }
        merged = {**defaults, **kwargs}
        prompt = FOLLOW_UP_QUESTION_PROMPT.format(**merged)
        raw = self.client.generate_text(prompt, system_prompt="You are an adaptive technical interviewer.")
        data = parse_and_repair_json(raw)
        return InterviewQuestion(**data)

    def evaluate_answer(self, **kwargs) -> AnswerEvaluation:
        prompt = ANSWER_EVALUATION_PROMPT.format(**kwargs)
        raw = self.client.generate_text(prompt, system_prompt="You are an objective AI interview coach.")
        data = parse_and_repair_json(raw)
        return AnswerEvaluation(**data)

    def generate_recommendations(self, **kwargs) -> RecommendationOutput:
        prompt = RECOMMENDATION_PROMPT.format(**kwargs)
        raw = self.client.generate_text(prompt, system_prompt="You are a senior engineering career coach.")
        data = parse_and_repair_json(raw)
        return RecommendationOutput(**data)


llm_service = LLMService()
