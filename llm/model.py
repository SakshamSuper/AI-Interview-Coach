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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content


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


class LocalMockLLMClient(BaseLLMClient):
    """
    Offline development & testing provider that deterministically generates structured responses
    using grounded domain heuristics when API keys are not supplied.
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

        # 2. Answer Evaluation Prompt
        elif "evaluate" in prompt_lower or "technical_accuracy" in prompt_lower:
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

        # 3. Question Generation / Follow-up Prompt
        else:
            topic = "System Design"
            if "python" in prompt_lower:
                topic = "Python & OOP"
                q = "Explain how the Python GIL impacts CPU-bound versus I/O-bound tasks, and how multiprocessing overcomes this limitation."
                concepts = ["GIL", "CPython mutex", "multiprocessing", "asyncio"]
            elif "database" in prompt_lower or "sql" in prompt_lower:
                topic = "SQL & DBMS"
                q = "Compare ACID guarantees with BASE in distributed storage, and describe how B+ Tree indexes accelerate point lookups."
                concepts = ["ACID", "BASE", "B+ Tree", "Leftmost prefix"]
            elif "learning" in prompt_lower or "ml" in prompt_lower or "rag" in prompt_lower:
                topic = "Generative AI & RAG"
                q = "Describe how a RAG pipeline reduces LLM hallucinations and compare recursive character chunking with semantic chunking."
                concepts = ["Vector embeddings", "FAISS", "Chunking strategies", "Grounding context"]
            else:
                q = "How do you design a scalable microservice architecture to handle high-throughput burst traffic using Kafka and Redis?"
                concepts = ["Backpressure", "Kafka partitions", "Redis caching", "Horizontal scaling"]

            return json.dumps({
                "question": q,
                "topic": topic,
                "difficulty": "Medium",
                "question_type": "Technical",
                "reason": "Targeting core domain architecture and candidate technical depth.",
                "expected_concepts": concepts,
                "source_context": "Technical knowledge base grounding."
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
        prompt = QUESTION_GENERATION_PROMPT.format(**kwargs)
        raw = self.client.generate_text(prompt, system_prompt="You are an expert technical interviewer.")
        data = parse_and_repair_json(raw)
        return InterviewQuestion(**data)

    def generate_follow_up(self, **kwargs) -> InterviewQuestion:
        prompt = FOLLOW_UP_QUESTION_PROMPT.format(**kwargs)
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
