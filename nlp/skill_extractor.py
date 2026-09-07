import re
from typing import Dict, List, Set, Tuple

# Comprehensive Technical Skill Taxonomy
TAXONOMY: Dict[str, Dict[str, List[str]]] = {
    "programming_languages": {
        "Python": ["python", "python3", "py"],
        "JavaScript": ["javascript", "js", "ecmascript"],
        "TypeScript": ["typescript", "ts"],
        "Java": ["java", "jdk", "jvm"],
        "C++": ["c++", "cpp"],
        "C#": ["c#", "csharp", ".net"],
        "Go": ["golang", "go language", "go lang", "go"],
        "Rust": ["rust", "rustlang"],
        "SQL": ["sql", "tsql", "plsql", "pl/sql"],
        "R": ["r language", "r programming"],
        "Ruby": ["ruby", "ruby on rails"],
        "PHP": ["php"],
        "Swift": ["swift"],
        "Kotlin": ["kotlin"],
        "Scala": ["scala"],
        "Bash": ["bash", "shell scripting", "sh"]
    },
    "frameworks": {
        "FastAPI": ["fastapi"],
        "Flask": ["flask"],
        "Django": ["django"],
        "React": ["react", "react.js", "reactjs"],
        "Next.js": ["next.js", "nextjs"],
        "Node.js": ["node.js", "nodejs", "node"],
        "Express": ["express", "express.js", "expressjs"],
        "Vue": ["vue", "vue.js", "vuejs"],
        "Angular": ["angular", "angularjs"],
        "Spring Boot": ["spring boot", "spring framework", "spring"],
        "PyTorch": ["pytorch", "torch"],
        "TensorFlow": ["tensorflow", "tf"],
        "Keras": ["keras"],
        "Scikit-Learn": ["scikit-learn", "sklearn"],
        "Pandas": ["pandas"],
        "NumPy": ["numpy"],
        "LangChain": ["langchain"],
        "LangGraph": ["langgraph"],
        "LlamaIndex": ["llamaindex", "llama-index"],
        "Hugging Face": ["huggingface", "hugging face", "transformers"]
    },
    "databases": {
        "PostgreSQL": ["postgresql", "postgres"],
        "MySQL": ["mysql"],
        "SQLite": ["sqlite", "sqlite3"],
        "MongoDB": ["mongodb", "mongo"],
        "Redis": ["redis"],
        "Cassandra": ["cassandra"],
        "DynamoDB": ["dynamodb"],
        "Elasticsearch": ["elasticsearch", "elastic"],
        "FAISS": ["faiss"],
        "Chroma": ["chromadb", "chroma"],
        "Qdrant": ["qdrant"],
        "Pinecone": ["pinecone"],
        "Neo4j": ["neo4j"]
    },
    "cloud_devops": {
        "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
        "GCP": ["gcp", "google cloud", "google cloud platform", "bigquery"],
        "Azure": ["azure", "microsoft azure"],
        "Docker": ["docker", "containerization"],
        "Kubernetes": ["kubernetes", "k8s"],
        "Terraform": ["terraform"],
        "CI/CD": ["ci/cd", "continuous integration", "continuous deployment"],
        "GitHub Actions": ["github actions", "gh actions"],
        "Jenkins": ["jenkins"],
        "Linux": ["linux", "ubuntu", "debian", "centos"],
        "Prometheus": ["prometheus"],
        "Grafana": ["grafana"]
    },
    "ai_ml_domain": {
        "Machine Learning": ["machine learning", "ml", "statistical learning"],
        "Deep Learning": ["deep learning", "dl", "neural networks", "ann", "cnn", "rnn", "lstm"],
        "NLP": ["natural language processing", "nlp", "computational linguistics"],
        "Computer Vision": ["computer vision", "cv", "opencv", "image processing"],
        "Large Language Models": ["large language models", "llm", "llms", "genai", "generative ai"],
        "RAG": ["retrieval-augmented generation", "rag", "retrieval augmented generation"],
        "Vector Embeddings": ["vector embeddings", "embeddings", "semantic search"],
        "Prompt Engineering": ["prompt engineering", "few-shot learning", "prompting"],
        "Fine-tuning": ["fine-tuning", "finetuning", "lora", "qlora", "peft"]
    },
    "tools": {
        "Git": ["git", "github", "gitlab"],
        "Jira": ["jira"],
        "Postman": ["postman"],
        "VS Code": ["vs code", "vscode", "visual studio code"],
        "Jupyter": ["jupyter", "jupyter notebook", "colab"],
        "MediaPipe": ["mediapipe"],
        "Whisper": ["whisper"]
    },
    "system_design": {
        "System Design": ["system design", "software architecture", "high-level design", "hld"],
        "Microservices": ["microservices", "microservice architecture"],
        "REST API": ["rest", "rest api", "restful", "restful apis"],
        "GraphQL": ["graphql"],
        "gRPC": ["grpc"],
        "Kafka": ["kafka", "apache kafka"],
        "RabbitMQ": ["rabbitmq", "message queue", "mq"],
        "Distributed Systems": ["distributed systems", "distributed computing"],
        "Caching": ["caching", "cache", "memcached"]
    }
}


class SkillExtractor:
    def __init__(self):
        self.skill_patterns = {}
        for category, skills in TAXONOMY.items():
            for canonical, aliases in skills.items():
                sub_patterns = []
                for alias in aliases:
                    escaped = re.escape(alias)
                    if alias in ["c++", "c#", ".net", "pl/sql", "ci/cd"]:
                        pattern = r"(?<!\w)" + escaped + r"(?!\w)"
                    elif alias in ["go", "r"]:
                        # Exact case sensitive match for 1-2 char words
                        pattern = r"\b" + alias.capitalize() + r"\b"
                    else:
                        pattern = r"\b" + escaped + r"\b"
                    sub_patterns.append(pattern)
                
                # Use case insensitive by default, but handle case-sensitive aliases
                flags = 0 if any(a in ["go", "r"] for a in aliases) else re.IGNORECASE
                if canonical == "Go":
                    combined = re.compile(r"\b(?:golang|go\s+lang(?:uage)?|Go)\b")
                elif canonical == "R":
                    combined = re.compile(r"\b(?:r\s+lang(?:uage)?|R\b(?=\s+programming|\s+scripting|,|\.))", re.IGNORECASE)
                else:
                    combined = re.compile("|".join(sub_patterns), re.IGNORECASE)
                self.skill_patterns[canonical] = (category, combined)

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        if not text:
            return {
                "all_skills": [],
                "programming_languages": [],
                "frameworks": [],
                "databases": [],
                "cloud_devops": [],
                "tools": [],
                "ai_ml_domain": [],
                "system_design": []
            }

        found_by_category: Dict[str, Set[str]] = {
            "programming_languages": set(),
            "frameworks": set(),
            "databases": set(),
            "cloud_devops": set(),
            "tools": set(),
            "ai_ml_domain": set(),
            "system_design": set()
        }
        all_found: Set[str] = set()

        for canonical, (category, regex) in self.skill_patterns.items():
            if regex.search(text):
                found_by_category[category].add(canonical)
                all_found.add(canonical)

        return {
            "all_skills": sorted(list(all_found)),
            "programming_languages": sorted(list(found_by_category["programming_languages"])),
            "frameworks": sorted(list(found_by_category["frameworks"])),
            "databases": sorted(list(found_by_category["databases"])),
            "cloud_devops": sorted(list(found_by_category["cloud_devops"])),
            "tools": sorted(list(found_by_category["tools"])),
            "ai_ml_domain": sorted(list(found_by_category["ai_ml_domain"])),
            "system_design": sorted(list(found_by_category["system_design"]))
        }


skill_extractor = SkillExtractor()
